import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from aws.dynamodb_client import DynamoDBClient
from models.agent import Agent, AgentCreate, AgentResponse, AgentStatus

logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing agents"""

    def __init__(self, dynamodb_client: DynamoDBClient, table_name: str = "oratio-agents"):
        self.dynamodb = dynamodb_client
        self.table_name = table_name

    def create_agent(
        self, user_id: str, kb_id: str, agent_data: AgentCreate
    ) -> Optional[Agent]:
        """
        Create a new agent entry in DynamoDB

        Args:
            user_id: User ID
            kb_id: Knowledge base ID
            agent_data: Agent creation data

        Returns:
            Optional[Agent]: Created agent or None if failed
        """
        try:
            # Generate unique ID
            agent_id = str(uuid4())

            # Create agent object
            agent = Agent(
                agent_id=agent_id,
                user_id=user_id,
                agent_name=agent_data.agent_name,
                agent_type=agent_data.agent_type,
                sop=agent_data.sop,
                knowledge_base_id=kb_id,
                knowledge_base_description=agent_data.knowledge_base_description,
                human_handoff_description=agent_data.human_handoff_description,
                voice_config=agent_data.voice_config,
                text_config=agent_data.text_config,
                status=AgentStatus.CREATING,
                created_at=int(datetime.now().timestamp()),
                updated_at=int(datetime.now().timestamp()),
            )

            # Convert to dict for DynamoDB
            item = agent.model_dump()

            # Put item in DynamoDB
            success = self.dynamodb.put_item(self.table_name, item)

            if success:
                logger.info(f"Created agent: {agent_id}")
                return agent
            else:
                logger.error(f"Failed to create agent in DynamoDB")
                return None

        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            return None

    def get_agent(self, user_id: str, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID with tenant isolation

        Args:
            user_id: User ID for tenant isolation
            agent_id: Agent ID

        Returns:
            Optional[Agent]: Agent or None if not found
        """
        try:
            item = self.dynamodb.get_item(
                self.table_name, key={"userId": user_id, "agentId": agent_id}
            )

            if item:
                return Agent(**item)
            return None

        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {e}")
            return None

    def list_user_agents(self, user_id: str, status_filter: Optional[AgentStatus] = None) -> List[Agent]:
        """
        List all agents for a user

        Args:
            user_id: User ID
            status_filter: Optional status filter

        Returns:
            List[Agent]: List of agents
        """
        try:
            items = self.dynamodb.query_by_partition_key(
                table_name=self.table_name,
                partition_key_name="userId",
                partition_key_value=user_id,
            )

            agents = [Agent(**item) for item in items]

            # Apply status filter if provided
            if status_filter:
                agents = [a for a in agents if a.status == status_filter]

            return agents

        except Exception as e:
            logger.error(f"Error listing agents for user {user_id}: {e}")
            return []

    def update_agent_status(self, user_id: str, agent_id: str, status: AgentStatus) -> bool:
        """
        Update agent status

        Args:
            user_id: User ID
            agent_id: Agent ID
            status: New status

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = {
                "status": status.value,
                "updatedAt": int(datetime.now().timestamp()),
            }

            success = self.dynamodb.update_item(
                table_name=self.table_name,
                key={"userId": user_id, "agentId": agent_id},
                updates=updates,
            )

            if success:
                logger.info(f"Updated agent {agent_id} status to {status}")
            return success

        except Exception as e:
            logger.error(f"Error updating agent {agent_id}: {e}")
            return False

    def update_agent_code_path(self, user_id: str, agent_id: str, code_path: str) -> bool:
        """
        Update agent code S3 path

        Args:
            user_id: User ID
            agent_id: Agent ID
            code_path: S3 path to agent code

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = {
                "agentCodeS3Path": code_path,
                "updatedAt": int(datetime.now().timestamp()),
            }

            success = self.dynamodb.update_item(
                table_name=self.table_name,
                key={"userId": user_id, "agentId": agent_id},
                updates=updates,
            )

            if success:
                logger.info(f"Updated agent {agent_id} code path")
            return success

        except Exception as e:
            logger.error(f"Error updating agent {agent_id} code path: {e}")
            return False

    def update_generated_prompt(self, user_id: str, agent_id: str, prompt: str) -> bool:
        """
        Update generated prompt from AgentCreator

        Args:
            user_id: User ID
            agent_id: Agent ID
            prompt: Generated prompt

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = {
                "generatedPrompt": prompt,
                "updatedAt": int(datetime.now().timestamp()),
            }

            success = self.dynamodb.update_item(
                table_name=self.table_name,
                key={"userId": user_id, "agentId": agent_id},
                updates=updates,
            )

            if success:
                logger.info(f"Updated agent {agent_id} generated prompt")
            return success

        except Exception as e:
            logger.error(f"Error updating agent {agent_id} prompt: {e}")
            return False

    def update_agentcore_details(
        self,
        user_id: str,
        agent_id: str,
        agentcore_agent_id: str,
        agentcore_agent_arn: str,
        websocket_url: Optional[str] = None,
        api_endpoint: Optional[str] = None,
    ) -> bool:
        """
        Update AgentCore deployment details

        Args:
            user_id: User ID
            agent_id: Agent ID
            agentcore_agent_id: AgentCore agent ID
            agentcore_agent_arn: AgentCore agent ARN
            websocket_url: Optional WebSocket URL
            api_endpoint: Optional API endpoint

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = {
                "agentcoreAgentId": agentcore_agent_id,
                "agentcoreAgentArn": agentcore_agent_arn,
                "status": AgentStatus.ACTIVE.value,
                "updatedAt": int(datetime.now().timestamp()),
            }

            if websocket_url:
                updates["websocketUrl"] = websocket_url
            if api_endpoint:
                updates["apiEndpoint"] = api_endpoint

            success = self.dynamodb.update_item(
                table_name=self.table_name,
                key={"userId": user_id, "agentId": agent_id},
                updates=updates,
            )

            if success:
                logger.info(f"Updated agent {agent_id} AgentCore details")
            return success

        except Exception as e:
            logger.error(f"Error updating agent {agent_id} AgentCore details: {e}")
            return False
