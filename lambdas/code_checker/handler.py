import json
import logging
import os

import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client("s3")

# Environment variables
CODE_BUCKET = os.environ.get("CODE_BUCKET", "oratio-generated-code")


def lambda_handler(event, context):
    """
    Code Checker Lambda
    Checks if generated agent code exists in S3
    """
    logger.info(f"Event: {json.dumps(event)}")

    try:
        # Extract parameters from event
        user_id = event.get("userId")
        agent_id = event.get("agentId")
        action = event.get("action", "check_code")

        if not all([user_id, agent_id]):
            raise ValueError("Missing required parameters: userId, agentId")

        # Construct S3 key
        s3_key = f"{user_id}/{agent_id}/agent_file.py"

        logger.info(f"Checking if code exists: s3://{CODE_BUCKET}/{s3_key}")

        # Check if file exists
        try:
            s3_client.head_object(Bucket=CODE_BUCKET, Key=s3_key)
            code_exists = True
            logger.info("Code file exists")
        except s3_client.exceptions.NoSuchKey:
            code_exists = False
            logger.info("Code file does not exist yet")
        except Exception as e:
            logger.error(f"Error checking S3: {e}")
            code_exists = False

        # Return result
        return {
            "userId": user_id,
            "agentId": agent_id,
            "codeReady": code_exists,
            "codeS3Path": f"s3://{CODE_BUCKET}/{s3_key}" if code_exists else None,
            "knowledgeBaseId": event.get("knowledgeBaseId"),
            "bedrockKnowledgeBaseId": event.get("bedrockKnowledgeBaseId"),
            "sop": event.get("sop"),
            "knowledgeBaseDescription": event.get("knowledgeBaseDescription"),
            "humanHandoffDescription": event.get("humanHandoffDescription"),
        }

    except Exception as e:
        logger.error(f"Error checking code: {e}", exc_info=True)
        raise
