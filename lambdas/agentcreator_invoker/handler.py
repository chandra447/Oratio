import json
import logging
import os
import time
import uuid

import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")
bedrock_agentcore_client = boto3.client("bedrock-agentcore")
ssm_client = boto3.client("ssm")

# Import MemoryClient for creating agent-specific memory
try:
    from bedrock_agentcore.memory import MemoryClient
    memory_client = MemoryClient()
    MEMORY_ENABLED = True
except ImportError:
    logger.warning("bedrock_agentcore.memory not available - memory features disabled")
    memory_client = None
    MEMORY_ENABLED = False

# Environment variables
AGENTS_TABLE = os.environ.get("AGENTS_TABLE", "oratio-agents")
CODE_BUCKET = os.environ.get("CODE_BUCKET", "oratio-generated-code")
CHAMELEON_RUNTIME_ARN_SSM_PATH = os.environ.get("CHAMELEON_RUNTIME_ARN_SSM_PATH", "/oratio/chameleon/runtime-arn")


def get_agentcreator_runtime_arn():
    """Fetch AgentCreator Runtime ARN from Parameter Store (CDK-friendly, no stack drift)"""
    try:
        response = ssm_client.get_parameter(
            Name='/oratio/agentcreator/runtime-arn',
            WithDecryption=False
        )
        arn = response['Parameter']['Value']
        logger.info(f"Retrieved AgentCreator Runtime ARN from Parameter Store: {arn}")
        return arn
    except Exception as e:
        logger.error(f"Failed to get Runtime ARN from Parameter Store: {e}")
        # Fallback to environment variable (for backward compatibility during migration)
        fallback_arn = os.environ.get("AGENTCREATOR_RUNTIME_ARN", "")
        if fallback_arn:
            logger.warning(f"Using fallback ARN from environment variable: {fallback_arn}")
        return fallback_arn


def get_chameleon_runtime_arn():
    """Fetch Chameleon Runtime ARN from Parameter Store"""
    try:
        response = ssm_client.get_parameter(
            Name=CHAMELEON_RUNTIME_ARN_SSM_PATH,
            WithDecryption=False
        )
        arn = response['Parameter']['Value']
        logger.info(f"Retrieved Chameleon Runtime ARN from Parameter Store: {arn}")
        return arn
    except Exception as e:
        logger.error(f"Failed to get Chameleon Runtime ARN from Parameter Store: {e}")
        raise ValueError(f"Chameleon Runtime ARN not found in Parameter Store at {CHAMELEON_RUNTIME_ARN_SSM_PATH}")


def lambda_handler(event, context):
    """
    AgentCreator Invoker Lambda
    Invokes the AgentCreator meta-agent (deployed on AgentCore) to generate custom agent code
    """
    logger.info(f"Event: {json.dumps(event)}")

    try:
        # Extract parameters from event
        user_id = event.get("userId")
        agent_id = event.get("agentId")
        kb_id = event.get("knowledgeBaseId")
        bedrock_kb_id = event.get("bedrockKnowledgeBaseId")
        sop = event.get("sop")
        kb_description = event.get("knowledgeBaseDescription")
        handoff_description = event.get("humanHandoffDescription")

        if not all([user_id, agent_id, kb_id, sop]):
            raise ValueError("Missing required parameters: userId, agentId, knowledgeBaseId, sop")

        # Get AgentCreator Runtime ARN from Parameter Store (CDK-friendly)
        agentcreator_runtime_arn = get_agentcreator_runtime_arn()
        if not agentcreator_runtime_arn:
            raise ValueError("AgentCreator Runtime ARN not found in Parameter Store or environment variable")

        logger.info(f"Invoking AgentCreator meta-agent for agent {agent_id}")

        # Get agent details from DynamoDB to retrieve voice_personality
        agents_table = dynamodb.Table(AGENTS_TABLE)
        agent_response = agents_table.get_item(Key={"userId": user_id, "agentId": agent_id})

        voice_personality_text = None
        if "Item" in agent_response:
            # Get voicePersonality from DynamoDB
            # If it's already a dict (structured), extract the text description
            # If it's a string, use it as-is
            voice_personality_raw = agent_response["Item"].get("voicePersonality")
            if isinstance(voice_personality_raw, dict):
                # If structured, try to extract a text description field
                voice_personality_text = voice_personality_raw.get("description") or voice_personality_raw.get("text")
                # If no description field, convert the whole dict to a readable string
                if not voice_personality_text:
                    voice_personality_text = json.dumps(voice_personality_raw, indent=2)
            elif isinstance(voice_personality_raw, str):
                voice_personality_text = voice_personality_raw

        # Prepare input for AgentCreator meta-agent
        agent_creator_input = {
            "sop": sop,
            "knowledge_base_description": kb_description,
            "human_handoff_description": handoff_description,
            "bedrock_knowledge_base_id": bedrock_kb_id,
            "agent_id": agent_id,
            "voice_personality_text": voice_personality_text,  # Pass as unstructured text
        }

        # Create session ID (must be 33+ characters for AgentCore)
        session_id = f"agent-creation-{agent_id}-{uuid.uuid4().hex}"
        
        # Prepare payload for AgentCore Runtime
        payload = json.dumps({"input": agent_creator_input})

        logger.info(f"Invoking AgentCreator Runtime: {agentcreator_runtime_arn}")
        logger.info(f"Session ID: {session_id} (length: {len(session_id)})")

        # --------------------------------Invoke the AgentCreator meta-agent via Bedrock AgentCore Runtime--------------------------------
        response = bedrock_agentcore_client.invoke_agent_runtime(
            agentRuntimeArn=agentcreator_runtime_arn,
            runtimeSessionId=session_id,
            payload=payload,
            qualifier="DEFAULT"
        )

        # Process response from AgentCore
        logger.info("Processing AgentCreator response")
        
        # Read the streaming response body
        response_body = response['response'].read()
        response_data = json.loads(response_body)
        
        logger.info(f"Received response from AgentCreator: {len(response_body)} bytes")

        # Extract outputs from AgentCore response
        output = response_data.get("output", {})
        
        # Check for errors in response
        if output.get("error"):
            error_msg = f"AgentCreator returned error: {output.get('error')} (type: {output.get('error_type')})"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        agent_code = output.get("agent_code")
        generated_prompt = output.get("generated_prompt")
        
        # Extract voice_prompt if present (for Nova Sonic voice interface)
        voice_prompt = None
        if isinstance(generated_prompt, dict):
            voice_prompt = generated_prompt.get("voice_prompt")
            # Use full_prompt for the agent code system prompt
            generated_prompt_text = generated_prompt.get("full_prompt", str(generated_prompt))
        else:
            generated_prompt_text = str(generated_prompt) if generated_prompt else ""

        if not agent_code or not generated_prompt_text:
            raise ValueError("AgentCreator did not return valid agent_code or generated_prompt")

        # Decode escaped newlines if present (e.g., "import os\nimport logging" -> actual newlines)
        # This handles cases where the LLM returns escaped strings
        if isinstance(agent_code, str) and "\\n" in agent_code:
            try:
                # Use encode/decode to properly handle escape sequences
                agent_code = agent_code.encode('utf-8').decode('unicode_escape')
                logger.info("Converted escaped newlines to actual newlines in agent code")
            except Exception as e:
                logger.warning(f"Failed to decode escape sequences: {e}, using code as-is")

        logger.info("AgentCreator invocation completed successfully")

        # Upload generated code to S3
        s3_key = f"{user_id}/{agent_id}/agent_file.py"
        logger.info(f"Uploading generated code to s3://{CODE_BUCKET}/{s3_key}")

        s3_client.put_object(
            Bucket=CODE_BUCKET,
            Key=s3_key,
            Body=agent_code.encode("utf-8"),
            ContentType="text/x-python",
            Tagging=f"userId={user_id}&agentId={agent_id}&resourceType=generated-code",
        )

        code_s3_path = f"s3://{CODE_BUCKET}/{s3_key}"
        logger.info(f"Uploaded code to {code_s3_path}")

        # Create or get dedicated memory resource for this agent
        memory_id = None
        if MEMORY_ENABLED and memory_client:
            try:
                logger.info(f"Creating/getting memory resource for agent {agent_id}")
                memory = memory_client.create_or_get_memory(
                    name=f"oratio-agent-{agent_id}",
                    strategies=[],  # No strategies = short-term memory only (raw events)
                    description=f"Conversation memory for agent {agent_id} (user: {user_id})",
                    event_expiry_days=30,  # Keep conversations for 30 days
                )
                memory_id = memory['id']
                logger.info(f"✅ Memory resource ready: {memory_id}")
            except Exception as memory_error:
                # Log error but don't fail the entire deployment
                # Agent can still work without memory (no conversation history)
                logger.error(f"Failed to create/get memory resource: {memory_error}", exc_info=True)
                logger.warning("Agent will be deployed WITHOUT memory (no conversation continuity)")
        else:
            logger.info("Memory creation skipped (not enabled or client not available)")

        # Get Chameleon runtime ARN from Parameter Store
        chameleon_runtime_arn = get_chameleon_runtime_arn()
        
        # Update agent in DynamoDB with code path, prompts, memory ID, and mark as active
        # Note: URLs (websocket/API endpoints) are constructed on-the-fly in FastAPI
        update_expression = "SET agentCodeS3Path = :path, generatedPrompt = :prompt, agentcoreRuntimeArn = :arn, #status = :status, updatedAt = :updated"
        expression_values = {
            ":path": code_s3_path,
            ":prompt": generated_prompt_text,  # Agent system prompt (full_prompt)
            ":arn": chameleon_runtime_arn,
            ":status": "active",
            ":updated": int(time.time()),
        }
        
        # Add voice_prompt if generated (for Nova Sonic)
        if voice_prompt:
            update_expression += ", voicePrompt = :voice_prompt"
            expression_values[":voice_prompt"] = voice_prompt
            logger.info(f"Voice prompt generated: {voice_prompt[:100]}...")
        
        # Add memory_id if created successfully
        if memory_id:
            update_expression += ", memoryId = :memory_id"
            expression_values[":memory_id"] = memory_id
        
        agents_table.update_item(
            Key={"userId": user_id, "agentId": agent_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues=expression_values,
        )

        logger.info(f"Agent {agent_id} marked as active with Chameleon runtime" + (f" and memory {memory_id}" if memory_id else " (no memory)"))

        # Return success with code details
        return {
            "userId": user_id,
            "agentId": agent_id,
            "knowledgeBaseId": kb_id,
            "bedrockKnowledgeBaseId": bedrock_kb_id,
            "codeS3Path": code_s3_path,
            "generatedPrompt": generated_prompt,
            "memoryId": memory_id,
            "sop": sop,
            "knowledgeBaseDescription": kb_description,
            "humanHandoffDescription": handoff_description,
        }

    except Exception as e:
        logger.error(f"Error invoking AgentCreator: {e}", exc_info=True)

        # Update agent status to failed
        try:
            agents_table = dynamodb.Table(AGENTS_TABLE)
            agents_table.update_item(
                Key={"userId": event.get("userId"), "agentId": event.get("agentId")},
                UpdateExpression="SET #status = :status, updatedAt = :updated",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "failed",
                    ":updated": int(time.time()),
                },
            )
        except Exception as update_error:
            logger.error(f"Error updating status: {update_error}")

        raise
