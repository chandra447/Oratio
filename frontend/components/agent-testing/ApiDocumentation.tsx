"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { IconChevronDown, IconChevronUp, IconCode, IconMessageCircle, IconMicrophone, IconBrandPython, IconBrandJavascript, IconTerminal } from "@tabler/icons-react"
import { useState } from "react"
import { CodeBlock } from "./CodeBlock"
import type { Agent } from "@/lib/api/agents"

// Language icons component
const LanguageIcon = ({ language }: { language: string }) => {
  switch (language) {
    case "python":
      return <IconBrandPython className="h-4 w-4" />
    case "javascript":
      return <IconBrandJavascript className="h-4 w-4" />
    case "bash":
      return <IconTerminal className="h-4 w-4" />
    default:
      return <IconCode className="h-4 w-4" />
  }
}

interface ApiDocumentationProps {
  agent: Agent
  apiEndpoint?: string
}

export function ApiDocumentation({ agent, apiEndpoint = "https://api.oratio.com/api/v1" }: ApiDocumentationProps) {
  const [isOpen, setIsOpen] = useState(false)
  const agentId = agent.agent_id

  // Chat API Examples
  const pythonChatExample = `import requests
import json

# Configuration
API_KEY = "your_api_key_here"
AGENT_ID = "${agentId}"
API_ENDPOINT = "${apiEndpoint}/chat"

# Create a chat session
actor_id = "user_123"  # Unique identifier for the user
session_id = "session_456"  # Unique identifier for the conversation

def chat_with_agent(message: str):
    """Send a message to the agent and get a response"""
    url = f"{API_ENDPOINT}/{AGENT_ID}/{actor_id}/{session_id}"
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": message,
        "metadata": {}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        return data["result"]
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")

# Usage
try:
    response = chat_with_agent("Hello, how can you help me?")
    print(f"Agent: {response}")
except Exception as e:
    print(f"Error: {e}")
`

  const jsChatExample = `// Configuration
const API_KEY = "your_api_key_here";
const AGENT_ID = "${agentId}";
const API_ENDPOINT = "${apiEndpoint}/chat";

// Create a chat session
const actorId = "user_123";  // Unique identifier for the user
const sessionId = "session_456";  // Unique identifier for the conversation

async function chatWithAgent(message) {
  const url = \`\${API_ENDPOINT}/\${AGENT_ID}/\${actorId}/\${sessionId}\`;
  
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      message: message,
      metadata: {}
    })
  });
  
  if (!response.ok) {
    throw new Error(\`HTTP error! status: \${response.status}\`);
  }
  
  const data = await response.json();
  return data.result;
}

// Usage
chatWithAgent("Hello, how can you help me?")
  .then(response => console.log("Agent:", response))
  .catch(error => console.error("Error:", error));
`

  const streamlitChatExample = `import streamlit as st
import requests

# Configuration
API_KEY = st.secrets["ORATIO_API_KEY"]
AGENT_ID = "${agentId}"
API_ENDPOINT = "${apiEndpoint}/chat"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = "streamlit_session_001"

# Streamlit UI
st.title("${agent.agent_name}")
st.caption("Powered by Oratio")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Call agent API
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            url = f"{API_ENDPOINT}/{AGENT_ID}/user_streamlit/{st.session_state.session_id}"
            
            headers = {
                "X-API-Key": API_KEY,
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                url, 
                headers=headers, 
                json={"message": prompt, "metadata": {}}
            )
            
            if response.status_code == 200:
                agent_response = response.json()["result"]
                st.markdown(agent_response)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": agent_response
                })
            else:
                st.error(f"Error: {response.status_code}")
`

  // Voice WebSocket Examples
  const pythonVoiceExample = `import asyncio
import websockets
import json
import pyaudio

# Configuration
API_KEY = "your_api_key_here"
AGENT_ID = "${agentId}"
WS_ENDPOINT = "${apiEndpoint.replace('https://', 'wss://').replace('http://', 'ws://')}/voice"

# Audio configuration (16kHz PCM16 mono for input)
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
INPUT_RATE = 16000   # Input: 16kHz
OUTPUT_RATE = 24000  # Output: 24kHz

class VoiceClient:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.websocket = None
        self.is_running = False
        
    async def connect(self):
        """Connect to the voice agent"""
        actor_id = "user_voice_123"
        session_id = "voice_session_456"
        url = f"{WS_ENDPOINT}/{AGENT_ID}/{actor_id}/{session_id}?api_key={API_KEY}"
        
        self.websocket = await websockets.connect(url)
        print("Connected to voice agent!")
        
        # Wait for ready signal
        ready_msg = await self.websocket.recv()
        ready_data = json.loads(ready_msg)
        if ready_data.get("type") == "ready":
            print("Agent is ready!")
        
    async def send_audio(self):
        """Send audio from microphone"""
        stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=INPUT_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        
        # Signal start of audio input
        await self.websocket.send("start_audio")
        print("🎤 Recording... (Press Ctrl+C to stop)")
        
        try:
            while self.is_running:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                # Send raw PCM16 audio bytes
                await self.websocket.send(data)
                await asyncio.sleep(0.01)
        finally:
            stream.stop_stream()
            stream.close()
            await self.websocket.send("stop_audio")
            print("🛑 Recording stopped")
            
    async def receive_messages(self):
        """Receive audio and events from agent"""
        # Output stream for playing audio
        output_stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=OUTPUT_RATE,
            output=True
        )
        
        try:
            async for message in self.websocket:
                if isinstance(message, bytes):
                    # Audio data (24kHz PCM16) - play it
                    output_stream.write(message)
                else:
                    # JSON events
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type")
                        
                        if msg_type == "transcript":
                            role = data.get("role", "unknown")
                            content = data.get("content", "")
                            print(f"💬 {role}: {content}")
                        elif msg_type == "barge_in":
                            print("⚡ User interrupted")
                        elif msg_type == "tool_call":
                            tool = data.get("tool", "unknown")
                            print(f"🔧 Tool called: {tool}")
                        elif msg_type == "error":
                            print(f"❌ Error: {data.get('message')}")
                    except json.JSONDecodeError:
                        pass
        finally:
            output_stream.stop_stream()
            output_stream.close()
            
    async def run(self):
        """Run the voice client"""
        await self.connect()
        self.is_running = True
        
        try:
            # Run send and receive concurrently
            await asyncio.gather(
                self.send_audio(),
                self.receive_messages()
            )
        except KeyboardInterrupt:
            print("\\n👋 Shutting down...")
        finally:
            self.is_running = False
            if self.websocket:
                await self.websocket.close()
        
# Usage
if __name__ == "__main__":
    client = VoiceClient()
    asyncio.run(client.run())
`

  const streamlitVoiceExample = `import streamlit as st
import asyncio
import websockets
import json
import pyaudio
import threading
from queue import Queue

# Configuration
API_KEY = st.secrets["ORATIO_API_KEY"]
AGENT_ID = "${agentId}"
WS_ENDPOINT = "${apiEndpoint.replace('https://', 'wss://').replace('http://', 'ws://')}/voice"

# Audio configuration
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
INPUT_RATE = 16000
OUTPUT_RATE = 24000

# Initialize session state
if "voice_active" not in st.session_state:
    st.session_state.voice_active = False
if "transcripts" not in st.session_state:
    st.session_state.transcripts = []
if "session_id" not in st.session_state:
    st.session_state.session_id = "streamlit_voice_001"
if "transcripts_queue" not in st.session_state:
    st.session_state.transcripts_queue = Queue()

class StreamlitVoiceAgent:
    """Voice agent for Streamlit with real-time audio streaming"""
    
    def __init__(self, session_id, transcripts_queue):
        self.session_id = session_id
        self.transcripts_queue = transcripts_queue
        self.ws = None
        self.audio = pyaudio.PyAudio()
        self.is_running = False
        
    async def connect(self):
        """Connect to voice agent"""
        actor_id = "streamlit_user"
        url = f"{WS_ENDPOINT}/{AGENT_ID}/{actor_id}/{self.session_id}?api_key={API_KEY}"
        
        self.ws = await websockets.connect(url)
        
        # Wait for ready signal
        ready_msg = await self.ws.recv()
        ready_data = json.loads(ready_msg)
        if ready_data.get("type") == "ready":
            return True
        return False
    
    async def send_audio_loop(self):
        """Send audio from microphone"""
        stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=INPUT_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        
        await self.ws.send("start_audio")
        
        try:
            while self.is_running:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                await self.ws.send(data)
                await asyncio.sleep(0.01)
        finally:
            stream.stop_stream()
            stream.close()
            await self.ws.send("stop_audio")
    
    async def receive_loop(self):
        """Receive audio and transcripts"""
        output_stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=OUTPUT_RATE,
            output=True
        )
        
        try:
            async for message in self.ws:
                if not self.is_running:
                    break
                    
                if isinstance(message, bytes):
                    # Play audio
                    output_stream.write(message)
                else:
                    data = json.loads(message)
                    
                    if data.get("type") == "transcript":
                        role = data.get("role", "unknown")
                        content = data.get("content", "")
                        # Put transcript in queue instead of accessing session_state
                        self.transcripts_queue.put({
                            "role": role,
                            "content": content
                        })
        finally:
            output_stream.stop_stream()
            output_stream.close()
    
    async def run(self):
        """Run the voice agent"""
        connected = await self.connect()
        if not connected:
            return False
            
        self.is_running = True
        
        try:
            await asyncio.gather(
                self.send_audio_loop(),
                self.receive_loop()
            )
        finally:
            self.is_running = False
            if self.ws:
                await self.ws.close()
        
        return True

def run_voice_agent(session_id, transcripts_queue):
    """Run voice agent in background thread"""
    agent = StreamlitVoiceAgent(session_id, transcripts_queue)
    asyncio.run(agent.run())

# Streamlit UI
st.title("🎙️ ${agent.agent_name} - Voice Chat")
st.caption("Powered by Oratio Voice Agents")

# Control buttons
col1, col2 = st.columns([1, 4])

with col1:
    if st.button("🎤 Start" if not st.session_state.voice_active else "🛑 Stop", 
                 type="primary" if not st.session_state.voice_active else "secondary"):
        if not st.session_state.voice_active:
            st.session_state.voice_active = True
            st.session_state.transcripts = []
            st.session_state.transcripts_queue = Queue()
            # Start voice agent in background with session_id and queue
            thread = threading.Thread(
                target=run_voice_agent, 
                args=(st.session_state.session_id, st.session_state.transcripts_queue),
                daemon=True
            )
            thread.start()
            st.success("Voice agent started! Speak into your microphone.")
        else:
            st.session_state.voice_active = False
            st.info("Voice agent stopped.")

with col2:
    if st.session_state.voice_active:
        st.info("🎤 Listening... The agent is active and processing your voice.")

# Poll the queue for new transcripts (non-blocking)
while not st.session_state.transcripts_queue.empty():
    try:
        transcript = st.session_state.transcripts_queue.get_nowait()
        st.session_state.transcripts.append(transcript)
    except:
        break

# Auto-refresh when active to check for new transcripts
if st.session_state.voice_active:
    import time
    time.sleep(0.5)
    st.rerun()

# Display transcripts
st.subheader("Conversation")

if st.session_state.transcripts:
    for transcript in st.session_state.transcripts:
        role = transcript["role"]
        content = transcript["content"]
        
        if role == "user":
            with st.chat_message("user"):
                st.write(content)
        else:
            with st.chat_message("assistant"):
                st.write(content)
else:
    st.info("No conversation yet. Click 'Start' and speak into your microphone.")

# Instructions
with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. Click the **Start** button to begin the voice session
    2. Allow microphone access when prompted
    3. Speak naturally - the agent will respond with voice and text
    4. The conversation will appear below in real-time
    5. Click **Stop** when you're done
    
    **Note:** Make sure you have a working microphone connected to your device.
    """)
`

  const jsVoiceExample = `// Configuration
const API_KEY = "your_api_key_here";
const AGENT_ID = "${agentId}";
const WS_ENDPOINT = "${apiEndpoint.replace('https://', 'wss://').replace('http://', 'ws://')}/voice";

class VoiceAgent {
  constructor() {
    this.ws = null;
    this.audioContext = null;
    this.mediaStream = null;
    this.audioQueue = [];
    this.isPlaying = false;
    this.workletNode = null;
  }
  
  async connect() {
    const actorId = "user_voice_123";
    const sessionId = "voice_session_456";
    const url = \`\${WS_ENDPOINT}/\${AGENT_ID}/\${actorId}/\${sessionId}?api_key=\${API_KEY}\`;
    
    this.ws = new WebSocket(url);
    
    this.ws.onopen = () => {
      console.log("✅ Connected to voice agent!");
    };
    
    this.ws.onmessage = async (event) => {
      if (event.data instanceof Blob) {
        // Audio data (24kHz PCM16) - queue for playback
        const arrayBuffer = await event.data.arrayBuffer();
        this.audioQueue.push(arrayBuffer);
        this.playAudio();
      } else {
        // JSON event
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === "ready") {
            console.log("🎙️ Agent ready! Starting microphone...");
            await this.startRecording();
          } else if (data.type === "transcript") {
            console.log(\`💬 \${data.role}: \${data.content}\`);
          } else if (data.type === "barge_in") {
            console.log("⚡ User interrupted - clearing audio queue");
            this.audioQueue = []; // Clear audio queue on interruption
          } else if (data.type === "tool_call") {
            console.log(\`🔧 Tool called: \${data.tool}\`);
          } else if (data.type === "error") {
            console.error(\`❌ Error: \${data.message}\`);
          }
        } catch (e) {
          console.warn("Could not parse message:", e);
        }
      }
    };
    
    this.ws.onerror = (error) => {
      console.error("❌ WebSocket error:", error);
    };
    
    this.ws.onclose = () => {
      console.log("👋 Disconnected from voice agent");
      this.stopRecording();
    };
  }
  
  async startRecording() {
    try {
      // Request microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        } 
      });
      
      // Create audio context at 16kHz (required by backend)
      this.audioContext = new AudioContext({ sampleRate: 16000 });
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      
      // Use ScriptProcessor for audio capture
      const processor = this.audioContext.createScriptProcessor(4096, 1, 1);
      
      processor.onaudioprocess = (e) => {
        if (this.ws?.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0);
          const pcm16 = this.float32ToPCM16(inputData);
          this.ws.send(pcm16);
        }
      };
      
      source.connect(processor);
      processor.connect(this.audioContext.destination);
      
      // Signal audio start to backend
      this.ws.send("start_audio");
      console.log("🎤 Recording started");
    } catch (error) {
      console.error("❌ Failed to start recording:", error);
    }
  }
  
  stopRecording() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send("stop_audio");
    }
    console.log("🛑 Recording stopped");
  }
  
  async playAudio() {
    if (this.isPlaying || this.audioQueue.length === 0) return;
    
    this.isPlaying = true;
    
    // Create playback context at 24kHz (output sample rate)
    const playbackContext = new AudioContext({ sampleRate: 24000 });
    
    while (this.audioQueue.length > 0) {
      const pcm16Data = this.audioQueue.shift();
      
      // Convert PCM16 to AudioBuffer
      const audioBuffer = await this.pcm16ToAudioBuffer(pcm16Data, playbackContext);
      
      const source = playbackContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(playbackContext.destination);
      
      await new Promise(resolve => {
        source.onended = resolve;
        source.start();
      });
    }
    
    this.isPlaying = false;
  }
  
  async pcm16ToAudioBuffer(pcm16Data, audioContext) {
    // Convert Int16 PCM to Float32 for Web Audio API
    const int16Array = new Int16Array(pcm16Data);
    const float32Array = new Float32Array(int16Array.length);
    
    for (let i = 0; i < int16Array.length; i++) {
      float32Array[i] = int16Array[i] / 32768.0; // Convert to [-1, 1]
    }
    
    const audioBuffer = audioContext.createBuffer(1, float32Array.length, 24000);
    audioBuffer.getChannelData(0).set(float32Array);
    return audioBuffer;
  }
  
  float32ToPCM16(float32Array) {
    const pcm16 = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return pcm16.buffer;
  }
  
  disconnect() {
    console.log("🔌 Disconnecting...");
    this.stopRecording();
    if (this.ws) {
      this.ws.send(JSON.stringify({ type: "end" }));
      this.ws.close();
      this.ws = null;
    }
  }
}

// Usage
const voiceAgent = new VoiceAgent();
voiceAgent.connect();

// To disconnect later:
// voiceAgent.disconnect();
`

  const curlChatExample = `# Chat with the agent
curl -X POST "${apiEndpoint}/chat/${agentId}/user_123/session_456" \\
  -H "X-API-Key: your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "Hello, how can you help me?",
    "metadata": {}
  }'

# Response format:
# {
#   "result": "Agent's response text...",
#   "stop_reason": "end_turn",
#   "metrics": {
#     "tokens": 150,
#     "conversation_turns": 1
#   },
#   "metadata": {}
# }
`

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className="bg-neutral-900/50 border-neutral-800/50 overflow-hidden">
        <CollapsibleTrigger className="w-full">
          <div className="flex items-center justify-between p-6 hover:bg-neutral-800/30 transition-colors">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-accent/10 border border-accent/20">
                <IconCode className="h-5 w-5 text-accent" />
              </div>
              <div className="text-left">
                <h3 className="text-lg font-semibold text-white">How to Use This Agent</h3>
                <p className="text-sm text-neutral-400">
                  Integration examples for Python, JavaScript, and more
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge className="bg-neutral-800/50 text-neutral-300 border-neutral-700/50">
                API Documentation
              </Badge>
              {isOpen ? (
                <IconChevronUp className="h-5 w-5 text-neutral-400" />
              ) : (
                <IconChevronDown className="h-5 w-5 text-neutral-400" />
              )}
            </div>
          </div>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="border-t border-neutral-800/50 p-6 space-y-8">
            {/* Overview */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="h-1 w-1 rounded-full bg-accent" />
                <h4 className="text-sm font-semibold text-white uppercase tracking-wider">
                  Overview
                </h4>
              </div>
              <p className="text-neutral-300 leading-relaxed">
                This agent provides two integration methods: <span className="text-accent font-medium">REST API for text chat</span> and{" "}
                <span className="text-accent font-medium">WebSocket for voice interactions</span>. Both require API key authentication
                which you can generate from the API Keys page.
              </p>
            </div>

            {/* Authentication */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="h-1 w-1 rounded-full bg-accent" />
                <h4 className="text-sm font-semibold text-white uppercase tracking-wider">
                  Authentication
                </h4>
              </div>
              <div className="bg-neutral-950/50 border border-neutral-800/50 rounded-lg p-4">
                <p className="text-sm text-neutral-300 mb-3">
                  All API requests require authentication using an API key. Include your key in the request:
                </p>
                <ul className="space-y-2 text-sm text-neutral-400">
                  <li className="flex items-start gap-2">
                    <span className="text-accent mt-0.5">•</span>
                    <span><strong className="text-neutral-300">REST API:</strong> Use <code className="px-1.5 py-0.5 rounded bg-neutral-900 text-accent text-xs">X-API-Key</code> header</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-accent mt-0.5">•</span>
                    <span><strong className="text-neutral-300">WebSocket:</strong> Pass as query parameter <code className="px-1.5 py-0.5 rounded bg-neutral-900 text-accent text-xs">?api_key=your_key</code></span>
                  </li>
                </ul>
              </div>
            </div>

            {/* Chat API Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <IconMessageCircle className="h-5 w-5 text-accent" />
                <h4 className="text-lg font-semibold text-white">Text Chat API</h4>
              </div>
              
              <div className="bg-neutral-950/50 border border-neutral-800/50 rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-neutral-300">Endpoint</span>
                  <Badge className="bg-green-500/10 text-green-400 border-green-500/20">POST</Badge>
                </div>
                <code className="block text-sm text-accent break-all">
                  {apiEndpoint}/chat/{`{agent_id}`}/{`{actor_id}`}/{`{session_id}`}
                </code>
              </div>

              <Tabs defaultValue="python" className="w-full">
                <TabsList className="grid w-full grid-cols-4 bg-neutral-900/50 border border-neutral-800/50">
                  <TabsTrigger value="python" className="flex items-center gap-2">
                    <LanguageIcon language="python" />
                    <span>Python</span>
                  </TabsTrigger>
                  <TabsTrigger value="javascript" className="flex items-center gap-2">
                    <LanguageIcon language="javascript" />
                    <span>JavaScript</span>
                  </TabsTrigger>
                  <TabsTrigger value="streamlit" className="flex items-center gap-2">
                    <LanguageIcon language="python" />
                    <span>Streamlit</span>
                  </TabsTrigger>
                  <TabsTrigger value="curl" className="flex items-center gap-2">
                    <LanguageIcon language="bash" />
                    <span>cURL</span>
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="python" className="mt-4">
                  <CodeBlock
                    code={pythonChatExample}
                    language="python"
                    title="chat_example.py"
                  />
                </TabsContent>

                <TabsContent value="javascript" className="mt-4">
                  <CodeBlock
                    code={jsChatExample}
                    language="javascript"
                    title="chat_example.js"
                  />
                </TabsContent>

                <TabsContent value="streamlit" className="mt-4">
                  <CodeBlock
                    code={streamlitChatExample}
                    language="python"
                    title="streamlit_app.py"
                  />
                </TabsContent>

                <TabsContent value="curl" className="mt-4">
                  <CodeBlock
                    code={curlChatExample}
                    language="bash"
                    title="curl_example.sh"
                  />
                </TabsContent>
              </Tabs>
            </div>

            {/* Voice API Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <IconMicrophone className="h-5 w-5 text-accent" />
                <h4 className="text-lg font-semibold text-white">Voice WebSocket API</h4>
              </div>
              
              <div className="bg-neutral-950/50 border border-neutral-800/50 rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-neutral-300">Endpoint</span>
                  <Badge className="bg-blue-500/10 text-blue-400 border-blue-500/20">WebSocket</Badge>
                </div>
                <code className="block text-sm text-accent break-all">
                  {apiEndpoint.replace('https://', 'wss://').replace('http://', 'ws://')}/voice/{`{agent_id}`}/{`{actor_id}`}/{`{session_id}`}?api_key={`{your_api_key}`}
                </code>
              </div>

              <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
                <p className="text-sm text-yellow-200">
                  <strong>Audio Requirements:</strong> Input audio must be 16kHz PCM16, mono channel. Output will be 24kHz PCM16.
                </p>
              </div>

              <Tabs defaultValue="python" className="w-full">
                <TabsList className="grid w-full grid-cols-3 bg-neutral-900/50 border border-neutral-800/50">
                  <TabsTrigger value="python" className="flex items-center gap-2">
                    <LanguageIcon language="python" />
                    <span>Python</span>
                  </TabsTrigger>
                  <TabsTrigger value="javascript" className="flex items-center gap-2">
                    <LanguageIcon language="javascript" />
                    <span>JavaScript</span>
                  </TabsTrigger>
                  <TabsTrigger value="streamlit" className="flex items-center gap-2">
                    <LanguageIcon language="python" />
                    <span>Streamlit</span>
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="python" className="mt-4 space-y-3">
                  <CodeBlock
                    code={pythonVoiceExample}
                    language="python"
                    title="voice_client.py"
                  />
                  <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
                    <p className="text-xs text-blue-200">
                      <strong>Dependencies:</strong> <code className="px-1.5 py-0.5 rounded bg-neutral-900 text-accent ml-1">pip install websockets pyaudio</code>
                    </p>
                  </div>
                </TabsContent>

                <TabsContent value="javascript" className="mt-4">
                  <CodeBlock
                    code={jsVoiceExample}
                    language="javascript"
                    title="voice_agent.js"
                  />
                </TabsContent>

                <TabsContent value="streamlit" className="mt-4 space-y-3">
                  <CodeBlock
                    code={streamlitVoiceExample}
                    language="python"
                    title="streamlit_voice_app.py"
                  />
                  <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
                    <p className="text-xs text-blue-200">
                      <strong>Dependencies:</strong> <code className="px-1.5 py-0.5 rounded bg-neutral-900 text-accent ml-1">pip install streamlit websockets pyaudio</code>
                    </p>
                  </div>
                  <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3">
                    <p className="text-xs text-yellow-200">
                      <strong>Note:</strong> Streamlit's threading model may have limitations with real-time audio. For production use, consider using the standalone Python example or JavaScript for web applications.
                    </p>
                  </div>
                </TabsContent>
              </Tabs>
            </div>

            {/* Parameters Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="h-1 w-1 rounded-full bg-accent" />
                <h4 className="text-sm font-semibold text-white uppercase tracking-wider">
                  Path Parameters
                </h4>
              </div>
              
              <div className="grid gap-3">
                <div className="bg-neutral-950/50 border border-neutral-800/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <code className="text-accent text-sm">{`{agent_id}`}</code>
                    <Badge className="text-xs bg-neutral-800/50 text-neutral-300 border-neutral-700/50">Required</Badge>
                  </div>
                  <p className="text-sm text-neutral-400">
                    Your agent's unique identifier: <code className="px-1.5 py-0.5 rounded bg-neutral-900 text-accent text-xs">{agentId}</code>
                  </p>
                </div>

                <div className="bg-neutral-950/50 border border-neutral-800/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <code className="text-accent text-sm">{`{actor_id}`}</code>
                    <Badge className="text-xs bg-neutral-800/50 text-neutral-300 border-neutral-700/50">Required</Badge>
                  </div>
                  <p className="text-sm text-neutral-400">
                    Unique identifier for the user/actor. Used for conversation isolation and tracking.
                  </p>
                </div>

                <div className="bg-neutral-950/50 border border-neutral-800/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <code className="text-accent text-sm">{`{session_id}`}</code>
                    <Badge className="text-xs bg-neutral-800/50 text-neutral-300 border-neutral-700/50">Required</Badge>
                  </div>
                  <p className="text-sm text-neutral-400">
                    Unique identifier for the conversation session. The same session_id maintains conversation context.
                  </p>
                </div>
              </div>
            </div>

            {/* Additional Resources */}
            <div className="space-y-3 pt-4 border-t border-neutral-800/50">
              <div className="flex items-center gap-2">
                <div className="h-1 w-1 rounded-full bg-accent" />
                <h4 className="text-sm font-semibold text-white uppercase tracking-wider">
                  Additional Resources
                </h4>
              </div>
              <ul className="space-y-2 text-sm text-neutral-400">
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-0.5">•</span>
                  <span>Generate API keys from the <a href="/dashboard/api-keys" className="text-accent hover:underline">API Keys</a> page</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-0.5">•</span>
                  <span>Each session maintains independent conversation history</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-0.5">•</span>
                  <span>Voice connections support real-time bidirectional audio streaming</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-0.5">•</span>
                  <span>Rate limits apply based on your subscription tier</span>
                </li>
              </ul>
            </div>
          </div>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  )
}

