import logging
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
#trigger github

class BedrockClient:
    """Bedrock client wrapper with tagging support for Oratio platform"""

    def __init__(self, region_name: str = "us-east-1"):
        self.bedrock_agent = boto3.client("bedrock-agent", region_name=region_name)
        self.bedrock_runtime = boto3.client("bedrock-runtime", region_name=region_name)
        self.bedrock_agent_runtime = boto3.client(
            "bedrock-agent-runtime", region_name=region_name
        )
        self.region_name = region_name

    def create_knowledge_base(
        self,
        name: str,
        description: str,
        role_arn: str,
        user_id: str,
        vector_bucket_arn: str,
        index_arn: str,
        index_name: str,
        embedding_model_arn: str = "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0",
    ) -> Optional[Dict]:
        """
        Create a Bedrock Knowledge Base with S3 Vectors backend and tagging

        Args:
            name: Name of the knowledge base
            description: Description of the knowledge base
            role_arn: IAM role ARN for Bedrock to access resources
            user_id: User ID for tagging
            vector_bucket_arn: ARN of the S3 bucket for vectors
            index_arn: ARN of the S3 vector index
            index_name: Name of the S3 vector index
            embedding_model_arn: ARN of the embedding model

        Returns:
            Optional[Dict]: Knowledge base details or None if failed
        """
        try:
            # Prepare tags
            tags = {
                "userId": user_id,
                "platform": "oratio",
                "environment": "production",
            }

            response = self.bedrock_agent.create_knowledge_base(
                name=name,
                description=description,
                roleArn=role_arn,
                knowledgeBaseConfiguration={
                    "type": "VECTOR",
                    "vectorKnowledgeBaseConfiguration": {
                        "embeddingModelArn": embedding_model_arn
                    },
                },
                storageConfiguration={
                    "type": "S3_VECTORS",
                    "s3VectorsConfiguration": {
                        "vectorBucketArn": vector_bucket_arn,
                        "indexArn": index_arn,
                        "indexName": index_name,
                    },
                },
                tags=tags,
            )

            kb_id = response["knowledgeBase"]["knowledgeBaseId"]
            kb_arn = response["knowledgeBase"]["knowledgeBaseArn"]

            logger.info(f"Successfully created knowledge base with S3 Vectors: {kb_id}")
            return {
                "knowledgeBaseId": kb_id,
                "knowledgeBaseArn": kb_arn,
                "status": response["knowledgeBase"]["status"],
            }

        except ClientError as e:
            logger.error(f"Failed to create knowledge base: {e}")
            return None

    def create_data_source(
        self,
        knowledge_base_id: str,
        name: str,
        s3_bucket_arn: str,
        s3_prefix: str,
    ) -> Optional[Dict]:
        """
        Create a data source for a knowledge base

        Args:
            knowledge_base_id: ID of the knowledge base
            name: Name of the data source
            s3_bucket_arn: ARN of the S3 bucket
            s3_prefix: S3 prefix (folder path)

        Returns:
            Optional[Dict]: Data source details or None if failed
        """
        try:
            response = self.bedrock_agent.create_data_source(
                knowledgeBaseId=knowledge_base_id,
                name=name,
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

            data_source_id = response["dataSource"]["dataSourceId"]
            logger.info(f"Successfully created data source: {data_source_id}")

            return {
                "dataSourceId": data_source_id,
                "status": response["dataSource"]["dataSourceStatus"],
            }

        except ClientError as e:
            logger.error(f"Failed to create data source: {e}")
            return None

    def start_ingestion_job(
        self, knowledge_base_id: str, data_source_id: str
    ) -> Optional[Dict]:
        """
        Start an ingestion job for a data source

        Args:
            knowledge_base_id: ID of the knowledge base
            data_source_id: ID of the data source

        Returns:
            Optional[Dict]: Ingestion job details or None if failed
        """
        try:
            response = self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=knowledge_base_id, dataSourceId=data_source_id
            )

            ingestion_job_id = response["ingestionJob"]["ingestionJobId"]
            logger.info(f"Successfully started ingestion job: {ingestion_job_id}")

            return {
                "ingestionJobId": ingestion_job_id,
                "status": response["ingestionJob"]["status"],
            }

        except ClientError as e:
            logger.error(f"Failed to start ingestion job: {e}")
            return None

    def get_ingestion_job_status(
        self, knowledge_base_id: str, data_source_id: str, ingestion_job_id: str
    ) -> Optional[str]:
        """
        Get the status of an ingestion job

        Args:
            knowledge_base_id: ID of the knowledge base
            data_source_id: ID of the data source
            ingestion_job_id: ID of the ingestion job

        Returns:
            Optional[str]: Status of the ingestion job or None if failed
        """
        try:
            response = self.bedrock_agent.get_ingestion_job(
                knowledgeBaseId=knowledge_base_id,
                dataSourceId=data_source_id,
                ingestionJobId=ingestion_job_id,
            )

            return response["ingestionJob"]["status"]

        except ClientError as e:
            logger.error(f"Failed to get ingestion job status: {e}")
            return None

    def invoke_model(
        self, model_id: str, prompt: str, max_tokens: int = 1024
    ) -> Optional[str]:
        """
        Invoke a Bedrock model

        Args:
            model_id: ID of the model to invoke
            prompt: Prompt to send to the model
            max_tokens: Maximum tokens to generate

        Returns:
            Optional[str]: Model response or None if failed
        """
        try:
            import json

            body = json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                }
            )

            response = self.bedrock_runtime.invoke_model(
                modelId=model_id, body=body, contentType="application/json"
            )

            response_body = json.loads(response["body"].read())
            return response_body["content"][0]["text"]

        except ClientError as e:
            logger.error(f"Failed to invoke model: {e}")
            return None
