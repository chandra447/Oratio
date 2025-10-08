import json
import logging
import os
import time

import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime")

# Environment variables
AGENTS_TABLE = os.environ.get("AGENTS_TABLE", "oratio-agents")
CODE_BUCKET = os.environ.get("CODE_BUCKET", "oratio-generated-code")
AGENTCREATOR_AGENT_ID = os.environ.get("AGENTCREATOR_AGENT_ID")
AGENTCREATOR_AGENT_ALIAS_ID = os.environ.get("AGENTCREATOR_AGENT_ALIAS_ID", "TSTALIASID")


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

        if not AGENTCREATOR_AGENT_ID:
            raise ValueError("AGENTCREATOR_AGENT_ID environment variable not configured")

        logger.info(f"Invoking AgentCreator meta-agent for agent {agent_id}")

        # Get agent details from DynamoDB to retrieve voice_personality
        agents_table = dynamodb.Table(AGENTS_TABLE)
        agent_response = agents_table.get_item(Key={"userId": user_id, "agentId": agent_id})

        voice_personality = None
        if "Item" in agent_response:
            voice_personality = agent_response["Item"].get("voicePersonality")

        # Prepare input for AgentCreator meta-agent
        agent_creator_input = {
            "sop": sop,
            "knowledge_base_description": kb_description,
            "human_handoff_description": handoff_description,
            "bedrock_knowledge_base_id": bedrock_kb_id,
            "agent_id": agent_id,
            "voice_personality": voice_personality,
        }

        input_text = json.dumps(agent_creator_input)
        session_id = f"agent-creation-{agent_id}-{int(time.time())}"

        logger.info(f"Invoking AgentCreator: {AGENTCREATOR_AGENT_ID}")

        # Invoke the AgentCreator meta-agent via Bedrock Agent Runtime
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENTCREATOR_AGENT_ID,
            agentAliasId=AGENTCREATOR_AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=input_text,
        )

        # Process streaming response
        agent_response_text = ""
        logger.info("Processing AgentCreator response stream")

        for event_chunk in response.get("completion", []):
            chunk = event_chunk.get("chunk")
            if chunk:
                chunk_bytes = chunk.get("bytes")
                if chunk_bytes:
                    chunk_text = chunk_bytes.decode("utf-8")
                    agent_response_text += chunk_text

        logger.info(f"Received response from AgentCreator ({len(agent_response_text)} bytes)")

        # Parse the response (AgentCreator returns JSON with agent_code and generated_prompt)
        result = json.loads(agent_response_text)
        agent_code = result.get("agent_code")
        generated_prompt = result.get("generated_prompt")

        if not agent_code or not generated_prompt:
            raise ValueError("AgentCreator did not return valid agent_code or generated_prompt")

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

        # Update agent in DynamoDB with code path and generated prompt
        agents_table.update_item(
            Key={"userId": user_id, "agentId": agent_id},
            UpdateExpression="SET agentCodeS3Path = :path, generatedPrompt = :prompt, updatedAt = :updated",
            ExpressionAttributeValues={
                ":path": code_s3_path,
                ":prompt": generated_prompt,
                ":updated": int(time.time()),
            },
        )

        logger.info(f"Updated agent {agent_id} with code path and prompt")

        # Return success with code details
        return {
            "userId": user_id,
            "agentId": agent_id,
            "knowledgeBaseId": kb_id,
            "bedrockKnowledgeBaseId": bedrock_kb_id,
            "codeS3Path": code_s3_path,
            "generatedPrompt": generated_prompt,
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
