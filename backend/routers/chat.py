"""Chat endpoints for conversational agents"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from config import settings
from dependencies import get_agent_service, get_api_key_service, get_agent_invocation_service
from models.api_key import APIKeyPermission
from services.agent_invocation_service import AgentInvocationService
from services.agent_service import AgentService
from services.api_key_service import APIKeyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model"""

    message: str = Field(..., description="User's message", min_length=1)
    metadata: dict = Field(default={}, description="Optional metadata")


class ChatResponse(BaseModel):
    """Chat response model"""

    result: str = Field(..., description="Agent's response")
    stop_reason: str = Field(default="end_turn", description="Why the agent stopped")
    metrics: dict = Field(default={}, description="Response metrics")
    metadata: dict = Field(default={}, description="Additional metadata")


@router.post(
    "/{agent_id}/{actor_id}/{session_id}",
    response_model=ChatResponse,
    summary="Chat with an agent",
    description="Send a message to a deployed agent and get a response",
)
async def chat_with_agent(
    agent_id: str,
    actor_id: str,
    session_id: str,
    request: ChatRequest,
    x_api_key: Annotated[str, Header(description="API key for authentication")],
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
    api_key_service: Annotated[APIKeyService, Depends(get_api_key_service)],
    invocation_service: Annotated[AgentInvocationService, Depends(get_agent_invocation_service)],
) -> ChatResponse:
    """
    Chat with a deployed agent

    **Path Parameters:**
    - `agent_id`: The agent's unique identifier
    - `actor_id`: The user/actor identifier (for conversation isolation)
    - `session_id`: The conversation session identifier

    **Headers:**
    - `X-API-Key`: API key for authentication

    **Request Body:**
    - `message`: The user's message to send to the agent
    - `metadata`: Optional metadata (not used currently)

    **Response:**
    - `result`: The agent's response message
    - `stop_reason`: Why the agent stopped (usually "end_turn")
    - `metrics`: Response metrics (tokens, conversation turns, etc.)
    - `metadata`: Additional metadata from the agent

    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/chat/agent-123/user-456/session-789" \\
      -H "X-API-Key: oratio_your_api_key_here" \\
      -H "Content-Type: application/json" \\
      -d '{"message": "Can I return this item?"}'
    ```
    """

    # Step 1: Validate API key
    logger.info(f"Validating API key for agent {agent_id}")
    validation = api_key_service.validate_key_for_agent(
        api_key=x_api_key, agent_id=agent_id
    )

    if not validation.valid:
        logger.warning(f"Invalid API key for agent {agent_id}: {validation.reason}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=validation.reason or "Invalid API key",
        )

    # Check chat permission
    if APIKeyPermission.CHAT not in validation.permissions:
        logger.warning(f"API key does not have chat permission for agent {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key does not have chat permission",
        )

    # Step 2: Get agent details
    logger.info(f"Retrieving agent {agent_id} for user {validation.user_id}")
    agent = agent_service.get_agent(
        user_id=validation.user_id, agent_id=agent_id
    )

    if not agent:
        logger.error(f"Agent {agent_id} not found for user {validation.user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    # Check if agent is active
    if agent.status != "active":
        logger.warning(f"Agent {agent_id} is not active (status: {agent.status})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent is not active (status: {agent.status})",
        )

    # Check if agent has AgentCore Runtime ARN
    if not agent.agentcore_runtime_arn:
        logger.error(f"Agent {agent_id} does not have AgentCore Runtime ARN")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent is not properly deployed",
        )

    # Step 3: Invoke the Chameleon AgentCore Runtime
    logger.info(
        f"Invoking Chameleon runtime for agent {agent_id} "
        f"(session: {session_id}, actor: {actor_id})"
    )

    # Note: memory_id is NOT passed to Chameleon
    # Chameleon fetches it from DynamoDB based on agent_id
    # Each agent has a unique memory_id created during agent creation

    result = invocation_service.invoke_agent(
        runtime_arn=agent.agentcore_runtime_arn,
        agent_id=agent_id,
        user_id=validation.user_id,
        session_id=session_id,
        prompt=request.message,
        actor_id=actor_id,
    )

    # Step 4: Handle response
    if not result.get("success"):
        logger.error(f"Agent invocation failed: {result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Agent invocation failed"),
        )

    logger.info(f"Agent invocation successful for session {session_id}")

    return ChatResponse(
        result=result["result"],
        stop_reason=result.get("stop_reason", "end_turn"),
        metrics=result.get("metrics", {}),
        metadata=result.get("metadata", {}),
    )


@router.get(
    "/health",
    summary="Health check",
    description="Check if the chat service is healthy",
)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "chat"}
