import logging
import os
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from aws.dynamodb_client import DynamoDBClient
from aws.s3_client import S3Client
from aws.stepfunctions_client import StepFunctionsClient
from dependencies import get_current_user
from models.agent import AgentCreate, AgentResponse, AgentStatus, AgentType
from models.knowledge_base import KnowledgeBaseCreate
from models.user import User
from services.agent_service import AgentService
from services.knowledge_base_service import KnowledgeBaseService
from services.s3_service import S3Service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])

# Initialize clients and services
dynamodb_client = DynamoDBClient()
s3_client = S3Client()
sfn_client = StepFunctionsClient()

agent_service = AgentService(dynamodb_client)
kb_service = KnowledgeBaseService(dynamodb_client)
s3_service = S3Service(s3_client)

# Get environment variables
from config import settings

STATE_MACHINE_ARN = settings.AGENT_CREATION_STATE_MACHINE_ARN or os.getenv(
    "STATE_MACHINE_ARN", "arn:aws:states:us-east-1:123456789012:stateMachine:oratio-agent-creation"
)


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_name: str = Form(...),
    agent_type: str = Form(...),
    sop: str = Form(...),
    knowledge_base_description: str = Form(...),
    human_handoff_description: str = Form(...),
    voice_personality: Optional[str] = Form(None),  # JSON string
    voice_config: Optional[str] = Form(None),  # JSON string
    text_config: Optional[str] = Form(None),  # JSON string
    files: List[UploadFile] = File(...),
    file_descriptions: Optional[str] = Form(None),  # JSON string mapping filename to description
    current_user: User = Depends(get_current_user),
):
    """
    Create a new agent with knowledge base

    This endpoint:
    1. Uploads files to S3 with proper tagging
    2. Creates knowledge base entry in DynamoDB
    3. Creates agent entry in DynamoDB
    4. Triggers Step Functions workflow for agent creation
    """
    try:
        import json

        from models.agent import VoicePersonality

        # Parse JSON fields
        voice_personality_obj = None
        if voice_personality:
            voice_personality_dict = json.loads(voice_personality)
            voice_personality_obj = VoicePersonality(**voice_personality_dict)

        voice_config_dict = json.loads(voice_config) if voice_config else None
        text_config_dict = json.loads(text_config) if text_config else None
        file_descriptions_dict = json.loads(file_descriptions) if file_descriptions else {}

        # Validate agent type
        try:
            agent_type_enum = AgentType(agent_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent_type. Must be one of: {', '.join([t.value for t in AgentType])}",
            )

        # Generate IDs
        agent_id = str(uuid4())
        kb_id = str(uuid4())
        user_id = current_user.user_id

        logger.info(f"Creating agent {agent_id} for user {user_id}")

        # Step 1: Upload files to S3
        file_upload_data = []
        for file in files:
            content = await file.read()
            import io

            file_obj = io.BytesIO(content)
            file_upload_data.append((file_obj, file.filename, file.content_type))

        upload_results = s3_service.upload_knowledge_base_files(
            files=file_upload_data, user_id=user_id, agent_id=agent_id
        )

        # Check if all uploads succeeded
        failed_uploads = [name for name, success in upload_results.items() if not success]
        if failed_uploads:
            logger.error(f"Failed to upload files: {failed_uploads}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload files: {', '.join(failed_uploads)}",
            )

        # Step 2: Generate folder structure with descriptions
        file_desc_list = [
            (filename, file_descriptions_dict.get(filename, ""))
            for filename in upload_results.keys()
        ]
        folder_structure = s3_service.generate_folder_structure(file_desc_list)

        # Step 3: Create knowledge base entry
        s3_path = s3_service.get_s3_path(user_id, agent_id)
        kb_data = KnowledgeBaseCreate(
            user_id=user_id,
            s3_path=s3_path,
            folder_file_descriptions=folder_structure,
        )

        kb = kb_service.create_knowledge_base(kb_data)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create knowledge base entry",
            )

        # Override the generated ID with our pre-generated one
        kb.knowledge_base_id = kb_id
        # Update in DynamoDB with correct ID
        kb_service.dynamodb.put_item("oratio-knowledgebases", kb.model_dump())

        logger.info(f"Created knowledge base {kb_id}")

        # Step 4: Create agent entry
        agent_create_data = AgentCreate(
            agent_name=agent_name,
            agent_type=agent_type_enum,
            sop=sop,
            knowledge_base_description=knowledge_base_description,
            human_handoff_description=human_handoff_description,
            voice_personality=voice_personality_obj,
            voice_config=voice_config_dict,
            text_config=text_config_dict,
        )

        agent = agent_service.create_agent(
            user_id=user_id, kb_id=kb_id, agent_data=agent_create_data
        )
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create agent entry",
            )

        # Override the generated ID with our pre-generated one
        agent.agent_id = agent_id
        # Update in DynamoDB with correct ID
        agent_service.dynamodb.put_item("oratio-agents", agent.model_dump())

        logger.info(f"Created agent {agent_id}")

        # Step 5: Trigger Step Functions workflow
        execution_name = f"agent-creation-{agent_id}"
        workflow_input = {
            "userId": user_id,
            "agentId": agent_id,
            "knowledgeBaseId": kb_id,
            "sop": sop,
            "knowledgeBaseDescription": knowledge_base_description,
            "humanHandoffDescription": human_handoff_description,
            "s3Path": s3_path,
        }

        execution = sfn_client.start_execution(
            state_machine_arn=STATE_MACHINE_ARN,
            execution_name=execution_name,
            input_data=workflow_input,
        )

        if not execution:
            logger.error("Failed to start Step Functions execution")
            # Don't fail the request, agent is created, workflow will be retried
            # raise HTTPException(
            #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            #     detail="Failed to start agent creation workflow",
            # )

        logger.info(f"Started Step Functions execution: {execution.get('executionArn')}")

        # Return agent response
        response = AgentResponse(
            agent_id=agent.agent_id,
            user_id=agent.user_id,
            agent_name=agent.agent_name,
            agent_type=agent.agent_type,
            sop=agent.sop,
            knowledge_base_id=agent.knowledge_base_id,
            knowledge_base_description=agent.knowledge_base_description,
            human_handoff_description=agent.human_handoff_description,
            voice_personality=agent.voice_personality,
            voice_config=agent.voice_config,
            text_config=agent.text_config,
            bedrock_knowledge_base_arn=agent.bedrock_knowledge_base_arn,
            agentcore_agent_id=agent.agentcore_agent_id,
            agentcore_agent_arn=agent.agentcore_agent_arn,
            generated_prompt=agent.generated_prompt,
            agent_code_s3_path=agent.agent_code_s3_path,
            status=agent.status,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
            websocket_url=agent.websocket_url,
            api_endpoint=agent.api_endpoint,
            knowledge_base=kb.model_dump(),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    List all agents for the current user

    Optional status filter: creating, active, failed, paused
    """
    try:
        user_id = current_user.user_id

        # Parse status filter if provided
        status_enum = None
        if status_filter:
            try:
                status_enum = AgentStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join([s.value for s in AgentStatus])}",
                )

        # Get agents
        agents = agent_service.list_user_agents(user_id, status_filter=status_enum)

        # Get knowledge bases for each agent
        responses = []
        for agent in agents:
            kb = kb_service.get_knowledge_base(agent.knowledge_base_id)

            response = AgentResponse(
                agent_id=agent.agent_id,
                user_id=agent.user_id,
                agent_name=agent.agent_name,
                agent_type=agent.agent_type,
                sop=agent.sop,
                knowledge_base_id=agent.knowledge_base_id,
                knowledge_base_description=agent.knowledge_base_description,
                human_handoff_description=agent.human_handoff_description,
                voice_personality=agent.voice_personality,
                voice_config=agent.voice_config,
                text_config=agent.text_config,
                bedrock_knowledge_base_arn=agent.bedrock_knowledge_base_arn,
                agentcore_agent_id=agent.agentcore_agent_id,
                agentcore_agent_arn=agent.agentcore_agent_arn,
                generated_prompt=agent.generated_prompt,
                agent_code_s3_path=agent.agent_code_s3_path,
                status=agent.status,
                created_at=agent.created_at,
                updated_at=agent.updated_at,
                websocket_url=agent.websocket_url,
                api_endpoint=agent.api_endpoint,
                knowledge_base=kb.model_dump() if kb else None,
            )
            responses.append(response)

        return responses

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific agent by ID
    """
    try:
        user_id = current_user.user_id

        # Get agent with tenant isolation
        agent = agent_service.get_agent(user_id, agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        # Get knowledge base
        kb = kb_service.get_knowledge_base(agent.knowledge_base_id)

        response = AgentResponse(
            agent_id=agent.agent_id,
            user_id=agent.user_id,
            agent_name=agent.agent_name,
            agent_type=agent.agent_type,
            sop=agent.sop,
            knowledge_base_id=agent.knowledge_base_id,
            knowledge_base_description=agent.knowledge_base_description,
            human_handoff_description=agent.human_handoff_description,
            voice_personality=agent.voice_personality,
            voice_config=agent.voice_config,
            text_config=agent.text_config,
            bedrock_knowledge_base_arn=agent.bedrock_knowledge_base_arn,
            agentcore_agent_id=agent.agentcore_agent_id,
            agentcore_agent_arn=agent.agentcore_agent_arn,
            generated_prompt=agent.generated_prompt,
            agent_code_s3_path=agent.agent_code_s3_path,
            status=agent.status,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
            websocket_url=agent.websocket_url,
            api_endpoint=agent.api_endpoint,
            knowledge_base=kb.model_dump() if kb else None,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
