"""Agent invocation service for calling deployed AgentCore agents"""

import json
import logging
import uuid
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class AgentInvocationService:
    """Service for invoking deployed AgentCore Runtime agents (Chameleon)"""

    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.bedrock_agentcore = boto3.client(
            "bedrock-agentcore", region_name=region
        )

    def invoke_agent(
        self,
        runtime_arn: str,
        agent_id: str,
        user_id: str,
        session_id: str,
        prompt: str,
        actor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Invoke Chameleon AgentCore Runtime with agent identifiers

        Args:
            runtime_arn: AgentCore Runtime ARN (Chameleon loader)
            agent_id: Agent identifier (Chameleon uses this to fetch code from S3 and memory_id from DynamoDB)
            user_id: Oratio platform user ID (enterprise who owns the agent)
            session_id: Session ID for conversation continuity
            prompt: User's message (from end customer)
            actor_id: End customer ID (enterprise's customer interacting with agent)

        Returns:
            Dict with response data

        Note:
            memory_id is NOT passed here. Chameleon fetches it from DynamoDB using agent_id.

        Raises:
            Exception: If invocation fails
        """
        try:
            # Ensure session ID is 33+ characters (AgentCore requirement)
            if len(session_id) < 33:
                session_id = f"{session_id}-{uuid.uuid4().hex}"[:50]

            # Prepare payload for Chameleon
            # Chameleon will:
            # 1. Use agent_id + user_id to fetch code from S3
            # 2. Use agent_id + user_id to fetch memory_id from DynamoDB
            # 3. Use actor_id + session_id for memory hooks
            payload = json.dumps({
                "agent_id": agent_id,
                "user_id": user_id,
                "prompt": prompt,
                "actor_id": actor_id,
                "session_id": session_id,
            })

            logger.info(
                f"Invoking Chameleon runtime for agent {agent_id} "
                f"(user: {user_id}, session: {session_id})"
            )

            # Invoke the AgentCore Runtime
            response = self.bedrock_agentcore.invoke_agent_runtime(
                agentRuntimeArn=runtime_arn,
                runtimeSessionId=session_id,
                payload=payload,
                qualifier="DEFAULT"
            )

            # Read the streaming response
            response_body = response['response'].read()
            response_data = json.loads(response_body)

            logger.info(f"Chameleon invocation successful: {len(response_body)} bytes")

            # Check for errors in response
            if "error" in response_data:
                logger.error(f"Chameleon returned error: {response_data.get('error')}")
                return {
                    "success": False,
                    "error": response_data.get("error"),
                    "error_type": response_data.get("error_type", "AgentError")
                }

            # Extract output from successful response
            output = response_data.get("output", {})

            # Try to parse structured output
            if isinstance(output, dict):
                return {
                    "success": True,
                    "result": output.get("message", {}).get("content", [{}])[0].get("text", str(output)),
                    "stop_reason": "end_turn",
                    "metrics": output.get("metrics", {}),
                    "metadata": output
                }
            else:
                # Plain response
                return {
                    "success": True,
                    "result": str(output),
                    "stop_reason": "end_turn",
                    "metrics": {},
                    "metadata": response_data
                }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"AWS error invoking AgentCore: {error_code} - {error_message}")

            return {
                "success": False,
                "error": f"AgentCore invocation failed: {error_message}",
                "error_code": error_code,
            }

        except Exception as e:
            logger.error(f"Error invoking AgentCore: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
            }

    def invoke_agent_streaming(
        self,
        agent_id: str,
        agent_alias_id: str,
        session_id: str,
        prompt: str,
        memory_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ):
        """
        Invoke agent with streaming response (generator)

        Args:
            agent_id: AgentCore agent ID
            agent_alias_id: Agent alias ID
            session_id: Session ID
            prompt: User's message
            memory_id: Optional memory ID
            actor_id: Optional actor ID

        Yields:
            str: Response chunks
        """
        try:
            # Prepare payload
            payload = {
                "prompt": prompt,
            }

            if memory_id:
                payload["memory_id"] = memory_id
            if actor_id:
                payload["actor_id"] = actor_id
            if session_id:
                payload["session_id"] = session_id

            logger.info(f"Invoking agent {agent_id} with streaming")

            # Invoke the agent
            response = self.bedrock_agent_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=json.dumps(payload),
                enableTrace=False,
                endSession=False,
            )

            # Stream chunks
            for event in response.get("completion", []):
                if "chunk" in event:
                    chunk = event["chunk"]
                    if "bytes" in chunk:
                        text = chunk["bytes"].decode("utf-8")
                        yield text

        except Exception as e:
            logger.error(f"Error in streaming invocation: {e}")
            yield json.dumps({"error": str(e)})
