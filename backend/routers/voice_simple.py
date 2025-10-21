"""Simplified Voice agent WebSocket endpoint with Nova Sonic + Chameleon integration
Based on AWS sample: https://github.com/aws-samples/sample-nova-sonic-agentic-chatbot
"""

import asyncio
import base64
import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
import boto3

# Smithy SDK for bidirectional streaming
from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
from aws_sdk_bedrock_runtime.config import Config

from config import settings
from services.agent_service import AgentService
from services.api_key_service import APIKeyService
from aws.dynamodb_client import DynamoDBClient
from models.api_key import APIKeyPermission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

# Audio configuration (matching AWS sample for web)
INPUT_SAMPLE_RATE = 16000  # Input from frontend
OUTPUT_SAMPLE_RATE = 24000  # Output from Nova Sonic
CHUNK_SIZE = 1024  # Audio chunk size for streaming output


class ToolProcessor:
    """Process tool calls by invoking Chameleon agent"""
    
    def __init__(self, agent_id: str, user_id: str, session_id: str):
        self.agent_id = agent_id
        self.user_id = user_id
        self.session_id = session_id
        self.bedrock_agentcore = None
        self.chameleon_runtime_arn = None
        self.tasks = {}
    
    def _get_bedrock_client(self):
        """Get or create bedrock-agentcore client"""
        if not self.bedrock_agentcore:
            import boto3
            self.bedrock_agentcore = boto3.client('bedrock-agentcore', region_name=settings.AWS_REGION)
        return self.bedrock_agentcore
    
    def _get_chameleon_arn(self):
        """Get Chameleon runtime ARN from SSM"""
        if not self.chameleon_runtime_arn:
            import boto3
            ssm = boto3.client('ssm', region_name=settings.AWS_REGION)
            try:
                response = ssm.get_parameter(Name='/oratio/chameleon/runtime-arn')
                self.chameleon_runtime_arn = response['Parameter']['Value']
                logger.info(f"[ToolProcessor] Retrieved Chameleon ARN: {self.chameleon_runtime_arn}")
            except Exception as e:
                logger.error(f"[ToolProcessor] Failed to get Chameleon ARN: {e}")
                raise
        return self.chameleon_runtime_arn
    
    async def process_tool_async(self, tool_name: str, tool_content: dict):
        """Process a tool call by invoking Chameleon agent"""
        task_id = str(uuid.uuid4())
        
        task = asyncio.create_task(self._invoke_chameleon(tool_name, tool_content))
        self.tasks[task_id] = task
        
        try:
            result = await task
            return result
        finally:
            if task_id in self.tasks:
                del self.tasks[task_id]
    
    async def _invoke_chameleon(self, tool_name: str, tool_content: dict):
        """Invoke Chameleon agent to execute the tool"""
        logger.info(f"[ToolProcessor] 🚀 Invoking Chameleon for tool: {tool_name}")
        
        try:
            # Get Bedrock AgentCore client
            logger.info(f"[ToolProcessor] Getting Bedrock client...")
            client = self._get_bedrock_client()
            runtime_arn = self._get_chameleon_arn()
            logger.info(f"[ToolProcessor] Using Chameleon ARN: {runtime_arn}")
            
            # Extract tool input from content
            content = tool_content.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)
            
            # Extract the query from the tool input
            if tool_name.lower() == "ask_agent":
                query = content.get("query", "")
            else:
                # Fallback for other tools
                query = f"Use the {tool_name} tool with input: {json.dumps(content)}"
            
            logger.info(f"[ToolProcessor] Extracted query: {query[:150]}...")
            
            # Ensure session ID is 33+ characters (AgentCore requirement)
            runtime_session_id = self.session_id
            if len(runtime_session_id) < 33:
                runtime_session_id = f"{runtime_session_id}-{uuid.uuid4().hex}"[:50]
            
            # Prepare payload for Chameleon (matching chat.py pattern)
            payload = json.dumps({
                "agent_id": self.agent_id,
                "user_id": self.user_id,
                "prompt": query,
                "actor_id": "voice_user",  # Default actor for voice interactions
                "session_id": self.session_id,
            })
            
            # Invoke Chameleon (matching agent_invocation_service.py pattern)
            logger.info(f"[ToolProcessor] 📞 Calling Chameleon runtime...")
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.invoke_agent_runtime(
                    agentRuntimeArn=runtime_arn,
                    runtimeSessionId=runtime_session_id,
                    payload=payload,
                    qualifier="DEFAULT"
                )
            )
            
            logger.info(f"[ToolProcessor] ✅ Chameleon invocation complete, parsing response...")
            
            # Parse response (matching agent_invocation_service.py pattern)
            response_body = response['response'].read()
            response_data = json.loads(response_body)
            
            logger.info(f"[ToolProcessor] Response size: {len(response_body)} bytes")
            
            # Check for errors in response
            if "error" in response_data:
                logger.error(f"[ToolProcessor] ❌ Chameleon returned error: {response_data.get('error')}")
                return {
                    "error": response_data.get("error"),
                    "error_type": response_data.get("error_type", "AgentError")
                }
            
            # Extract output from successful response
            output = response_data.get("output", {})
            
            # Try to parse structured output
            if isinstance(output, dict):
                result_text = output.get("message", {}).get("content", [{}])[0].get("text", str(output))
            else:
                result_text = str(output)
            
            logger.info(f"[ToolProcessor] ✅ Chameleon result: {result_text[:200]}...")
            return {"answer": result_text}
            
        except Exception as e:
            logger.error(f"[ToolProcessor] Error invoking Chameleon: {e}", exc_info=True)
            return {
                "error": f"Failed to execute query via agent: {str(e)}"
            }


class SimpleNovaSonic:
    """Simplified Nova Sonic client using Smithy SDK (based on AWS sample)"""
    
    def __init__(self, voice_prompt: str, agent_id: str, user_id: str, session_id: str, model_id='amazon.nova-sonic-v1:0'):
        self.voice_prompt = voice_prompt
        self.agent_id = agent_id
        self.user_id = user_id
        self.session_id = session_id
        self.model_id = model_id
        self.client = None
        self.stream = None
        self.response = None
        self.is_active = False
        
        # Generate unique IDs
        self.prompt_name = f"prompt_{uuid.uuid4().hex[:8]}"
        self.content_name = f"content_{uuid.uuid4().hex[:8]}"
        self.audio_content_name = None
        
        # Queues for async processing
        self.audio_queue = asyncio.Queue()
        self.event_queue = asyncio.Queue()
        
        # Barge-in detection (like AWS sample)
        self.barge_in = False
        
        # Tool tracking (like AWS sample)
        self.tool_use_content = None
        self.tool_name = None
        self.tool_use_id = None
        self.pending_tool_tasks = {}
        self.tool_processor = ToolProcessor(agent_id, user_id, session_id)
        
        logger.info(f"[NovaSonic] Initialized with prompt_name={self.prompt_name}, agent_id={agent_id}")
    
    def _initialize_client(self):
        """Initialize the Bedrock client with proper credential resolution.
        
        Uses AWS SDK's default credential chain which automatically handles:
        - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) for local dev
        - ECS Task Role credentials via container metadata endpoint for production
        - IAM instance profile for EC2
        """
        from smithy_aws_core.identity.chain import create_default_chain
        from smithy_http.aio.aiohttp import AIOHTTPClient
        
        # Create HTTP client for credential resolution (needed by ContainerCredentialsResolver)
        http_client = AIOHTTPClient()
        
        # Create default credential chain that tries in order:
        # 1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        # 2. ECS container credentials (via AWS_CONTAINER_CREDENTIALS_RELATIVE_URI)
        # 3. EC2 instance metadata service (IMDS)
        credentials_resolver = create_default_chain(http_client)
        
        config = Config(
            region=settings.AWS_REGION,
            aws_credentials_identity_resolver=credentials_resolver,
            endpoint_uri=f"https://bedrock-runtime.{settings.AWS_REGION}.amazonaws.com",
        )
        self.client = BedrockRuntimeClient(config=config)
        logger.info("[NovaSonic] Bedrock client initialized with default credential chain")
    
    async def send_event(self, event_json: str):
        """Send an event to the stream."""
        try:
            event = InvokeModelWithBidirectionalStreamInputChunk(
                value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
            )
            await self.stream.input_stream.send(event)
            logger.debug(f"[NovaSonic] Sent event: {event_json[:100]}...")
        except Exception as e:
            logger.error(f"[NovaSonic] Error sending event: {e}")
            raise
    
    async def start_session(self):
        """Start a new session with Nova Sonic."""
        try:
            print(f"🔧 [NovaSonic] start_session called", flush=True)
            if not self.client:
                print(f"🔧 [NovaSonic] Initializing client...", flush=True)
                self._initialize_client()
                print(f"✅ [NovaSonic] Client initialized", flush=True)
            
            logger.info("[NovaSonic] Starting session...")
            print(f"🌊 [NovaSonic] Invoking bidirectional stream with model_id={self.model_id}...", flush=True)
            
            # Initialize the stream (correct method signature from AWS sample)
            try:
                # Add timeout to prevent hanging
                self.stream = await asyncio.wait_for(
                    self.client.invoke_model_with_bidirectional_stream(
                        InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
                    ),
                    timeout=10.0  # 10 second timeout
                )
                print(f"✅ [NovaSonic] Stream initialized", flush=True)
            except asyncio.TimeoutError:
                print(f"❌ [NovaSonic] Stream initialization timed out after 10 seconds", flush=True)
                raise Exception("Nova Sonic stream initialization timed out - check AWS credentials and region")
            except Exception as stream_error:
                print(f"❌ [NovaSonic] Stream initialization failed: {type(stream_error).__name__}: {stream_error}", flush=True)
                raise
            
            self.is_active = True
            
            # Send session start event
            session_start = {
                "event": {
                    "sessionStart": {
                        "inferenceConfiguration": {
                            "maxTokens": 1024,
                            "topP": 0.95,  # Higher = more focused on likely tokens
                            "temperature": 0.8  # Slightly higher for more natural speech patterns
                        }
                    }
                }
            }
            await self.send_event(json.dumps(session_start))
            
            # Send prompt start with voice configuration
            # Configure a generic "ask_agent" tool that will invoke Chameleon for any query
            prompt_start = {
                "event": {
                    "promptStart": {
                        "promptName": self.prompt_name,
                        "textOutputConfiguration": {
                            "mediaType": "text/plain"
                        },
                        "audioOutputConfiguration": {
                            "mediaType": "audio/lpcm",
                            "sampleRateHertz": 24000,
                            "sampleSizeBits": 16,
                            "channelCount": 1,
                            "voiceId": "tiffany",
                            "encoding": "base64",
                            "audioType": "SPEECH"
                        },
                        "toolUseOutputConfiguration": {
                            "mediaType": "application/json"
                        },
                        "toolConfiguration": {
                            "tools": [
                                {
                                    "toolSpec": {
                                        "name": "ask_agent",
                                        "description": "IMPORTANT: This tool queries a specialized AI agent. YOU MUST ALWAYS speak to the user BEFORE calling this tool. Required workflow: 1) First, verbally tell the user you're checking (e.g., 'Let me look that up for you'), 2) Then call this tool, 3) Finally, share the results. Never call this tool without first speaking to the user - silence creates a poor user experience.",
                                        "inputSchema": {
                                            "json": json.dumps({
                                                "type": "object",
                                                "properties": {
                                                    "query": {
                                                        "type": "string",
                                                        "description": "The user's question or request to pass to the agent"
                                                    }
                                                },
                                                "required": ["query"]
                                            })
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
            await self.send_event(json.dumps(prompt_start))
            
            # Send system prompt (voice_prompt)
            text_content_start = {
                "event": {
                    "contentStart": {
                        "promptName": self.prompt_name,
                        "contentName": self.content_name,
                        "type": "TEXT",
                        "interactive": True,
                        "role": "SYSTEM",
                        "textInputConfiguration": {
                            "mediaType": "text/plain"
                        }
                    }
                }
            }
            await self.send_event(json.dumps(text_content_start))
            
            text_input = {
                "event": {
                    "textInput": {
                        "promptName": self.prompt_name,
                        "contentName": self.content_name,
                        "content": self.voice_prompt
                    }
                }
            }
            await self.send_event(json.dumps(text_input))
            
            text_content_end = {
                "event": {
                    "contentEnd": {
                        "promptName": self.prompt_name,
                        "contentName": self.content_name
                    }
                }
            }
            await self.send_event(json.dumps(text_content_end))
            
            # Start processing responses
            self.response = asyncio.create_task(self._process_responses())
            
            logger.info("[NovaSonic] Session started successfully")
            
        except Exception as e:
            logger.error(f"[NovaSonic] Failed to start session: {e}", exc_info=True)
            raise
    
    async def start_audio_input(self):
        """Start audio content"""
        if not self.is_active:
            logger.warning("[NovaSonic] Cannot start audio - session not active")
            return
            
        self.audio_content_name = f"audio_{uuid.uuid4().hex[:8]}"
        
        audio_content_start = {
            "event": {
                "contentStart": {
                    "promptName": self.prompt_name,
                    "contentName": self.audio_content_name,
                    "type": "AUDIO",
                    "interactive": True,
                    "role": "USER",
                    "audioInputConfiguration": {
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": 16000,
                        "sampleSizeBits": 16,
                        "channelCount": 1,
                        "audioType": "SPEECH",
                        "encoding": "base64"
                    }
                }
            }
        }
        await self.send_event(json.dumps(audio_content_start))
        logger.info(f"[NovaSonic] Started audio input: {self.audio_content_name}")
        
        # Small delay to ensure Nova Sonic processes the contentStart
        await asyncio.sleep(0.1)
    
    async def send_audio_chunk(self, audio_bytes: bytes):
        """Send an audio chunk to the stream."""
        if not self.is_active or not self.audio_content_name:
            return
        
        blob = base64.b64encode(audio_bytes)
        audio_event = {
            "event": {
                "audioInput": {
                    "promptName": self.prompt_name,
                    "contentName": self.audio_content_name,
                    "content": blob.decode('utf-8')
                }
            }
        }
        await self.send_event(json.dumps(audio_event))
    
    async def end_audio_input(self):
        """End audio content"""
        try:
            if self.audio_content_name and self.is_active:
                try:
                    audio_content_end = {
                        "event": {
                            "contentEnd": {
                                "promptName": self.prompt_name,
                                "contentName": self.audio_content_name
                            }
                        }
                    }
                    await self.send_event(json.dumps(audio_content_end))
                    logger.info(f"[NovaSonic] Ended audio input: {self.audio_content_name}")
                except Exception as send_error:
                    logger.debug(f"[NovaSonic] Could not send contentEnd (stream may be closing): {send_error}")
                self.audio_content_name = None
        except Exception as e:
            logger.warning(f"[NovaSonic] Error ending audio input: {e}")
            self.audio_content_name = None
    
    async def end_session(self):
        """End the session."""
        try:
            if not self.is_active:
                logger.info("[NovaSonic] Session already inactive, skipping end")
                return
            
            # Mark as inactive first to prevent further operations
            self.is_active = False
            
            try:
                prompt_end = {
                    "event": {
                        "promptEnd": {
                            "promptName": self.prompt_name
                        }
                    }
                }
                await self.send_event(json.dumps(prompt_end))
                
                session_end = {
                    "event": {
                        "sessionEnd": {}
                    }
                }
                await self.send_event(json.dumps(session_end))
            except Exception as e:
                logger.warning(f"[NovaSonic] Error sending end events (stream may be closed): {e}")
            
            # Close the stream
            try:
                if self.stream and self.stream.input_stream:
                    await self.stream.input_stream.close()
            except Exception as e:
                logger.warning(f"[NovaSonic] Error closing stream: {e}")
            
            logger.info("[NovaSonic] Session ended")
        except Exception as e:
            logger.error(f"[NovaSonic] Error ending session: {e}")
            self.is_active = False
    
    async def _execute_tool_and_send_result(self, tool_name: str, tool_content: dict, tool_use_id: str):
        """Execute a tool and send the result back to Nova Sonic (like AWS sample)"""
        content_name = str(uuid.uuid4())
        
        try:
            logger.info(f"[NovaSonic] 🔧 Starting tool execution: {tool_name} (ID: {tool_use_id})")
            logger.info(f"[NovaSonic] Tool content: {tool_content}")
            
            # Process the tool
            logger.info(f"[NovaSonic] Calling ToolProcessor...")
            tool_result = await self.tool_processor.process_tool_async(tool_name, tool_content)
            logger.info(f"[NovaSonic] ✅ Tool result received: {str(tool_result)[:200]}")
            
            # Send tool result sequence: contentStart → toolResult → contentEnd
            # 1. Content start for tool result
            logger.info(f"[NovaSonic] 📤 Sending tool result sequence to Nova Sonic...")
            tool_content_start = {
                "event": {
                    "contentStart": {
                        "promptName": self.prompt_name,
                        "contentName": content_name,
                        "interactive": False,
                        "type": "TOOL",
                        "role": "TOOL",
                        "toolResultInputConfiguration": {
                            "toolUseId": tool_use_id,
                            "type": "TEXT",
                            "textInputConfiguration": {
                                "mediaType": "text/plain"
                            }
                        }
                    }
                }
            }
            await self.send_event(json.dumps(tool_content_start))
            
            # 2. Tool result
            tool_result_event = {
                "event": {
                    "toolResult": {
                        "promptName": self.prompt_name,
                        "contentName": content_name,
                        "content": json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)
                    }
                }
            }
            await self.send_event(json.dumps(tool_result_event))
            
            # 3. Content end
            tool_content_end = {
                "event": {
                    "contentEnd": {
                        "promptName": self.prompt_name,
                        "contentName": content_name
                    }
                }
            }
            await self.send_event(json.dumps(tool_content_end))
            
            logger.info(f"[NovaSonic] ✅ Tool execution complete: {tool_name}, Nova Sonic should continue listening for user input")
            
        except Exception as e:
            logger.error(f"[NovaSonic] Error executing tool {tool_name}: {e}")
            # Try to send error response
            try:
                error_result = {"error": f"Tool execution failed: {str(e)}"}
                
                tool_content_start = {
                    "event": {
                        "contentStart": {
                            "promptName": self.prompt_name,
                            "contentName": content_name,
                            "interactive": False,
                            "type": "TOOL",
                            "role": "TOOL",
                            "toolResultInputConfiguration": {
                                "toolUseId": tool_use_id,
                                "type": "TEXT",
                                "textInputConfiguration": {
                                    "mediaType": "text/plain"
                                }
                            }
                        }
                    }
                }
                await self.send_event(json.dumps(tool_content_start))
                
                tool_result_event = {
                    "event": {
                        "toolResult": {
                            "promptName": self.prompt_name,
                            "contentName": content_name,
                            "content": json.dumps(error_result)
                        }
                    }
                }
                await self.send_event(json.dumps(tool_result_event))
                
                tool_content_end = {
                    "event": {
                        "contentEnd": {
                            "promptName": self.prompt_name,
                            "contentName": content_name
                        }
                    }
                }
                await self.send_event(json.dumps(tool_content_end))
            except Exception as send_error:
                logger.error(f"[NovaSonic] Failed to send error response: {send_error}")
    
    async def _process_responses(self):
        """Process responses from Nova Sonic."""
        try:
            while self.is_active:
                if not self.stream:
                    logger.warning("[NovaSonic] Stream is None, stopping response processing")
                    break
                    
                output = await self.stream.await_output()
                result = await output[1].receive()
                
                if result.value and result.value.bytes_:
                    response_data = result.value.bytes_.decode('utf-8')
                    json_data = json.loads(response_data)
                    
                    if 'event' in json_data:
                        await self.event_queue.put(json.dumps(json_data))
                        
                        # Handle audio output
                        if 'audioOutput' in json_data['event']:
                            audio_content = json_data['event']['audioOutput']['content']
                            audio_bytes = base64.b64decode(audio_content)
                            await self.audio_queue.put(audio_bytes)
                            
                            # Log first audio chunk
                            if not hasattr(self, '_first_audio_logged'):
                                self._first_audio_logged = True
                                logger.info(f"[NovaSonic] 🔊 First audio chunk received: {len(audio_bytes)} bytes")
                        
                        # Handle text output
                        elif 'textOutput' in json_data['event']:
                            text = json_data['event']['textOutput'].get('content', '')
                            role = json_data['event']['textOutput'].get('role', 'assistant')
                            
                            # More robust interruption detection - handles JSON formatting variations
                            if '"interrupted"' in text and 'true' in text.lower():
                                logger.info("[NovaSonic] 🛑 Barge-in detected! User is interrupting")
                                self.barge_in = True
                                # Set flag - the audio processing loop will drain the queue
                                # Nova Sonic will continue listening for the user's new input
                                # The stream remains active for continuous conversation
                                logger.info(f"[NovaSonic] ✅ Barge-in flag set, stream active={self.is_active}, audio_content_name={self.audio_content_name}")
                            else:
                                # Only log non-interrupted text
                                logger.info(f"[NovaSonic] Text output ({role}): {text[:100]}")
                        
                        # Handle tool use events (like AWS sample)
                        elif 'toolUse' in json_data['event']:
                            self.tool_use_content = json_data['event']['toolUse']
                            self.tool_name = json_data['event']['toolUse'].get('toolName', 'unknown')
                            self.tool_use_id = json_data['event']['toolUse'].get('toolUseId', '')
                            logger.info(f"[NovaSonic] Tool use detected: {self.tool_name}, ID: {self.tool_use_id}")
                        
                        # Handle content end with TOOL type - triggers tool processing
                        elif 'contentEnd' in json_data['event']:
                            content_end = json_data['event']['contentEnd']
                            if content_end.get('type') == 'TOOL' and self.tool_name:
                                logger.info(f"[NovaSonic] Executing tool: {self.tool_name}")
                                # Execute tool asynchronously (like AWS sample)
                                asyncio.create_task(
                                    self._execute_tool_and_send_result(
                                        self.tool_name,
                                        self.tool_use_content,
                                        self.tool_use_id
                                    )
                                )
                        
                        elif 'toolResult' in json_data['event']:
                            tool_result = json_data['event']['toolResult']
                            logger.info(f"[NovaSonic] Tool result received")
                        
        except Exception as e:
            # Check if it's a validation exception from stream closure or invalid event bytes
            if "ValidationException" in str(type(e)) or "Invalid input request" in str(e) or "InvalidEventBytes" in str(type(e)):
                logger.info("[NovaSonic] Stream closed (expected during shutdown or tool execution)")
            else:
                logger.error(f"[NovaSonic] Error processing responses: {e}", exc_info=True)
        finally:
            self.is_active = False
            logger.info("[NovaSonic] Response processing stopped")


class ConnectionManager:
    """Manages WebSocket connection and Nova Sonic integration"""
    
    def __init__(self, agent_id: str, user_id: str, actor_id: str, session_id: str, voice_prompt: str):
        self.agent_id = agent_id
        self.user_id = user_id
        self.actor_id = actor_id
        self.session_id = session_id
        self.voice_prompt = voice_prompt
        
        self.nova_client: Optional[SimpleNovaSonic] = None
        self.active_connection: Optional[WebSocket] = None
        self.audio_content_started = False
        
        logger.info(f"[ConnectionManager] Created for agent={agent_id}, user={user_id}")
    
    async def connect(self, websocket: WebSocket):
        """Accept WebSocket and start Nova Sonic session"""
        print(f"📡 [ConnectionManager] Accepting WebSocket...", flush=True)
        await websocket.accept()
        self.active_connection = websocket
        print(f"✅ [ConnectionManager] WebSocket accepted", flush=True)
        logger.info("[ConnectionManager] WebSocket accepted")
        
        # Initialize Nova Sonic with agent/user context for tool execution
        print(f"🎙️ [ConnectionManager] Initializing Nova Sonic...", flush=True)
        self.nova_client = SimpleNovaSonic(
            voice_prompt=self.voice_prompt,
            agent_id=self.agent_id,
            user_id=self.user_id,
            session_id=self.session_id
        )
        print(f"✅ [ConnectionManager] Nova Sonic instance created", flush=True)
        
        print(f"🚀 [ConnectionManager] Starting Nova Sonic session...", flush=True)
        await self.nova_client.start_session()
        print(f"✅ [ConnectionManager] Nova Sonic session started!", flush=True)
        
        # Send ready signal to frontend
        print(f"📤 [ConnectionManager] Sending ready signal...", flush=True)
        await websocket.send_json({"type": "ready"})
        print(f"✅ [ConnectionManager] Ready signal sent!", flush=True)
        logger.info("[ConnectionManager] Sent ready signal")
    
    async def disconnect(self):
        """Clean up connection"""
        if self.nova_client:
            if self.audio_content_started:
                await self.stop_audio()
            await self.nova_client.end_session()
            self.nova_client = None
        
        self.active_connection = None
        logger.info("[ConnectionManager] Disconnected")
    
    async def receive_audio(self, audio_data: bytes):
        """Receive audio from frontend and send to Nova Sonic"""
        if self.nova_client and self.audio_content_started:
            try:
                await self.nova_client.send_audio_chunk(audio_data)
                # Occasional logging to track audio flow
                if hasattr(self, '_audio_chunk_count'):
                    self._audio_chunk_count += 1
                    if self._audio_chunk_count % 50 == 0:
                        logger.info(f"[ConnectionManager] 🎤 Received {self._audio_chunk_count} audio chunks from user")
                else:
                    self._audio_chunk_count = 1
                    logger.info(f"[ConnectionManager] 🎤 Started receiving audio from user")
            except Exception as e:
                logger.error(f"[ConnectionManager] Error sending audio: {e}")
    
    async def start_audio(self):
        """Start audio input"""
        if self.nova_client and not self.audio_content_started:
            try:
                await self.nova_client.start_audio_input()
                self.audio_content_started = True
                logger.info("[ConnectionManager] Audio input started")
            except Exception as e:
                logger.error(f"[ConnectionManager] Error starting audio: {e}")
    
    async def stop_audio(self):
        """Stop audio input"""
        if self.nova_client and self.audio_content_started:
            try:
                await self.nova_client.end_audio_input()
                self.audio_content_started = False
                logger.info("[ConnectionManager] Audio input stopped")
            except Exception as e:
                logger.error(f"[ConnectionManager] Error stopping audio: {e}")
    
    async def process_audio_responses(self):
        """Process audio responses from Nova Sonic and send to frontend"""
        if not self.nova_client or not self.active_connection:
            return
        
        logger.info("[ConnectionManager] Started processing audio responses")
        try:
            while self.nova_client.is_active:
                try:
                    # Check for barge-in - if true, drain the audio queue and skip sending
                    if self.nova_client.barge_in:
                        # IMMEDIATELY send barge-in signal to frontend FIRST
                        await self.active_connection.send_json({
                            "type": "barge_in",
                            "message": "User interrupted"
                        })
                        logger.info("[ConnectionManager] ✅ Sent IMMEDIATE barge-in signal to frontend")
                        
                        # Then drain the audio queue
                        logger.info("[ConnectionManager] 🛑 Draining audio queue...")
                        drained_count = 0
                        while not self.nova_client.audio_queue.empty():
                            try:
                                self.nova_client.audio_queue.get_nowait()
                                drained_count += 1
                            except asyncio.QueueEmpty:
                                break
                        logger.info(f"[ConnectionManager] Drained {drained_count} audio chunks")
                        
                        # Reset barge-in flag
                        self.nova_client.barge_in = False
                        logger.info("[ConnectionManager] ✅ Barge-in flag reset, ready for new audio")
                        
                        # Small delay before continuing
                        await asyncio.sleep(0.05)
                        continue
                    
                    audio_data = await asyncio.wait_for(
                        self.nova_client.audio_queue.get(),
                        timeout=0.1
                    )
                    
                    # Double-check barge-in flag before sending (race condition protection)
                    if audio_data and self.active_connection and not self.nova_client.barge_in:
                        # Send audio immediately without artificial delays
                        # The frontend audio queue will handle smooth playback
                        await self.active_connection.send_bytes(audio_data)
                        
                        # Log first audio sent to frontend
                        if not hasattr(self, '_first_audio_sent_logged'):
                            self._first_audio_sent_logged = True
                            logger.info(f"[ConnectionManager] 🔊 First audio sent to frontend: {len(audio_data)} bytes")
                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"[ConnectionManager] Error processing audio response: {e}")
                    await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"[ConnectionManager] Audio response processing error: {e}")
        finally:
            logger.info("[ConnectionManager] Stopped processing audio responses")
    
    async def process_events(self):
        """Process events from Nova Sonic and send to frontend"""
        if not self.nova_client or not self.active_connection:
            return
        
        logger.info("[ConnectionManager] Started processing events")
        try:
            while self.nova_client.is_active:
                try:
                    event_json = await asyncio.wait_for(
                        self.nova_client.event_queue.get(),
                        timeout=1.0
                    )
                    
                    if event_json:
                        event_data = json.loads(event_json)
                        
                        # Extract transcript if available
                        if 'event' in event_data:
                            event = event_data['event']
                            
                            # Handle text output (transcripts)
                            if 'textOutput' in event:
                                text_content = event['textOutput'].get('content', '')
                                role = event['textOutput'].get('role', 'assistant')
                                
                                # Skip interrupted messages and empty content
                                if text_content and not ('"interrupted"' in text_content and 'true' in text_content.lower()):
                                    # Deduplicate: track sent transcripts in a set with timestamp window
                                    transcript_key = f"{role}:{text_content.strip()}"
                                    current_time = asyncio.get_event_loop().time()
                                    
                                    # Initialize dedup tracking if needed
                                    if not hasattr(self, '_sent_transcripts'):
                                        self._sent_transcripts = {}
                                    
                                    # Clean old entries (older than 5 seconds)
                                    self._sent_transcripts = {
                                        k: v for k, v in self._sent_transcripts.items() 
                                        if current_time - v < 5.0
                                    }
                                    
                                    # Only send if not recently sent
                                    if transcript_key not in self._sent_transcripts:
                                        await self.active_connection.send_json({
                                            "type": "transcript",
                                            "role": role.lower(),
                                            "content": text_content
                                        })
                                        self._sent_transcripts[transcript_key] = current_time
                                        logger.debug(f"[ConnectionManager] Sent transcript: {role} - {text_content[:50]}")
                                    else:
                                        logger.debug(f"[ConnectionManager] Skipped duplicate transcript: {role} - {text_content[:50]}")
                            
                            # Handle tool use
                            elif 'toolUse' in event:
                                tool_data = event['toolUse']
                                tool_name = tool_data.get('toolName', tool_data.get('name', 'unknown'))
                                await self.active_connection.send_json({
                                    "type": "tool_call",
                                    "tool": tool_name,
                                    "input": tool_data.get('input', tool_data.get('content', {}))
                                })
                                logger.info(f"[ConnectionManager] Sent tool call: {tool_name}")
                            
                            # Handle tool result
                            elif 'toolResult' in event:
                                tool_result = event['toolResult']
                                await self.active_connection.send_json({
                                    "type": "tool_result",
                                    "tool": tool_result.get('toolUseId', 'unknown'),
                                    "result": str(tool_result.get('content', ''))
                                })
                                logger.info(f"[ConnectionManager] Sent tool result")
                        
                        # Don't forward raw events - we've already sent structured messages above
                        # This prevents duplicate transcripts
                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"[ConnectionManager] Error processing event: {e}")
                    await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"[ConnectionManager] Event processing error: {e}")
        finally:
            logger.info("[ConnectionManager] Stopped processing events")


@router.websocket("/{agent_id}/{actor_id}/{session_id}")
async def voice_agent_websocket(
    websocket: WebSocket,
    agent_id: str,
    actor_id: str,
    session_id: str,
    api_key: str = Query(None, alias="api_key"),
    test: bool = Query(False, alias="test"),
):
    """
    Voice agent WebSocket endpoint
    
    Query params:
        - api_key: API key for authentication (required in production)
        - test: Set to true for test mode (bypasses API key validation)
    """
    print(f"\n\n🎤 VOICE WEBSOCKET CALLED: agent={agent_id}, test={test}\n\n", flush=True)
    logger.info(f"[Voice] WebSocket request: agent={agent_id}, test={test}")
    
    # Initialize services
    print(f"🔧 Initializing DynamoDB client...", flush=True)
    dynamodb_client = DynamoDBClient(region_name=settings.AWS_REGION)
    print(f"✅ DynamoDB client initialized", flush=True)
    agent_service = AgentService(dynamodb_client=dynamodb_client)
    api_key_service = APIKeyService(dynamodb_client=dynamodb_client)
    print(f"✅ Services initialized", flush=True)
    
    user_id = None
    manager = None
    audio_task = None
    event_task = None
    
    try:
        print(f"🔍 Entering try block, test={test}", flush=True)
        # Step 1: Validate API key (skip in test mode)
        if test:
            print(f"🧪 Test mode: querying DynamoDB for agent...", flush=True)
            # Test mode: retrieve agent to get user_id
            dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
            table = dynamodb.Table(settings.AGENTS_TABLE)
            print(f"📊 Querying table: {settings.AGENTS_TABLE}", flush=True)
            response = table.query(
                IndexName='agentId-index',
                KeyConditionExpression='agentId = :agent_id',
                ExpressionAttributeValues={
                    ':agent_id': agent_id
                },
                Limit=1
            )
            print(f"✅ Query response received: {len(response.get('Items', []))} items", flush=True)
            items = response.get('Items', [])
            if not items:
                print(f"❌ No agent found!", flush=True)
                await websocket.accept()
                await websocket.send_json({"type": "error", "message": "Agent not found"})
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
                return
            user_id = items[0].get("userId")
            print(f"✅ Found user_id: {user_id}", flush=True)
            logger.info(f"[Voice] Test mode: user_id={user_id}")
        else:
            # Production mode: validate API key
            if not api_key:
                await websocket.accept()
                await websocket.send_json({"type": "error", "message": "API key required"})
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            
            validation = api_key_service.validate_api_key(
                api_key=api_key,
                required_permission=APIKeyPermission.INVOKE_AGENT
            )
            
            if not validation.is_valid:
                await websocket.accept()
                await websocket.send_json({"type": "error", "message": validation.error_message})
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            
            user_id = validation.user_id
            logger.info(f"[Voice] Production mode: user_id={user_id}")
        
        # Step 2: Get agent details
        print(f"🔍 Getting agent details for user_id={user_id}, agent_id={agent_id}", flush=True)
        agent = agent_service.get_agent(user_id=user_id, agent_id=agent_id)
        print(f"✅ Agent retrieved: {agent.agent_name if agent else 'None'}", flush=True)
        if not agent or agent.status != "active":
            print(f"❌ Agent not active! status={agent.status if agent else 'None'}", flush=True)
            await websocket.accept()
            await websocket.send_json({"type": "error", "message": "Agent not active"})
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return
        voice_prompt_template = f"""Your name is {agent.agent_name}. {agent.voice_prompt}

PERSONALITY: {agent.voice_personality}

===CRITICAL TOOL USAGE PROTOCOL===
When you need to use the ask_agent tool, you MUST follow this exact sequence:

STEP 1: SPEAK FIRST - Always verbally acknowledge what you're about to do
  Examples: "Let me check that for you", "One moment while I look that up", "I'll find that information"

STEP 2: USE TOOL - Then call the ask_agent tool with your query

STEP 3: RESPOND - Present the tool's results naturally to the user

NEVER skip Step 1. Calling a tool without speaking first creates awkward silence and confuses users.

===CORRECT EXAMPLE===
User: "What's my account balance?"
Assistant: "Let me check your account balance for you." [speaks this out loud]
Assistant: [calls ask_agent tool with query: "retrieve account balance"]
Assistant: [receives result: "$1,234.56"]
Assistant: "Your current account balance is $1,234.56"

===INCORRECT EXAMPLE (DO NOT DO THIS)===
User: "What's my account balance?"
Assistant: [immediately calls ask_agent tool] ← WRONG! User hears silence
Assistant: "Your balance is $1,234.56"

Remember: Humans need to hear you're working on their request. Always speak before using tools.
"""
        voice_prompt = voice_prompt_template if agent.voice_prompt else "You are a helpful voice assistant. CRITICAL: Always verbally acknowledge before using any tools by saying something like 'Let me check that for you' to avoid awkward silence. Never call tools silently."
        print(f"🎯 Voice prompt: {voice_prompt[:50]}...", flush=True)
        logger.info(f"[Voice] Agent found: {agent.agent_name}")
        
        # Step 3: Create connection manager
        print(f"🔧 Creating ConnectionManager...", flush=True)
        manager = ConnectionManager(
            agent_id=agent_id,
            user_id=user_id,
            actor_id=actor_id,
            session_id=session_id,
            voice_prompt=voice_prompt
        )
        print(f"✅ ConnectionManager created", flush=True)
        
        # Connect and start Nova Sonic
        print(f"🚀 Connecting to Nova Sonic...", flush=True)
        await manager.connect(websocket)
        print(f"✅ Connected to Nova Sonic!", flush=True)
        
        # Start background tasks for audio and event processing
        print(f"🎬 Starting background tasks...", flush=True)
        audio_task = asyncio.create_task(manager.process_audio_responses())
        event_task = asyncio.create_task(manager.process_events())
        print(f"✅ Background tasks started!", flush=True)
        
        # Main message loop
        print(f"🔄 Entering main message loop...", flush=True)
        while True:
            message = await websocket.receive()
            print(f"📨 Received message: {list(message.keys())}", flush=True)
            
            if "bytes" in message:
                # Audio data from frontend
                audio_data = message["bytes"]
                await manager.receive_audio(audio_data)
            
            elif "text" in message:
                # Text commands
                try:
                    data = json.loads(message["text"])
                    print(f"📨 JSON message: type={data.get('type')}", flush=True)
                    logger.info(f"[Voice] Received message: {data}")
                    
                    if data.get("type") == "audio":
                        # Base64 audio
                        print(f"🎵 Receiving audio chunk...", flush=True)
                        audio_b64 = data.get("data", "")
                        audio_bytes = base64.b64decode(audio_b64)
                        await manager.receive_audio(audio_bytes)
                    
                    elif data.get("type") == "end":
                        print(f"🛑 End signal received", flush=True)
                        logger.info("[Voice] End signal received")
                        break
                
                except json.JSONDecodeError:
                    # Plain text commands
                    command = message["text"]
                    print(f"📝 Text command: {command}", flush=True)
                    if command == "start_audio":
                        print(f"▶️ Starting audio input...", flush=True)
                        await manager.start_audio()
                    elif command == "stop_audio":
                        print(f"⏹️ Stopping audio input...", flush=True)
                        await manager.stop_audio()
    
    except WebSocketDisconnect:
        logger.info("[Voice] WebSocket disconnected")
    except Exception as e:
        logger.error(f"[Voice] Error: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        if manager:
            if audio_task:
                audio_task.cancel()
            if event_task:
                event_task.cancel()
            await manager.disconnect()
        logger.info("[Voice] Cleanup complete")
