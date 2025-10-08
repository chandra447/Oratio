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
bedrock_agent = boto3.client("bedrock-agent")

# Environment variables
AGENTS_TABLE = os.environ.get("AGENTS_TABLE", "oratio-agents")
CODE_BUCKET = os.environ.get("CODE_BUCKET", "oratio-generated-code")
AGENTCORE_ROLE_ARN = os.environ.get(
    "AGENTCORE_ROLE_ARN", "arn:aws:iam::123456789012:role/AgentCoreExecutionRole"
)


def lambda_handler(event, context):
    """
    AgentCore Deployer Lambda
    Deploys generated agent code to AWS AgentCore
    """
    logger.info(f"Event: {json.dumps(event)}")

    try:
        # Extract parameters from event
        user_id = event.get("userId")
        agent_id = event.get("agentId")
        code_s3_path = event.get("codeS3Path")
        bedrock_kb_id = event.get("bedrockKnowledgeBaseId")

        if not all([user_id, agent_id]):
            raise ValueError("Missing required parameters: userId, agentId")

        logger.info(f"Deploying agent {agent_id} to AgentCore")

        # Step 1: Retrieve generated code from S3
        s3_key = f"{user_id}/{agent_id}/agent_file.py"

        logger.info(f"Retrieving code from s3://{CODE_BUCKET}/{s3_key}")

        code_response = s3_client.get_object(Bucket=CODE_BUCKET, Key=s3_key)
        agent_code = code_response["Body"].read().decode("utf-8")

        logger.info(f"Retrieved agent code ({len(agent_code)} bytes)")

        # Step 2: Get agent details from DynamoDB
        agents_table = dynamodb.Table(AGENTS_TABLE)
        agent_response = agents_table.get_item(Key={"userId": user_id, "agentId": agent_id})

        if "Item" not in agent_response:
            raise ValueError(f"Agent {agent_id} not found in DynamoDB")

        agent_item = agent_response["Item"]
        agent_name = agent_item.get("agentName", f"oratio-agent-{agent_id}")
        agent_type = agent_item.get("agentType", "text")
        generated_prompt = agent_item.get("generatedPrompt", "")

        # Step 3: Create AgentCore agent
        logger.info(f"Creating AgentCore agent: {agent_name}")

        # Prepare instruction (system prompt)
        instruction = generated_prompt or "You are a helpful AI assistant."

        create_agent_response = bedrock_agent.create_agent(
            agentName=agent_name,
            agentResourceRoleArn=AGENTCORE_ROLE_ARN,
            description=f"Oratio agent {agent_id}",
            foundationModel="anthropic.claude-3-sonnet-20240229-v1:0",
            instruction=instruction,
            tags={"userId": user_id, "agentId": agent_id, "platform": "oratio", "environment": "production"},
        )

        agentcore_agent_id = create_agent_response["agent"]["agentId"]
        agentcore_agent_arn = create_agent_response["agent"]["agentArn"]

        logger.info(f"Created AgentCore agent: {agentcore_agent_id}")

        # Step 4: Associate knowledge base with agent (if available)
        if bedrock_kb_id:
            logger.info(f"Associating knowledge base {bedrock_kb_id} with agent")

            try:
                bedrock_agent.associate_agent_knowledge_base(
                    agentId=agentcore_agent_id,
                    agentVersion="DRAFT",
                    knowledgeBaseId=bedrock_kb_id,
                    description="Agent knowledge base",
                    knowledgeBaseState="ENABLED",
                )
                logger.info("Knowledge base associated successfully")
            except Exception as kb_error:
                logger.warning(f"Failed to associate KB: {kb_error}")

        # Step 5: Prepare agent (creates a version)
        logger.info("Preparing agent")

        prepare_response = bedrock_agent.prepare_agent(agentId=agentcore_agent_id)
        agent_status = prepare_response["agentStatus"]

        logger.info(f"Agent preparation status: {agent_status}")

        # Wait for agent to be prepared
        max_wait = 60  # 1 minute
        elapsed = 0
        poll_interval = 5

        while elapsed < max_wait:
            get_agent_response = bedrock_agent.get_agent(agentId=agentcore_agent_id)
            agent_status = get_agent_response["agent"]["agentStatus"]

            if agent_status in ["PREPARED", "FAILED", "NOT_PREPARED"]:
                break

            time.sleep(poll_interval)
            elapsed += poll_interval

        if agent_status != "PREPARED":
            logger.warning(f"Agent preparation did not complete: {agent_status}")

        # Step 6: Create agent alias
        logger.info("Creating agent alias")

        alias_response = bedrock_agent.create_agent_alias(
            agentId=agentcore_agent_id, agentAliasName="production", description="Production alias"
        )

        agent_alias_id = alias_response["agentAlias"]["agentAliasId"]
        agent_alias_arn = alias_response["agentAlias"]["agentAliasArn"]

        logger.info(f"Created agent alias: {agent_alias_id}")

        # Step 7: Generate endpoints
        # For voice agents, we'll create WebSocket URL
        # For text agents, we'll create REST API endpoint
        websocket_url = None
        api_endpoint = None

        if agent_type in ["voice", "both"]:
            websocket_url = f"wss://voice.oratio.io/agents/{agent_id}"

        if agent_type in ["text", "both"]:
            api_endpoint = f"https://api.oratio.io/agents/{agent_id}/chat"

        # Step 8: Update agent in DynamoDB
        logger.info("Updating agent in DynamoDB")

        update_expression = "SET agentcoreAgentId = :agent_id, agentcoreAgentArn = :agent_arn, #status = :status, updatedAt = :updated"
        expression_values = {
            ":agent_id": agentcore_agent_id,
            ":agent_arn": agentcore_agent_arn,
            ":status": "active",
            ":updated": int(time.time()),
        }
        expression_names = {"#status": "status"}

        if websocket_url:
            update_expression += ", websocketUrl = :ws_url"
            expression_values[":ws_url"] = websocket_url

        if api_endpoint:
            update_expression += ", apiEndpoint = :api_endpoint"
            expression_values[":api_endpoint"] = api_endpoint

        agents_table.update_item(
            Key={"userId": user_id, "agentId": agent_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
        )

        logger.info(f"Agent {agent_id} deployed successfully and marked as active")

        # Return success
        return {
            "userId": user_id,
            "agentId": agent_id,
            "agentcoreAgentId": agentcore_agent_id,
            "agentcoreAgentArn": agentcore_agent_arn,
            "agentAliasId": agent_alias_id,
            "agentAliasArn": agent_alias_arn,
            "status": "active",
            "websocketUrl": websocket_url,
            "apiEndpoint": api_endpoint,
        }

    except Exception as e:
        logger.error(f"Error deploying agent: {e}", exc_info=True)

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

