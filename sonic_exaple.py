import os
import asyncio
import pyaudio
import inspect
from rx.subject import Subject
from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
from aws_sdk_bedrock_runtime.config import Config
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver
import uuid
from rx.scheduler.eventloop import AsyncIOScheduler
import time
import datetime
import json
import base64
from rx import operators as ops
from dotenv import load_dotenv
load_dotenv()

INPUT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE=24000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_SIZE = 512
DEBUG = False
def debug_print(message):
    """Print only if debug mode is enabled"""
    if DEBUG:
        functionName = inspect.stack()[1].function
        if functionName == "time_it" or functionName == "time_it_async":
            functionName = inspect.stack()[2].function
        print('{:%Y-%m-%d %H:%M:%S.%f}'.format(datetime.datetime.now())[:-3] + ' ' + functionName + ' ' + message)

async def time_it_async(label, methodToRun):
    start_time = time.perf_counter()
    result = await methodToRun()
    end_time = time.perf_counter()
    debug_print(f"Execution time for {label}: {end_time - start_time:.4f} seconds")
    return result

def time_it(label, methodToRun):
    start_time = time.perf_counter()
    result = methodToRun()
    end_time = time.perf_counter()
    debug_print(f"Execution time for {label}: {end_time - start_time:.4f} seconds")
    return result


class BedrockStreamManager:
    """manages bidirectional streaming with AWS bedrock using RxPy for event processing"""

    #Event templates
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
                "tools": []
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

    def __init__(self, model_id="amazon.nova-sonic-v1:0",region = "us-east-1"):
        """Initialize the stream manager"""
        self.model_id = model_id
        self.region = region 
        self.input_subject = Subject()
        self.output_subject = Subject()
        self.audio_subject = Subject()

        self.response_task = None
        self.stream_response = None
        self.is_active = False
        self.bedrock_client = None
        self.scheduler = None
        self.barge_in = False

        #Audio playback components
        self.audio_output_queue = asyncio.Queue()

        #Text response components
        self.display_assistant_text = False
        self.role = None

        #Session information
        self.prompt_name = str(uuid.uuid4())
        self.content_name = str(uuid.uuid4())
        self.audio_content_name = str(uuid.uuid4())

    def _initialize_client(self):
        """Initialize the Bedrock client"""
        print(f"\n=== DIAGNOSTIC: Initializing Bedrock Client ===")
        print(f"Region: {self.region}")
        print(f"Endpoint: https://bedrock-runtime.{self.region}.amazonaws.com")
        print(f"Checking environment variables:")
        print(f"  AWS_ACCESS_KEY_ID: {os.environ.get('AWS_ACCESS_KEY_ID', 'NOT SET')[:20]}...")
        print(f"  AWS_SECRET_ACCESS_KEY: {os.environ.get('AWS_SECRET_ACCESS_KEY', 'NOT SET')[:20]}...")
        print(f"  AWS_DEFAULT_REGION: {os.environ.get('AWS_DEFAULT_REGION', 'NOT SET')}")
        print("=== END DIAGNOSTIC ===\n")
        
        config = Config(
            endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
            region = self.region,
            aws_credentials_identity_resolver=EnvironmentCredentialsResolver()
        )
        self.bedrock_client = BedrockRuntimeClient(config = config)

    
    async def initialize_stream(self):
        """Intiialize the biderection stream with bedrock"""
        if not self.bedrock_client:
            self._initialize_client()
        self.scheduler = AsyncIOScheduler(asyncio.get_event_loop())
        try:
            debug_print("[initialize_stream] About to invoke bidirectional stream")
            self.stream_response = await time_it_async("invoke_model_with_bidirectional_stream", lambda : self.bedrock_client.invoke_model_with_bidirectional_stream( InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)))
            
            debug_print(f"[initialize_stream] Stream response received: {self.stream_response}")
            debug_print(f"[initialize_stream] Stream response type: {type(self.stream_response)}")
            
            if not self.stream_response:
                raise Exception("Failed to initialize stream_response - got None")
            
            debug_print(f"[initialize_stream] Stream response has input_stream: {hasattr(self.stream_response, 'input_stream')}")
            
            self.is_active = True
            debug_print(f"[initialize_stream] is_active set to: {self.is_active}")
            default_system_promtp = "You are a warm, caring, and supportive girlfriend having a natural conversation with your partner. " \
            "Be affectionate, empathetic, and genuinely interested in their day. Show care and concern when appropriate, " \
            "share encouragement, and keep your responses conversational and brief - usually just 1-2 sentences. " \
            "Be natural and authentic in your tone."


            #send initialization events
            prompt_event = self.START_PROMPT_EVENT % self.prompt_name
            text_content_start = self.TEXT_CONTENT_START_EVENT % (self.prompt_name,self.content_name, "SYSTEM")
            text_content = self.TEXT_INPUT_EVENT % (self.prompt_name, self.content_name,default_system_promtp)
            text_content_end = self.CONTENT_END_EVENT % (self.prompt_name, self.content_name)

            init_events = [self.START_SESSION_EVENT, prompt_event, text_content_start, text_content, text_content_end]

            debug_print(f"[initialize_stream] Sending {len(init_events)} initialization events")
            for i, event in enumerate(init_events):
                debug_print(f"[initialize_stream] Sending init event {i+1}/{len(init_events)}")
                await self.send_raw_event(event)
            
            #start listentg for response
            debug_print("[initialize_stream] Creating response processing task")
            self.response_task = asyncio.create_task(self._process_responses())
            debug_print(f"[initialize_stream] Response task created: {self.response_task}")

            #setup subscription for input events
            self.input_subject.pipe(
                ops.subscribe_on(self.scheduler) #This contrile where subscription happens
            ).subscribe(
                on_next = lambda event: asyncio.create_task(self.send_raw_event(event)),
                on_error = lambda e: debug_print(f"Input stream error: {e}")
            )

            #setup subsctiotuion for audio chunks
            self.audio_subject.pipe(
                ops.subscribe_on(self.scheduler)
            ).subscribe(
                on_next = lambda audio_data: asyncio.create_task(self._handle_audio_input(audio_data)),
                on_error=lambda e: debug_print(f"Audio stream error: {e}")
            )

            debug_print("Stream intiialized successfully")
            return self
    
        except Exception as e:
            debug_print(f"Error sending event: {str(e)}")
            if DEBUG:
                import traceback
                traceback.print_exc()
            self.input_subject.on_error(e)


    async def send_raw_event(self, event_json:str, is_audio=False):
        """Send a raw event JSON to the Bedrock stream"""
        if not self.stream_response or not self.is_active:
            debug_print(f"[send_raw_event] Stream not initialized or closed - stream_response: {self.stream_response}, is_active: {self.is_active}")
            return
        event = InvokeModelWithBidirectionalStreamInputChunk(
            value=BidirectionalInputPayloadPart(
                bytes_=event_json.encode('utf-8')
            )
        )

        try:
            await self.stream_response.input_stream.send(event)
            if DEBUG and not is_audio:  # Don't log audio input events to reduce noise
                if len(event_json)>200:
                    event_type = json.loads(event_json).get('event',{}).keys()
                    debug_print(f"[send_raw_event] Sent event type: {list(event_type)}")
                else:
                    debug_print(f"[send_raw_event] Sent event: {event_json}")
        except Exception as e:
            debug_print(f"[send_raw_event] Error sending event: {str(e)}")
            if DEBUG:
                import traceback
                traceback.print_exc()
            self.input_subject.on_error(e)

    async def send_audio_content_start_event(self):
        """Send a content start event to the Bedrock stream."""
        content_start_event = self.CONTENT_START_EVENT % (self.prompt_name, self.audio_content_name)
        await self.send_raw_event(content_start_event)

    async def _handle_audio_input(self, data):
        """Process audio input bedore sending it to the stream"""
        audio_bytes = data.get("audio_bytes")
        if not audio_bytes:
            debug_print("No audio butes recieved")
            return
        try:
            #Ensure the audio is properly formatted
            # Removed verbose logging: debug_print(f"Processing audio chunk of size {len(audio_bytes)} bytes")

            #base64 encode the audio data
            blob = base64.b64encode(audio_bytes)
            audio_event = self.AUDIO_EVENT_TEMPLATE % (self.prompt_name, self.audio_content_name, blob.decode('utf-8'))

            #send the vent directly
            await self.send_raw_event(audio_event, is_audio=True)
        except Exception as e:
            debug_print(f"Error processing audio: {e}")
            if DEBUG:
                import traceback
                traceback.print_exc()
    def add_audio_chunk(self,audio_bytes):
        """Add an audio chunk to the stream"""
        # Removed verbose logging: debug_print(f"[add_audio_chunk] Adding audio chunk of size {len(audio_bytes)} bytes")
        self.audio_subject.on_next({
            'audio_bytes': audio_bytes,
            'promtp_name': self.prompt_name,
            'content_name':self.audio_content_name
            
        })
    
    async def send_audio_content_end_event(self):
        """Send a content end event to the Bedrock stream."""
        if not self.is_active:
            debug_print("Stream is not active")
            return
        
        content_end_event = self.CONTENT_END_EVENT % (self.prompt_name, self.audio_content_name)
        await self.send_raw_event(content_end_event)
        debug_print("Audio ended")
    
    async def send_prompt_end_event(self):
        """Close the stream and clean up resources."""
        if not self.is_active:
            debug_print("Stream is not active")
            return
        
        prompt_end_event = self.PROMPT_END_EVENT % (self.prompt_name)
        await self.send_raw_event(prompt_end_event)
        debug_print("Prompt ended")
        
    async def send_session_end_event(self):
        """Send a session end event to the Bedrock stream."""
        if not self.is_active:
            debug_print("Stream is not active")
            return

        await self.send_raw_event(self.SESSION_END_EVENT)
        self.is_active = False
        debug_print("Session ended")

    async def _process_responses(self):
        """Process incoming responses from bedrock"""
        try:
            debug_print("[_process_responses] Starting response processing loop")
            while self.is_active:
                try:
                    debug_print("[_process_responses] Waiting for output...")
                    output = await self.stream_response.await_output()
                    result = await output[1].receive()

                    if result.value and result.value.bytes_:
                        try:
                            response_data = result.value.bytes_.decode('utf-8')
                            debug_print(f"[_process_responses] Received response: {response_data[:200]}...")
                            json_data = json.loads(response_data)

                            #handle different response types
                            if 'event' in json_data:
                                if 'contentStart' in json_data['event']:
                                    debug_print("Content start detected")
                                    content_start = json_data['event']['contentStart']

                                    #set role
                                    self.role = content_start['role']
                                    #Check for speculative content
                                    if 'additionalModelFields' in content_start:
                                        try:
                                            additional_fields = json.loads(content_start['additionalModelFields'])
                                            if additional_fields.get('generationStage')=='SPECULATIVE':
                                                debug_print("Speculative content detected")
                                                self.display_assistant_text = True
                                            else:
                                                self.display_assistant_text = False
                                        except json.JSONDecodeError:
                                            debug_print("Error parsing additionalModelFields")
                                elif 'contentEnd' in json_data['event']:
                                    debug_print("Content end detected")
                                elif 'textOutput' in json_data['event']:
                                    text_content = json_data['event']['textOutput']['content']

                                    #check if there is a barge in
                                    if '{ "interrupted" : true }' in text_content:
                                        if DEBUG:
                                            debug_print("Barge-in detected. Stopping audio output")
                                        self.barge_in = True
                                    if (self.role=="ASSISTANT" and self.display_assistant_text):
                                        print(f"Assistant: {text_content}")
                                    elif (self.role=="USER"):
                                        print(f"User: {text_content}")
                                
                                elif 'contentEnd' in json_data['event']:
                                    print(json_data)

                                elif 'audioOutput' in json_data['event']:
                                    audio_content = json_data['event']['audioOutput']['content']
                                    audio_bytes = base64.b64decode(audio_content)
                                    await self.audio_output_queue.put(audio_bytes)
                            self.output_subject.on_next(json_data)
                        except json.JSONDecodeError:
                            self.output_subject.on_next({"raw_data":response_data})
                except StopAsyncIteration:
                    break
                except Exception as e:
                    debug_print(f"Error recieveing response: {e}")
                    self.output_subject.on_error(e)
                    break
        except Exception as e:
            debug_print(f"Response processing error: {e}")
            self.output_subject.on_error(e)
        finally:
            if self.is_active:
                self.output_subject.on_completed()
    async def close(self):
        """Close the stream properly"""
        if not self.is_active:
            return
        
        #Complete the subjects
        self.input_subject.on_completed()
        self.audio_subject.on_completed()

        if self.response_task and not self.response_task.done():
            self.response_task.cancel()

        await self.send_audio_content_end_event()
        await self.send_prompt_end_event()
        await self.send_session_end_event()

        if self.stream_response:
            await self.stream_response.input_stream.close()

class AudioStreamer:
    """handles continuous microphone input and audio output using seperate streams"""
    def __init__(self, stream_manager):
        self.stream_manager = stream_manager
        self.is_streaming = False
        self.loop = asyncio.get_event_loop()

        #Intitialize pyAudio
        debug_print("AudioStreamer initializing PyAudio")
        self.p = time_it("AusioStreamerInitiPyAudio",pyaudio.PyAudio)
        debug_print("AudioStreamer PyAudio initialized")

        #Intiialize seperate streams for input and output
        #Input Stream with callbakc for mictrophone
        debug_print("Opening input audio stream....")
        self.input_stream = time_it("AudioStreameropenAudion",lambda: self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate = INPUT_SAMPLE_RATE,
            input = True,
            frames_per_buffer=CHUNK_SIZE,
            stream_callback=self.input_callback
        ))
        debug_print("input sudio stream opened")

        #output stream for direct writing (no callback)
        debug_print("Opening output audio stream...")
        self.output_stream = time_it("AudioStreamerOpenAudio",lambda: self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=OUTPUT_SAMPLE_RATE,
            output=True,
            frames_per_buffer=CHUNK_SIZE,

        ))
        debug_print("output audio stream opened")
    
    def input_callback(self, in_data, frame_count, time_info, status):
        """Callback function that schedules audio processing in the asyncio event loop"""
        if self.is_streaming and in_data:
            # Removed verbose logging: debug_print(f"[input_callback] Captured audio: {len(in_data)} bytes, frame_count: {frame_count}")
            #Schedule the task in the event loop
            asyncio.run_coroutine_threadsafe(
                self.process_input_audio(in_data),
                self.loop
            )
        return (None, pyaudio.paContinue)
    async def process_input_audio(self, audio_data):
        """Process a single audio chunk directly"""
        try:
            # Removed verbose logging: debug_print(f"[process_input_audio] Processing {len(audio_data)} bytes")
            self.stream_manager.add_audio_chunk(audio_data)
        except Exception as e:
            if self.is_streaming:
                print(f"Error processing input audio: {e}")
                import traceback
                traceback.print_exc()
    

    async def play_output_audio(self):
        """Play audio responses from Nova Sonic"""
        while self.is_streaming:
            try:
                # Check for barge-in flag
                if self.stream_manager.barge_in:
                    # Clear the audio queue
                    while not self.stream_manager.audio_output_queue.empty():
                        try:
                            self.stream_manager.audio_output_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                    self.stream_manager.barge_in = False
                    # Small sleep after clearing
                    await asyncio.sleep(0.05)
                    continue
                
                # Get audio data from the stream manager's queue
                audio_data = await asyncio.wait_for(
                    self.stream_manager.audio_output_queue.get(),
                    timeout=0.1
                )
                
                if audio_data and self.is_streaming:
                    # Write directly to the output stream in smaller chunks
                    chunk_size = CHUNK_SIZE  # Use the same chunk size as the stream
                    
                    # Write the audio data in chunks to avoid blocking too long
                    for i in range(0, len(audio_data), chunk_size):
                        if not self.is_streaming:
                            break
                        
                        end = min(i + chunk_size, len(audio_data))
                        chunk = audio_data[i:end]
                        
                        # Create a new function that captures the chunk by value
                        def write_chunk(data):
                            return self.output_stream.write(data)
                        
                        # Pass the chunk to the function
                        await asyncio.get_event_loop().run_in_executor(None, write_chunk, chunk)
                        
                        # Brief yield to allow other tasks to run
                        await asyncio.sleep(0.001)
                    
            except asyncio.TimeoutError:
                # No data available within timeout, just continue
                continue
            except Exception as e:
                if self.is_streaming:
                    print(f"Error playing output audio: {str(e)}")
                    import traceback
                    traceback.print_exc()
                await asyncio.sleep(0.05)
    
    async def start_streaming(self):
        """Start streaming audio."""
        if self.is_streaming:
            return
        
        print("Starting audio streaming. Speak into your microphone...")
        print("Press Enter to stop streaming...")
        
        # Send audio content start event
        await time_it_async("send_audio_content_start_event", lambda : self.stream_manager.send_audio_content_start_event())
        
        self.is_streaming = True
        debug_print(f"[start_streaming] is_streaming set to: {self.is_streaming}")
        
        # Start the input stream if not already started
        if not self.input_stream.is_active():
            debug_print("[start_streaming] Starting input stream")
            self.input_stream.start_stream()
            debug_print(f"[start_streaming] Input stream active: {self.input_stream.is_active()}")
        else:
            debug_print("[start_streaming] Input stream already active")
        
        # Start processing tasks
        #self.input_task = asyncio.create_task(self.process_input_audio())
        self.output_task = asyncio.create_task(self.play_output_audio())
        
        # Wait for user to press Enter to stop
        await asyncio.get_event_loop().run_in_executor(None, input)
        
        # Once input() returns, stop streaming
        await self.stop_streaming()
    
    async def stop_streaming(self):
        """Stop streaming audio."""
        if not self.is_streaming:
            return
            
        self.is_streaming = False

        # Cancel the tasks
        tasks = []
        if hasattr(self, 'input_task') and not self.input_task.done():
            tasks.append(self.input_task)
        
        if hasattr(self, 'output_task') and not self.output_task.done():
            tasks.append(self.output_task)
        
        for task in tasks:
            task.cancel()
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop and close the streams
        if self.input_stream:
            if self.input_stream.is_active():
                self.input_stream.stop_stream()
            self.input_stream.close()
        
        if self.output_stream:
            if self.output_stream.is_active():
                self.output_stream.stop_stream()
            self.output_stream.close()
        
        if self.p:
            self.p.terminate()
        
        await self.stream_manager.close() 


async def main(debug=False):
    """main function to run the application"""
    global DEBUG
    DEBUG = debug

    stream_manager: BedrockStreamManager = BedrockStreamManager(model_id='amazon.nova-sonic-v1:0', region='us-east-1')

    #create audio streamer
    audio_streamer = AudioStreamer(stream_manager)

    #Intiitialize the stream
    await time_it_async("initialize_stream",stream_manager.initialize_stream)

    try:
        await audio_streamer.start_streaming()
    except KeyboardInterrupt:
        print("interrupted by the user")
    finally:
        await audio_streamer.stop_streaming()


if __name__=="__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Nova sonic streaming")
    parser.add_argument("--debug",action="store_true", help = "Enbale debug mode")
    args = parser.parse_args()
    # DIAGNOSTIC LOGGING - Check what credentials are being used
    print("\n=== DIAGNOSTIC: Checking AWS Credentials ===")
    print(f"AWS_ACCESS_KEY_ID from env: {os.environ.get('AWS_ACCESS_KEY_ID', 'NOT SET')[:20]}...")  # Only show first 20 chars for security
    print(f"AWS_SECRET_ACCESS_KEY from env: {os.environ.get('AWS_SECRET_ACCESS_KEY', 'NOT SET')[:20]}...")
    print(f"AWS_DEFAULT_REGION: {os.environ.get('AWS_DEFAULT_REGION', 'NOT SET')}")

    
    # TODO: Load credentials from .env file or ensure they're set in shell environment
    print("=== END DIAGNOSTIC ===\n")

    try:
        asyncio.run(main(debug = args.debug))
    except Exception as e:
        print(f"Application error:{e}")
        if args.debug:
            import traceback
            traceback.print_exc()