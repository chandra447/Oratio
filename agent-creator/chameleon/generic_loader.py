"""
Generic AgentCore Runtime Loader ("Chameleon")
Loads and executes agent code from S3 dynamically based on agent_id and user_id
Includes memory hooks for conversation continuity
"""
import os
import sys
import json
import logging
import boto3
import tempfile
import importlib.util
from typing import Dict, Any
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from strands.hooks import AgentInitializedEvent, HookProvider, HookRegistry, MessageAddedEvent
from opentelemetry import baggage, context as otel_context
#comment to trigger a build
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
CODE_BUCKET = os.environ.get('CODE_BUCKET', 'oratio-generated-code')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AGENTS_TABLE = os.environ.get('AGENTS_TABLE', 'oratio-agents')

# Initialize clients
s3_client = boto3.client('s3', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
memory_client = MemoryClient(region_name=AWS_REGION)

# Create BedrockAgentCoreApp
app = BedrockAgentCoreApp()


class MemoryHookProvider(HookProvider):
    """
    Memory hook provider for Chameleon generic loader.
    Handles conversation history loading and storage for all generated agents.
    
    Based on: https://github.com/awslabs/amazon-bedrock-agentcore-samples/blob/main/01-tutorials/04-AgentCore-memory/01-short-term-memory/01-single-agent/with-strands-agent/personal-agent.ipynb
    """
    
    def __init__(self, memory_client: MemoryClient, memory_id: str):
        self.memory_client = memory_client
        self.memory_id = memory_id
    
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """Load recent conversation history when agent starts"""
        try:
            # Get session info from agent state
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")
            
            if not actor_id or not session_id:
                logger.warning("Missing actor_id or session_id in agent state")
                return
            
            # Load the last 10 conversation turns from memory
            recent_turns = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=actor_id,
                session_id=session_id,
                k=10  # Last 10 turns for conversation context
            )
            
            if recent_turns:
                # Format conversation history for context
                context_messages = []
                for turn in recent_turns:
                    for message in turn:
                        role = message['role']
                        content = message['content']['text']
                        context_messages.append(f"{role}: {content}")
                
                context = "\n".join(context_messages)
                # Add context to agent's system prompt
                event.agent.system_prompt += f"\n\nRecent conversation:\n{context}"
                logger.info(f"✅ Loaded {len(recent_turns)} conversation turns for session {session_id}")
                
        except Exception as e:
            logger.error(f"Memory load error: {e}")
    
    def on_message_added(self, event: MessageAddedEvent):
        """Store messages in memory"""
        messages = event.agent.messages
        try:
            # Get session info from agent state
            actor_id = event.agent.state.get("actor_id")
            session_id = event.agent.state.get("session_id")
            
            if not actor_id or not session_id:
                logger.warning("Missing actor_id or session_id, skipping memory save")
                return

            if messages[-1]["content"][0].get("text"):
                self.memory_client.create_event(
                    memory_id=self.memory_id,
                    actor_id=actor_id,
                    session_id=session_id,
                    messages=[(messages[-1]["content"][0]["text"], messages[-1]["role"])]
                )
                logger.debug(f"✅ Saved message to memory for session {session_id}")
        except Exception as e:
            logger.error(f"Memory save error: {e}")
    
    def register_hooks(self, registry: HookRegistry):
        """Register memory hooks"""
        registry.add_callback(MessageAddedEvent, self.on_message_added)
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entrypoint for generic agent loader
    
    Loads agent code from S3 and executes it dynamically
    
    Args:
        payload: Request payload containing:
            - agent_id: Agent identifier (created by Oratio platform user)
            - user_id: Oratio platform user ID (enterprise who owns the agent)
            - prompt: User message (from end customer)
            - actor_id: REQUIRED - End customer ID (enterprise's customer interacting with agent)
            - session_id: Optional - Conversation ID (defaults to continuous session per actor)
        context: Request context from AgentCore
    
    Returns:
        Dict with agent response or error
        
    Example Payload:
        {
            "agent_id": "support-agent-abc",
            "user_id": "enterprise-acme-corp",     # Oratio platform user (owns agent)
            "actor_id": "acme-customer-john-123",  # End customer (interacts with agent)
            "session_id": "chat-2025-01-15",       # Optional conversation ID
            "prompt": "What's my order status?"
        }
    """
    try:
        logger.info(f"Generic loader invoked with payload: {json.dumps(payload, default=str)}")
        
        # Extract identifiers
        agent_id = payload.get('agent_id')
        user_id = payload.get('user_id')
        
        # Validate required fields
        if not agent_id:
            error_msg = "Missing required field: agent_id"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'error_type': 'ValidationError'
            }
        
        if not user_id:
            error_msg = "Missing required field: user_id"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'error_type': 'ValidationError'
            }
        
        # Fetch agent details from DynamoDB to get memory_id
        agents_table = dynamodb.Table(AGENTS_TABLE)
        try:
            agent_response = agents_table.get_item(
                Key={"userId": user_id, "agentId": agent_id}
            )
            agent_data = agent_response.get('Item', {})
            agent_memory_id = agent_data.get('memoryId')
            
            if agent_memory_id:
                logger.info(f"Agent has dedicated memory resource: {agent_memory_id}")
            else:
                logger.info(f"Agent has no memory resource (conversation history disabled)")
        except Exception as db_error:
            logger.warning(f"Failed to fetch agent from DynamoDB: {db_error}")
            agent_memory_id = None
        
        # Construct S3 path
        s3_key = f"{user_id}/{agent_id}/agent_file.py"
        logger.info(f"Fetching agent code from s3://{CODE_BUCKET}/{s3_key}")
        
        # Fetch agent code from S3
        try:
            response = s3_client.get_object(Bucket=CODE_BUCKET, Key=s3_key)
            agent_code = response['Body'].read().decode('utf-8')
            logger.info(f"Successfully fetched {len(agent_code)} bytes of agent code")
        except s3_client.exceptions.NoSuchKey:
            error_msg = f"Agent code not found at s3://{CODE_BUCKET}/{s3_key}"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'error_type': 'AgentNotFoundError'
            }
        except Exception as e:
            error_msg = f"Failed to fetch agent code from S3: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'error': error_msg,
                'error_type': 'S3Error'
            }
        
        # Write code to temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            prefix=f'agent_{agent_id}_'
        ) as tmp_file:
            tmp_file.write(agent_code)
            tmp_file_path = tmp_file.name
        
        logger.info(f"Agent code written to temporary file: {tmp_file_path}")
        
        try:
            # Import the agent module dynamically
            spec = importlib.util.spec_from_file_location(
                f"dynamic_agent_{agent_id}",
                tmp_file_path
            )
            
            if spec is None or spec.loader is None:
                raise ImportError(f"Failed to load spec from {tmp_file_path}")
            
            agent_module = importlib.util.module_from_spec(spec)
            
            # Add to sys.modules to support relative imports
            sys.modules[spec.name] = agent_module
            
            # Execute the module
            logger.info("Executing agent module")
            spec.loader.exec_module(agent_module)
            
            # Check if module has invoke function
            if not hasattr(agent_module, 'invoke'):
                error_msg = "Agent code does not have 'invoke' function"
                logger.error(error_msg)
                return {
                    'error': error_msg,
                    'error_type': 'CodeStructureError'
                }
            
            # Prepare memory hooks and state for injection
            hooks = []
            state = {}
            
            if memory_client and agent_memory_id:
                # Extract session info from payload
                # actor_id = end customer ID (provided by enterprise/Oratio user's app)
                # session_id = conversation ID (can be generated or provided)
                actor_id = payload.get('actor_id')
                
                if not actor_id:
                    logger.warning("No actor_id provided - memory will use fallback 'anonymous' actor")
                    actor_id = f"anonymous_{user_id}"  # Fallback for missing actor_id
                
                session_id = payload.get('session_id', f"session_{actor_id}_{agent_id}_default")
                
                # Set OpenTelemetry baggage for session correlation
                # This allows CloudWatch to group traces by session
                ctx = baggage.set_baggage("session.id", session_id)
                ctx = baggage.set_baggage("actor.id", actor_id, context=ctx)
                ctx = baggage.set_baggage("agent.id", agent_id, context=ctx)
                ctx = baggage.set_baggage("user.id", user_id, context=ctx)
                context_token = otel_context.attach(ctx)
                logger.info(f"✅ OpenTelemetry baggage set: session_id={session_id}, actor_id={actor_id}, agent_id={agent_id}")
                
                # Create memory hook provider with agent-specific memory_id
                memory_hook = MemoryHookProvider(memory_client, agent_memory_id)
                hooks.append(memory_hook)
                
                # Set state for agent
                state = {
                    "actor_id": actor_id,
                    "session_id": session_id
                }
                
                logger.info(f"Memory hooks enabled for actor_id={actor_id}, session_id={session_id}, memory_id={agent_memory_id}")
            else:
                context_token = None
                logger.info(f"Memory hooks disabled (agent_memory_id={'not configured' if not agent_memory_id else 'unavailable'})")
            
            # Call the agent's invoke function with hooks and state injection
            logger.info("Calling agent invoke function with memory hooks")
            result = agent_module.invoke(payload, context, hooks=hooks, state=state)
            
            logger.info(f"Agent execution completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Error executing agent code: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'error': error_msg,
                'error_type': type(e).__name__
            }
        finally:
            # Detach OpenTelemetry context
            try:
                if 'context_token' in locals() and context_token is not None:
                    otel_context.detach(context_token)
                    logger.debug("Detached OpenTelemetry baggage context")
            except Exception as context_error:
                logger.warning(f"Failed to detach context: {context_error}")
            
            # Cleanup: Remove temporary file
            try:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                    logger.info(f"Cleaned up temporary file: {tmp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp file: {cleanup_error}")
            
            # Cleanup: Remove from sys.modules
            try:
                if spec and spec.name in sys.modules:
                    del sys.modules[spec.name]
            except:
                pass
    
    except Exception as e:
        error_msg = f"Unexpected error in generic loader: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'error': error_msg,
            'error_type': type(e).__name__
        }


if __name__ == "__main__":
    # Run the app
    logger.info("Starting Generic AgentCore Runtime Loader")
    logger.info(f"CODE_BUCKET: {CODE_BUCKET}")
    logger.info(f"AWS_REGION: {AWS_REGION}")
    app.run()

