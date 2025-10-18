"""Voice agent WebSocket endpoint with Nova Sonic + Chameleon integration"""

import asyncio
import base64
import json
import logging
import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status
from pydantic import BaseModel

from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
from aws_sdk_bedrock_runtime.config import Config
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver
from rx.subject import Subject
from rx import operators as ops
from rx.scheduler.eventloop import AsyncIOScheduler

from config import settings
from dependencies import get_agent_service, get_api_key_service, get_agent_invocation_service
from services.agent_service import AgentService
from services.api_key_service import APIKeyService
from services.agent_invocation_service import AgentInvocationService
from services.conversation_logger_service import ConversationLoggerService
from models.api_key import APIKeyPermission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


class NovaSonicStreamManager:
    """
    Manages Nova Sonic bidirectional streaming with Chameleon integration
    Based on sonic_exaple.py with Chameleon tool support
    """
    
    # Event templates (from sonic_exaple.py)
    START_SESSION_EVENT = '''{
        "event": {
            "sessionStart": {
                "inferenceConfiguration": {
                    "maxTokens": 1024,
                    "topP": 0.9,
                    "temperature": 0.7
                }
            }
        }
    }'''
    
    START_PROMPT_EVENT = '''{
        "event": {
            "promptStart": {
                "promptName": "%s",
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
                    "tools": %s
                }
            }
        }
    }'''
    
    CONTENT_START_EVENT = '''{
        "event": {
            "contentStart": {
                "promptName": "%s",
                "contentName": "%s",
                "type": "AUDIO",
                "interactive": true,
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
    }'''
    
    AUDIO_EVENT_TEMPLATE = '''{
        "event": {
            "audioInput": {
                "promptName": "%s",
                "contentName": "%s",
                "content": "%s"
            }
        }
    }'''
    
    TEXT_CONTENT_START_EVENT = '''{
        "event": {
            "contentStart": {
                "promptName": "%s",
                "contentName": "%s",
                "role": "%s",
                "type": "TEXT",
                "interactive": true,
                "textInputConfiguration": {
                    "mediaType": "text/plain"
                }
            }
        }
    }'''
    
    TEXT_INPUT_EVENT = '''{
        "event": {
            "textInput": {
                "promptName": "%s",
                "contentName": "%s",
                "content": "%s"
            }
        }
    }'''
    
    CONTENT_END_EVENT = '''{
        "event": {
            "contentEnd": {
                "promptName": "%s",
                "contentName": "%s"
            }
        }
    }'''
    
    PROMPT_END_EVENT = '''{
        "event": {
            "promptEnd": {
                "promptName": "%s"
            }
        }
    }'''
    
    SESSION_END_EVENT = '''{
        "event": {
            "sessionEnd": {}
        }
    }'''
    
    TOOL_RESULT_EVENT = '''{
        "event": {
            "toolResult": {
                "promptName": "%s",
                "toolUseId": "%s",
                "content": "%s",
                "status": "success"
            }
        }
    }'''
    
    def __init__(
        self,
        agent_id: str,
        user_id: str,
        actor_id: str,
        session_id: str,
        websocket: WebSocket,
        invocation_service: AgentInvocationService,
        chameleon_runtime_arn: str,
        memory_id: str,
        region: str = "us-east-1"
    ):
        self.agent_id = agent_id
        self.user_id = user_id
        self.actor_id = actor_id
        self.session_id = session_id
        self.websocket = websocket
        self.invocation_service = invocation_service
        self.chameleon_runtime_arn = chameleon_runtime_arn
        self.memory_id = memory_id
        self.region = region
        
        # Streaming components
        self.input_subject = Subject()
        self.output_subject = Subject()
        self.audio_subject = Subject()
        self.stream_response = None
        self.is_active = False
        self.bedrock_client = None
        self.scheduler = None
        
        # Session identifiers
        self.prompt_name = str(uuid.uuid4())
        self.content_name = str(uuid.uuid4())
        self.audio_content_name = str(uuid.uuid4())
        
        # Conversation logging (using service)
        self.conversation_logger = ConversationLoggerService(agent_id, user_id, actor_id, session_id)
        
        # Audio output queue for WebSocket streaming
        self.audio_output_queue = asyncio.Queue()
        
        # Tool use tracking
        self.pending_tool_uses = {}
    
    def _initialize_client(self):
        """Initialize Bedrock Runtime client"""
        config = Config(
            endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
            region=self.region,
            aws_credentials_identity_resolver=EnvironmentCredentialsResolver()
        )
        self.bedrock_client = BedrockRuntimeClient(config=config)
    
    def _create_chameleon_tool_definition(self) -> list:
        """Create Chameleon tool definition for Nova Sonic"""
        tool_def = {
            "toolSpec": {
                "name": "business_agent",
                "description": f"Invoke the custom business logic agent to handle complex queries. Use this when you need to access business-specific knowledge, policies, or procedures.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The user's query to process"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        }
        return [tool_def]
    
    async def _invoke_chameleon_tool(self, tool_use_id: str, query: str) -> str:
        """Invoke Chameleon and return result"""
        try:
            logger.info(f"[Chameleon Tool] Invoking for query: {query[:100]}...")
            
            result = self.invocation_service.invoke_agent(
                runtime_arn=self.chameleon_runtime_arn,
                agent_id=self.agent_id,
                user_id=self.user_id,
                actor_id=self.actor_id,
                session_id=self.session_id,
                prompt=query
            )
            
            if result.get("success"):
                response_text = result["result"]
                logger.info(f"[Chameleon Tool] Success: {response_text[:100]}...")
                
                # Log tool call
                self.conversation_logger.log_tool_call(
                    tool_name="business_agent",
                    tool_input={"query": query},
                    tool_output=response_text
                )
                
                return response_text
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"[Chameleon Tool] Error: {error}")
                return f"I encountered an error accessing the business system: {error}"
                
        except Exception as e:
            logger.error(f"[Chameleon Tool] Exception: {e}", exc_info=True)
            return f"I'm sorry, I couldn't access the business system right now."
    
    async def initialize_stream(self, system_prompt: str):
        """Initialize Nova Sonic bidirectional stream"""
        if not self.bedrock_client:
            self._initialize_client()
        
        self.scheduler = AsyncIOScheduler(asyncio.get_event_loop())
        
        try:
            # Initialize bidirectional stream
            self.stream_response = await self.bedrock_client.invoke_model_with_bidirectional_stream(
                InvokeModelWithBidirectionalStreamOperationInput(model_id="amazon.nova-sonic-v1:0")
            )
            
            self.is_active = True
            
            # Create tool configuration with Chameleon
            tools = self._create_chameleon_tool_definition()
            tools_json = json.dumps(tools)
            
            # Send initialization events
            prompt_event = self.START_PROMPT_EVENT % (self.prompt_name, tools_json)
            text_content_start = self.TEXT_CONTENT_START_EVENT % (self.prompt_name, self.content_name, "SYSTEM")
            text_content = self.TEXT_INPUT_EVENT % (self.prompt_name, self.content_name, system_prompt)
            text_content_end = self.CONTENT_END_EVENT % (self.prompt_name, self.content_name)
            
            init_events = [self.START_SESSION_EVENT, prompt_event, text_content_start, text_content, text_content_end]
            
            for event in init_events:
                await self.send_raw_event(event)
            
            # Start response processing
            asyncio.create_task(self._process_responses())
            asyncio.create_task(self._stream_audio_to_websocket())
            
            # Setup RxPy subscriptions
            self.input_subject.pipe(
                ops.subscribe_on(self.scheduler)
            ).subscribe(
                on_next=lambda event: asyncio.create_task(self.send_raw_event(event)),
                on_error=lambda e: logger.error(f"Input stream error: {e}")
            )
            
            self.audio_subject.pipe(
                ops.subscribe_on(self.scheduler)
            ).subscribe(
                on_next=lambda audio_data: asyncio.create_task(self._handle_audio_input(audio_data)),
                on_error=lambda e: logger.error(f"Audio stream error: {e}")
            )
            
            logger.info("[NovaSonic] Stream initialized successfully")
            return self
            
        except Exception as e:
            logger.error(f"[NovaSonic] Error initializing stream: {e}", exc_info=True)
            self.is_active = False
            raise
    
    async def send_raw_event(self, event_json: str):
        """Send event to Nova Sonic"""
        if not self.stream_response or not self.is_active:
            return
        
        event = InvokeModelWithBidirectionalStreamInputChunk(
            value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
        )
        
        try:
            await self.stream_response.input_stream.send(event)
        except Exception as e:
            logger.error(f"[NovaSonic] Error sending event: {e}")
            self.input_subject.on_error(e)
    
    async def _handle_audio_input(self, data: Dict):
        """Process audio input from WebSocket"""
        audio_bytes = data.get("audio_bytes")
        if not audio_bytes:
            return
        
        try:
            # Base64 encode
            blob = base64.b64encode(audio_bytes)
            audio_event = self.AUDIO_EVENT_TEMPLATE % (
                self.prompt_name,
                self.audio_content_name,
                blob.decode('utf-8')
            )
            await self.send_raw_event(audio_event)
        except Exception as e:
            logger.error(f"[NovaSonic] Error processing audio: {e}")
    
    def add_audio_chunk(self, audio_bytes: bytes):
        """Add audio chunk from WebSocket"""
        self.audio_subject.on_next({
            'audio_bytes': audio_bytes,
            'prompt_name': self.prompt_name,
            'content_name': self.audio_content_name
        })
    
    async def send_audio_content_start_event(self):
        """Start audio content"""
        content_start_event = self.CONTENT_START_EVENT % (self.prompt_name, self.audio_content_name)
        await self.send_raw_event(content_start_event)
    
    async def send_audio_content_end_event(self):
        """End audio content"""
        content_end_event = self.CONTENT_END_EVENT % (self.prompt_name, self.audio_content_name)
        await self.send_raw_event(content_end_event)
    
    async def _process_responses(self):
        """Process responses from Nova Sonic"""
        try:
            while self.is_active:
                try:
                    output = await self.stream_response.await_output()
                    result = await output[1].receive()
                    
                    if result.value and result.value.bytes_:
                        response_data = result.value.bytes_.decode('utf-8')
                        json_data = json.loads(response_data)
                        
                        if 'event' in json_data:
                            event = json_data['event']
                            
                            # Handle text output (transcription/response)
                            if 'textOutput' in event:
                                text_content = event['textOutput']['content']
                                role = event['textOutput'].get('role', 'ASSISTANT')
                                
                                # Log to conversation history
                                self.conversation_logger.log_turn(role, text_content, "text")
                                
                                # Send transcript to WebSocket
                                await self.websocket.send_json({
                                    "type": "transcript",
                                    "role": role.lower(),
                                    "content": text_content
                                })
                            
                            # Handle audio output
                            elif 'audioOutput' in event:
                                audio_content = event['audioOutput']['content']
                                audio_bytes = base64.b64decode(audio_content)
                                await self.audio_output_queue.put(audio_bytes)
                            
                            # Handle tool use (Chameleon invocation)
                            elif 'toolUse' in event:
                                tool_use = event['toolUse']
                                tool_use_id = tool_use['toolUseId']
                                tool_name = tool_use['name']
                                tool_input = json.loads(tool_use['input'])
                                
                                logger.info(f"[NovaSonic] Tool use: {tool_name} ({tool_use_id})")
                                
                                # Send tool call notification to WebSocket
                                await self.websocket.send_json({
                                    "type": "tool_call",
                                    "tool": tool_name,
                                    "input": tool_input
                                })
                                
                                # Invoke Chameleon
                                if tool_name == "business_agent":
                                    query = tool_input.get("query", "")
                                    result_text = await self._invoke_chameleon_tool(tool_use_id, query)
                                    
                                    # Send tool result back to Nova Sonic
                                    tool_result_event = self.TOOL_RESULT_EVENT % (
                                        self.prompt_name,
                                        tool_use_id,
                                        result_text
                                    )
                                    await self.send_raw_event(tool_result_event)
                                    
                                    # Notify WebSocket
                                    await self.websocket.send_json({
                                        "type": "tool_result",
                                        "tool": tool_name,
                                        "result": result_text[:200]  # Truncate for UI
                                    })
                        
                        self.output_subject.on_next(json_data)
                        
                except StopAsyncIteration:
                    break
                except Exception as e:
                    logger.error(f"[NovaSonic] Error receiving response: {e}")
                    self.output_subject.on_error(e)
                    break
        except Exception as e:
            logger.error(f"[NovaSonic] Response processing error: {e}")
            self.output_subject.on_error(e)
        finally:
            if self.is_active:
                self.output_subject.on_completed()
    
    async def _stream_audio_to_websocket(self):
        """Stream audio output to WebSocket"""
        while self.is_active:
            try:
                audio_data = await asyncio.wait_for(
                    self.audio_output_queue.get(),
                    timeout=0.1
                )
                
                if audio_data:
                    # Send base64 encoded audio to WebSocket
                    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                    await self.websocket.send_json({
                        "type": "audio",
                        "data": audio_b64
                    })
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if self.is_active:
                    logger.error(f"[NovaSonic] Error streaming audio: {e}")
                await asyncio.sleep(0.05)
    
    async def close(self):
        """Close stream and save conversation history"""
        if not self.is_active:
            return
        
        self.input_subject.on_completed()
        self.audio_subject.on_completed()
        
        await self.send_audio_content_end_event()
        
        prompt_end_event = self.PROMPT_END_EVENT % self.prompt_name
        await self.send_raw_event(prompt_end_event)
        await self.send_raw_event(self.SESSION_END_EVENT)
        
        if self.stream_response:
            await self.stream_response.input_stream.close()
        
        # Save conversation history
        await self.conversation_logger.save_to_dynamodb()
        
        self.is_active = False
        logger.info("[NovaSonic] Stream closed")


@router.websocket("/{agent_id}/{actor_id}/{session_id}")
async def voice_agent_websocket(
    websocket: WebSocket,
    agent_id: str,
    actor_id: str,
    session_id: str,
    api_key: str = Query(..., alias="api_key"),
    agent_service: AgentService = Depends(get_agent_service),
    api_key_service: APIKeyService = Depends(get_api_key_service),
    invocation_service: AgentInvocationService = Depends(get_agent_invocation_service),
):
    """
    Voice agent WebSocket endpoint
    
    Handles bidirectional voice streaming with Nova Sonic + Chameleon integration
    
    Client sends: {"type": "audio", "data": "<base64_audio>"}
    Client receives:
        - {"type": "audio", "data": "<base64_audio>"} - Voice response
        - {"type": "transcript", "role": "user"/"assistant", "content": "..."} - Text
        - {"type": "tool_call", "tool": "business_agent", "input": {...}} - Tool invocation
        - {"type": "tool_result", "tool": "business_agent", "result": "..."} - Tool result
    """
    stream_manager = None
    
    try:
        # Accept WebSocket connection
        await websocket.accept()
        logger.info(f"[Voice] WebSocket connected: agent={agent_id}, actor={actor_id}, session={session_id}")
        
        # Step 1: Validate API key
        validation = api_key_service.validate_key_for_agent(api_key=api_key, agent_id=agent_id)
        if not validation.valid:
            await websocket.send_json({"type": "error", "message": validation.reason})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Check voice permission
        if APIKeyPermission.VOICE not in validation.permissions:
            await websocket.send_json({"type": "error", "message": "API key does not have voice permission"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Step 2: Get agent details
        agent = agent_service.get_agent(user_id=validation.user_id, agent_id=agent_id)
        if not agent or agent.status != "active":
            await websocket.send_json({"type": "error", "message": "Agent not found or not active"})
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return
        
        if not agent.agentcore_runtime_arn:
            await websocket.send_json({"type": "error", "message": "Agent not properly deployed"})
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return
        
        # Step 3: Initialize Nova Sonic stream with Chameleon
        stream_manager = NovaSonicStreamManager(
            agent_id=agent_id,
            user_id=validation.user_id,
            actor_id=actor_id,
            session_id=session_id,
            websocket=websocket,
            invocation_service=invocation_service,
            chameleon_runtime_arn=agent.agentcore_runtime_arn,  # Chameleon ARN
            memory_id=agent.memory_id or f"voice-{agent_id}",
            region=settings.AWS_REGION
        )
        
        # Use agent's voice_prompt (Nova Sonic optimized) or fall back to generated_prompt or default
        base_prompt = (
            agent.voice_prompt 
            or agent.generated_prompt 
            or "You are a helpful voice assistant. Use the business_agent tool when customers need specialized information."
        )
        
        # Prepend agent name to system prompt
        system_prompt = f"Your name is {agent.agent_name}. {base_prompt}"
        
        logger.info(f"[Voice] Agent name: {agent.agent_name}")
        
        await stream_manager.initialize_stream(system_prompt)
        
        # Send ready signal
        await websocket.send_json({"type": "ready", "message": "Voice agent ready"})
        
        # Send audio content start
        await stream_manager.send_audio_content_start_event()
        
        # Step 4: WebSocket message loop
        while True:
            message = await websocket.receive_json()
            
            msg_type = message.get("type")
            
            if msg_type == "audio":
                # Client sending audio chunk
                audio_b64 = message.get("data")
                if audio_b64:
                    audio_bytes = base64.b64decode(audio_b64)
                    stream_manager.add_audio_chunk(audio_bytes)
            
            elif msg_type == "end":
                # Client ending session
                logger.info("[Voice] Client requested session end")
                break
            
            else:
                logger.warning(f"[Voice] Unknown message type: {msg_type}")
    
    except WebSocketDisconnect:
        logger.info("[Voice] WebSocket disconnected")
    
    except Exception as e:
        logger.error(f"[Voice] Error: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    
    finally:
        # Cleanup
        if stream_manager:
            await stream_manager.close()
        
        try:
            await websocket.close()
        except:
            pass
        
        logger.info("[Voice] WebSocket closed")


@router.get("/health")
async def voice_health():
    """Voice service health check"""
    return {"status": "healthy", "service": "voice"}

