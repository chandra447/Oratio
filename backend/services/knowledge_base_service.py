import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from aws.dynamodb_client import DynamoDBClient
from models.knowledge_base import KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseStatus

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service for managing knowledge bases"""

    def __init__(self, dynamodb_client: DynamoDBClient, table_name: str = "oratio-knowledgebases"):
        self.dynamodb = dynamodb_client
        self.table_name = table_name

    def create_knowledge_base(self, kb_data: KnowledgeBaseCreate, kb_id: Optional[str] = None) -> Optional[KnowledgeBase]:
        """
        Create a new knowledge base entry in DynamoDB

        Args:
            kb_data: Knowledge base creation data
            kb_id: Optional pre-generated knowledge base ID (if None, generates new UUID)

        Returns:
            Optional[KnowledgeBase]: Created knowledge base or None if failed
        """
        try:
            # Use provided ID or generate unique ID
            if kb_id is None:
                kb_id = str(uuid4())

            # Create knowledge base object
            kb = KnowledgeBase(
                knowledge_base_id=kb_id,
                user_id=kb_data.user_id,
                s3_path=kb_data.s3_path,
                folder_file_descriptions=kb_data.folder_file_descriptions,
                status=KnowledgeBaseStatus.NOTREADY,
                created_at=int(datetime.now().timestamp()),
                updated_at=int(datetime.now().timestamp()),
            )

            # Convert to dict for DynamoDB (use aliases for camelCase keys)
            item = kb.model_dump(by_alias=True)

            # Put item in DynamoDB
            success = self.dynamodb.put_item(self.table_name, item)

            if success:
                logger.info(f"Created knowledge base: {kb_id}")
                return kb
            else:
                logger.error(f"Failed to create knowledge base in DynamoDB")
                return None

        except Exception as e:
            logger.error(f"Error creating knowledge base: {e}")
            return None

    def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        """
        Get a knowledge base by ID

        Args:
            kb_id: Knowledge base ID

        Returns:
            Optional[KnowledgeBase]: Knowledge base or None if not found
        """
        try:
            item = self.dynamodb.get_item(
                self.table_name, key={"knowledgeBaseId": kb_id}
            )

            if item:
                return KnowledgeBase(**item)
            return None

        except Exception as e:
            logger.error(f"Error getting knowledge base {kb_id}: {e}")
            return None

    def list_user_knowledge_bases(self, user_id: str) -> List[KnowledgeBase]:
        """
        List all knowledge bases for a user

        Args:
            user_id: User ID

        Returns:
            List[KnowledgeBase]: List of knowledge bases
        """
        try:
            items = self.dynamodb.query_by_gsi(
                table_name=self.table_name,
                index_name="userId-index",
                partition_key_name="userId",
                partition_key_value=user_id,
            )

            return [KnowledgeBase(**item) for item in items]

        except Exception as e:
            logger.error(f"Error listing knowledge bases for user {user_id}: {e}")
            return []

    def update_status(
        self, kb_id: str, status: KnowledgeBaseStatus, bedrock_kb_id: Optional[str] = None
    ) -> bool:
        """
        Update knowledge base status

        Args:
            kb_id: Knowledge base ID
            status: New status
            bedrock_kb_id: Optional Bedrock KB ID to update

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = {
                "status": status.value,
                "updatedAt": int(datetime.now().timestamp()),
            }

            if bedrock_kb_id:
                updates["bedrockKnowledgeBaseId"] = bedrock_kb_id

            success = self.dynamodb.update_item(
                table_name=self.table_name,
                key={"knowledgeBaseId": kb_id},
                updates=updates,
            )

            if success:
                logger.info(f"Updated knowledge base {kb_id} status to {status}")
            return success

        except Exception as e:
            logger.error(f"Error updating knowledge base {kb_id}: {e}")
            return False

    def update_bedrock_kb_id(self, kb_id: str, bedrock_kb_id: str) -> bool:
        """
        Update Bedrock Knowledge Base ID

        Args:
            kb_id: Knowledge base ID
            bedrock_kb_id: Bedrock KB ID

        Returns:
            bool: True if successful, False otherwise
        """
        return self.update_status(kb_id, KnowledgeBaseStatus.READY, bedrock_kb_id)
