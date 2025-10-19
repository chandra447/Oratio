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
bedrock_agent = boto3.client("bedrock-agent")
s3vectors = boto3.client("s3vectors")
iam = boto3.client("iam")

# Environment variables
AGENTS_TABLE = os.environ.get("AGENTS_TABLE", "oratio-agents")
KB_TABLE = os.environ.get("KB_TABLE", "oratio-knowledgebases")
KB_BUCKET = os.environ.get("KB_BUCKET", "oratio-knowledge-bases")
KB_ROLE_ARN = os.environ.get(
    "KB_ROLE_ARN", "arn:aws:iam::123456789012:role/BedrockKnowledgeBaseRole"
)


def create_kb_service_role(kb_id: str, vector_bucket_name: str, account_id: str) -> str:
    """
    Create an IAM role for Bedrock Knowledge Base to access S3 Vectors
    """
    role_name = f"oratio-kb-role-{kb_id}"
    
    # Trust policy for Bedrock
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "bedrock.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    
    try:
        # Create the role
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"Service role for Bedrock Knowledge Base {kb_id}",
        )
        role_arn = response["Role"]["Arn"]
        logger.info(f"Created IAM role: {role_arn}")
        
        # Create inline policy for S3 Vectors access
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3vectors:GetVectors",
                        "s3vectors:PutVectors",
                        "s3vectors:DeleteVectors",
                        "s3vectors:QueryVectors",
                        "s3vectors:ListVectors",
                        "s3vectors:GetIndex",
                        "s3vectors:ListIndexes",
                    ],
                    "Resource": [
                        f"arn:aws:s3vectors:*:{account_id}:bucket/{vector_bucket_name}",
                        f"arn:aws:s3vectors:*:{account_id}:bucket/{vector_bucket_name}/*",
                    ],
                },
                {
                    "Effect": "Allow",
                    "Action": ["bedrock:InvokeModel"],
                    "Resource": "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0",
                },
            ],
        }
        
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="BedrockKBAccessPolicy",
            PolicyDocument=json.dumps(policy_document),
        )
        logger.info(f"Attached policy to role {role_name}")
        
        # Wait a bit for IAM eventual consistency
        time.sleep(10)
        
        return role_arn
        
    except iam.exceptions.EntityAlreadyExistsException:
        logger.info(f"Role {role_name} already exists, retrieving ARN")
        response = iam.get_role(RoleName=role_name)
        return response["Role"]["Arn"]


def create_vector_bucket_and_index(kb_id: str, user_id: str) -> tuple:
    """
    Create S3 Vector bucket and index for the knowledge base
    Returns: (vector_bucket_name, index_arn, index_name)
    """
    vector_bucket_name = f"oratio-kb-vectors-{kb_id}"
    index_name = f"oratio-kb-index-{kb_id}"
    
    try:
        # Create S3 Vector bucket
        logger.info(f"Creating S3 Vector bucket: {vector_bucket_name}")
        bucket_response = s3vectors.create_vector_bucket(
            vectorBucketName=vector_bucket_name
        )
        logger.info(f"Created S3 Vector bucket: {vector_bucket_name}")
        
        # Create vector index with Titan Embed v2 dimensions (1024) and cosine distance
        logger.info(f"Creating vector index: {index_name}")
        s3vectors.create_index(
            vectorBucketName=vector_bucket_name,
            indexName=index_name,
            dataType="float32",  # Data type for vector embeddings
            dimension=1024,  # Titan Embed Text v2 dimension
            distanceMetric="cosine",
        )
        logger.info(f"Created vector index: {index_name}")
        
        # Get the index ARN by listing indexes (create_index returns empty response)
        logger.info(f"Retrieving index ARN for: {index_name}")
        list_response = s3vectors.list_indexes(
            vectorBucketName=vector_bucket_name
        )
        
        # Find the index we just created
        index_arn = None
        for index in list_response.get("indexes", []):
            if index.get("indexName") == index_name:
                index_arn = index.get("indexArn")
                break
        
        if not index_arn:
            raise Exception(f"Failed to retrieve ARN for index {index_name}")
        
        logger.info(f"Retrieved vector index ARN: {index_arn}")
        
        return vector_bucket_name, index_arn, index_name
        
    except Exception as e:
        logger.error(f"Error creating vector bucket/index: {e}")
        raise


def lambda_handler(event, context):
    """
    KB Provisioner Lambda
    Creates Bedrock Knowledge Base and ingests documents from S3
    """
    logger.info(f"Event: {json.dumps(event)}")

    try:
        # Extract parameters from event
        user_id = event.get("userId")
        agent_id = event.get("agentId")
        kb_id = event.get("knowledgeBaseId")
        s3_path = event.get("s3Path")

        if not all([user_id, agent_id, kb_id, s3_path]):
            raise ValueError("Missing required parameters: userId, agentId, knowledgeBaseId, s3Path")

        logger.info(f"Provisioning KB {kb_id} for agent {agent_id}")
        
        # Get AWS account ID from context
        account_id = context.invoked_function_arn.split(":")[4]

        # Step 1: Get knowledge base details from DynamoDB
        kb_table = dynamodb.Table(KB_TABLE)
        kb_response = kb_table.get_item(Key={"knowledgeBaseId": kb_id})

        if "Item" not in kb_response:
            raise ValueError(f"Knowledge base {kb_id} not found in DynamoDB")

        kb_item = kb_response["Item"]
        logger.info(f"Retrieved KB from DynamoDB: {kb_item}")

        # Step 2: Create S3 Vector bucket and index
        vector_bucket_name, index_arn, index_name = create_vector_bucket_and_index(kb_id, user_id)
        logger.info(f"Created vector bucket: {vector_bucket_name}, index: {index_name}")

        # Step 3: Create IAM role for Bedrock KB to access S3 Vectors
        kb_role_arn = create_kb_service_role(kb_id, vector_bucket_name, account_id)
        logger.info(f"Created KB service role: {kb_role_arn}")

        # Step 4: Create Bedrock Knowledge Base with S3 Vectors
        kb_name = f"oratio-kb-{agent_id}"
        kb_description = f"Knowledge base for agent {agent_id}"

        logger.info(f"Creating Bedrock Knowledge Base: {kb_name}")

        create_kb_response = bedrock_agent.create_knowledge_base(
            name=kb_name,
            description=kb_description,
            roleArn=kb_role_arn,
            knowledgeBaseConfiguration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
                },
            },
            storageConfiguration={
                "type": "S3_VECTORS",
                "s3VectorsConfiguration": {
                    "vectorBucketArn": f"arn:aws:s3vectors:us-east-1:{account_id}:bucket/{vector_bucket_name}",
                    "indexArn": index_arn,
                    "indexName": index_name,
                },
            },
            tags={"userId": user_id, "platform": "oratio", "environment": "production"},
        )

        bedrock_kb_id = create_kb_response["knowledgeBase"]["knowledgeBaseId"]
        bedrock_kb_arn = create_kb_response["knowledgeBase"]["knowledgeBaseArn"]

        logger.info(f"Created Bedrock KB: {bedrock_kb_id}")

        # Step 3: Create S3 data source
        data_source_name = f"oratio-ds-{agent_id}"
        s3_bucket_arn = f"arn:aws:s3:::{KB_BUCKET}"
        s3_prefix = f"{user_id}/{agent_id}/"

        logger.info(f"Creating data source for S3 path: {s3_prefix}")

        create_ds_response = bedrock_agent.create_data_source(
            knowledgeBaseId=bedrock_kb_id,
            name=data_source_name,
            dataSourceConfiguration={
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": s3_bucket_arn,
                    "inclusionPrefixes": [s3_prefix],
                },
            },
            vectorIngestionConfiguration={
                "chunkingConfiguration": {
                    "chunkingStrategy": "FIXED_SIZE",
                    "fixedSizeChunkingConfiguration": {
                        "maxTokens": 500,
                        "overlapPercentage": 20,
                    },
                }
            },
        )

        data_source_id = create_ds_response["dataSource"]["dataSourceId"]
        logger.info(f"Created data source: {data_source_id}")

        # Step 4: Start ingestion job
        logger.info("Starting ingestion job")

        ingestion_response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=bedrock_kb_id, dataSourceId=data_source_id
        )

        ingestion_job_id = ingestion_response["ingestionJob"]["ingestionJobId"]
        logger.info(f"Started ingestion job: {ingestion_job_id}")

        # Step 5: Wait for ingestion to complete (with timeout)
        max_wait_time = 240  # 4 minutes
        poll_interval = 10  # 10 seconds
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            job_status_response = bedrock_agent.get_ingestion_job(
                knowledgeBaseId=bedrock_kb_id,
                dataSourceId=data_source_id,
                ingestionJobId=ingestion_job_id,
            )

            job_status = job_status_response["ingestionJob"]["status"]
            logger.info(f"Ingestion job status: {job_status}")

            if job_status == "COMPLETE":
                logger.info("Ingestion completed successfully")
                break
            elif job_status == "FAILED":
                raise Exception(f"Ingestion job failed: {job_status_response}")

            time.sleep(poll_interval)
            elapsed_time += poll_interval

        if elapsed_time >= max_wait_time:
            logger.warning("Ingestion job timeout, but continuing...")

        # Step 6: Update knowledge base in DynamoDB with vector bucket and index info
        kb_table.update_item(
            Key={"knowledgeBaseId": kb_id},
            UpdateExpression="SET bedrockKnowledgeBaseId = :kb_id, vectorBucketName = :bucket, indexArn = :index_arn, indexName = :index_name, #status = :status, updatedAt = :updated",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":kb_id": bedrock_kb_id,
                ":bucket": vector_bucket_name,
                ":index_arn": index_arn,
                ":index_name": index_name,
                ":status": "ready",
                ":updated": int(time.time()),
            },
        )

        logger.info(f"Updated KB {kb_id} in DynamoDB with vector bucket and index info")

        # Step 7: Update agent with Bedrock KB ARN
        agents_table = dynamodb.Table(AGENTS_TABLE)
        agents_table.update_item(
            Key={"userId": user_id, "agentId": agent_id},
            UpdateExpression="SET bedrockKnowledgeBaseArn = :arn, updatedAt = :updated",
            ExpressionAttributeValues={
                ":arn": bedrock_kb_arn,
                ":updated": int(time.time()),
            },
        )

        logger.info(f"Updated agent {agent_id} with Bedrock KB ARN")

        # Return success with KB details
        return {
            "userId": user_id,
            "agentId": agent_id,
            "knowledgeBaseId": kb_id,
            "bedrockKnowledgeBaseId": bedrock_kb_id,
            "bedrockKnowledgeBaseArn": bedrock_kb_arn,
            "vectorBucketName": vector_bucket_name,
            "indexArn": index_arn,
            "indexName": index_name,
            "status": "ready",
            "sop": event.get("sop"),
            "knowledgeBaseDescription": event.get("knowledgeBaseDescription"),
            "humanHandoffDescription": event.get("humanHandoffDescription"),
        }

    except Exception as e:
        logger.error(f"Error provisioning KB: {e}", exc_info=True)

        # Update KB status to error
        try:
            kb_table = dynamodb.Table(KB_TABLE)
            kb_table.update_item(
                Key={"knowledgeBaseId": event.get("knowledgeBaseId")},
                UpdateExpression="SET #status = :status, updatedAt = :updated",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "error",
                    ":updated": int(time.time()),
                },
            )

            # Update agent status to failed
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
