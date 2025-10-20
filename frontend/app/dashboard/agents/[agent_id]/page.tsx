"use client"

import { useEffect, useState, useRef } from "react"
import { useParams, useRouter } from "next/navigation"
import DashboardLayout from "@/components/dashboard-layout"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import AITextLoading from "@/components/kokonutui/ai-text-loading"
import { cn } from "@/lib/utils"
import { IconArrowLeft, IconSend, IconRobot, IconUser, IconSparkles, IconPhone, IconPhoneOff, IconMicrophone } from "@tabler/icons-react"
import type { Agent } from "@/lib/api/agents"
import { getAgent } from "@/lib/api/agents"
import { sendMessage, type ChatMessage } from "@/lib/api/chat"
import { 
  connectVoiceAgent, 
  sendAudioChunk, 
  endVoiceSession, 
  audioBufferToBase64,
  base64ToAudioBuffer,
  type VoiceMessage,
  type VoiceTranscript,
  type VoiceToolCall
} from "@/lib/api/voice"

export default function AgentDetailPage() {
  const params = useParams()
  const router = useRouter()
  const agentId = params.agent_id as string

  // Agent data
  const [agent, setAgent] = useState<Agent | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const [isSending, setIsSending] = useState(false)
  const [actorId] = useState(`test-user-${Date.now()}`)
  const [sessionId] = useState(`test-session-${Date.now()}`)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const voiceTranscriptsEndRef = useRef<HTMLDivElement>(null)
  const voiceTranscriptsContainerRef = useRef<HTMLDivElement>(null)

  // Voice state
  const [isVoiceActive, setIsVoiceActive] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [voiceTranscripts, setVoiceTranscripts] = useState<VoiceTranscript[]>([])
  const [voiceToolCalls, setVoiceToolCalls] = useState<VoiceToolCall[]>([])
  const [voiceTime, setVoiceTime] = useState(0)
  const [voiceError, setVoiceError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null) // For recording (16kHz)
  const playbackAudioContextRef = useRef<AudioContext | null>(null) // For playback (24kHz)
  const audioQueueRef = useRef<ArrayBuffer[]>([])
  const isPlayingRef = useRef(false)
  const nextPlayTimeRef = useRef(0)
  const activeSourcesRef = useRef<AudioBufferSourceNode[]>([])
  const voiceTimerRef = useRef<NodeJS.Timeout | null>(null)
  const audioStreamRef = useRef<MediaStream | null>(null)

  // Load agent data
  useEffect(() => {
    async function loadAgent() {
      try {
        setLoading(true)
        const agentData = await getAgent(agentId)
        setAgent(agentData)
      } catch (err: any) {
        console.error("Error loading agent:", err)
        setError(err.message || "Failed to load agent")
      } finally {
        setLoading(false)
      }
    }

    loadAgent()
  }, [agentId])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Auto-scroll voice transcripts (scroll within container, not the page)
  useEffect(() => {
    if (voiceTranscriptsContainerRef.current) {
      voiceTranscriptsContainerRef.current.scrollTop = voiceTranscriptsContainerRef.current.scrollHeight
    }
  }, [voiceTranscripts])

  // Voice timer
  useEffect(() => {
    if (isVoiceActive) {
      voiceTimerRef.current = setInterval(() => {
        setVoiceTime((t) => t + 1)
      }, 1000)
    } else {
      if (voiceTimerRef.current) {
        clearInterval(voiceTimerRef.current)
      }
      setVoiceTime(0)
    }

    return () => {
      if (voiceTimerRef.current) {
        clearInterval(voiceTimerRef.current)
      }
    }
  }, [isVoiceActive])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        endVoiceSession(wsRef.current)
        wsRef.current.close()
      }
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach((track) => track.stop())
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close()
      }
      if (playbackAudioContextRef.current && playbackAudioContextRef.current.state !== 'closed') {
        playbackAudioContextRef.current.close()
      }
    }
  }, [])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !agent || isSending) return

    const userMessage: ChatMessage = {
      role: "user",
      content: inputMessage,
      timestamp: Date.now(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputMessage("")
    setIsSending(true)

    try {
      const response = await sendMessage(
        agentId,
        actorId,
        sessionId,
        inputMessage,
        true // test mode
      )

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.result,
        timestamp: Date.now(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err: any) {
      console.error("Error sending message:", err)
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: `Error: ${err.message || "Failed to send message"}`,
        timestamp: Date.now(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsSending(false)
    }
  }

  // Voice functions
  const formatVoiceTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  const playAudioChunk = async (arrayBuffer: ArrayBuffer) => {
    try {
      // Initialize playback audio context (separate from recording)
      if (!playbackAudioContextRef.current) {
        playbackAudioContextRef.current = new AudioContext({ sampleRate: 24000 })
        nextPlayTimeRef.current = 0
        console.log("[Voice] 🔊 Created playback AudioContext (24kHz)")
      }
      
      // Resume if suspended (browser autoplay policy)
      if (playbackAudioContextRef.current.state === 'suspended') {
        console.log("[Voice] ▶️ Resuming suspended AudioContext")
        await playbackAudioContextRef.current.resume()
      }

      // Add raw ArrayBuffer to queue (don't convert yet)
      audioQueueRef.current.push(arrayBuffer)
      
      if (!isPlayingRef.current) {
        isPlayingRef.current = true
        playNextAudioChunk()
      }
    } catch (err) {
      console.error("[Voice] ❌ Error queueing audio:", err)
    }
  }

  const playNextAudioChunk = async () => {
    if (!playbackAudioContextRef.current) {
      isPlayingRef.current = false
      return
    }
    
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false
      return
    }

    const arrayBuffer = audioQueueRef.current.shift()!
    
    try {
      // Convert raw PCM16 (24kHz, mono) to AudioBuffer
      // Nova Sonic sends 16-bit PCM at 24kHz sample rate
      const audioBuffer = playbackAudioContextRef.current.createBuffer(
        1, // mono
        arrayBuffer.byteLength / 2, // 16-bit samples (2 bytes per sample)
        24000 // sample rate (Nova Sonic outputs 24kHz)
      )
      
      const channelData = audioBuffer.getChannelData(0)
      const view = new DataView(arrayBuffer)
      
      // Convert 16-bit PCM to Float32 (-1.0 to 1.0)
      // PCM16 range: -32768 to 32767
      for (let i = 0; i < channelData.length; i++) {
        const sample = view.getInt16(i * 2, true) // little-endian
        channelData[i] = sample / 32768.0 // Normalize to -1.0 to 1.0
      }
      
      // Create source and schedule playback
      const source = playbackAudioContextRef.current.createBufferSource()
      source.buffer = audioBuffer
      source.connect(playbackAudioContextRef.current.destination)
      
      // Track active source for interruption
      activeSourcesRef.current.push(source)
      
      // Remove from active sources when done
      source.onended = () => {
        const index = activeSourcesRef.current.indexOf(source)
        if (index > -1) {
          activeSourcesRef.current.splice(index, 1)
        }
        // Process next chunk when this one finishes (if not using scheduled playback)
        if (!isPlayingRef.current && audioQueueRef.current.length > 0) {
          isPlayingRef.current = true
          playNextAudioChunk()
        }
      }
      
      // Schedule playback for smooth continuous audio
      const currentTime = playbackAudioContextRef.current.currentTime
      if (nextPlayTimeRef.current < currentTime) {
        nextPlayTimeRef.current = currentTime + 0.01 // Small buffer to prevent clicks
      }
      
      source.start(nextPlayTimeRef.current)
      nextPlayTimeRef.current += audioBuffer.duration
      
      console.log(`[Voice] 🎵 Playing audio chunk: ${audioBuffer.duration.toFixed(3)}s, next at ${nextPlayTimeRef.current.toFixed(3)}s`)
      
      // Process next chunk immediately for scheduled playback
      if (audioQueueRef.current.length > 0) {
        playNextAudioChunk()
      } else {
        isPlayingRef.current = false
      }
      
    } catch (err) {
      console.error("[Voice] ❌ Error playing audio chunk:", err)
      isPlayingRef.current = false
      // Try next chunk on error
      if (audioQueueRef.current.length > 0) {
        playNextAudioChunk()
      }
    }
  }

  const startVoiceSession = async () => {
    if (!agent) return

    try {
      console.log("[Voice] Starting voice session...")
      setVoiceError(null)
      setVoiceTranscripts([])
      setVoiceToolCalls([])
      
      // Connect WebSocket
      const ws = connectVoiceAgent(agentId, actorId, `voice-${Date.now()}`, true)
      wsRef.current = ws

      ws.onopen = () => {
        console.log("[Voice] ✅ WebSocket connected")
      }

      ws.onmessage = async (event) => {
        // Handle binary audio data (PCM from Nova Sonic)
        if (event.data instanceof ArrayBuffer || event.data instanceof Blob) {
          console.log("[Voice] 🔊 Received binary audio")
          const arrayBuffer = event.data instanceof Blob ? await event.data.arrayBuffer() : event.data
          await playAudioChunk(arrayBuffer)
          return
        }
        
        // Handle JSON messages
        try {
          const message: VoiceMessage = JSON.parse(event.data)
          console.log("[Voice] 📥 Received message:", message.type, message)
          
          switch (message.type) {
            case "ready":
              console.log("[Voice] ✅ Agent ready, starting recording...")
              setIsVoiceActive(true)
              await startRecording()
              break
            
            case "transcript":
              console.log(`[Voice] 💬 Transcript (${message.role}):`, message.content)
              setVoiceTranscripts((prev) => [
                ...prev,
                {
                  role: message.role as "user" | "assistant",
                  content: message.content || "",
                  timestamp: Date.now(),
                },
              ])
              break
            
            case "tool_call":
              console.log("[Voice] 🔧 Tool call:", message.tool, message.input)
              setVoiceToolCalls((prev) => [
                ...prev,
                {
                  tool: message.tool || "",
                  input: message.input || {},
                  timestamp: Date.now(),
                },
              ])
              break
            
            case "tool_result":
              console.log("[Voice] ✅ Tool result:", message.result)
              setVoiceToolCalls((prev) =>
                prev.map((call, idx) =>
                  idx === prev.length - 1 && call.tool === message.tool
                    ? { ...call, result: message.result }
                    : call
                )
              )
              break
            
            case "barge_in":
              console.log("[Voice] 🛑 Barge-in detected! Stopping all audio")
              // Stop all currently playing audio sources
              activeSourcesRef.current.forEach(source => {
                try {
                  source.stop()
                  source.disconnect()
                } catch (e) {
                  // Source might already be stopped
                }
              })
              activeSourcesRef.current = []
              
              // Clear frontend audio queue
              audioQueueRef.current = []
              isPlayingRef.current = false
              
              // Reset next play time to current time (don't close context - keep it ready)
              if (playbackAudioContextRef.current) {
                nextPlayTimeRef.current = playbackAudioContextRef.current.currentTime
              }
              
              console.log("[Voice] ✅ Audio cleared, ready for new input")
              // The microphone is still active, user can continue speaking
              break
            
            case "error":
              console.error("[Voice] ❌ Error:", message.message)
              setVoiceError(message.message || "Unknown error")
              stopVoiceSession()
              break
            
            default:
              // Don't log raw Nova Sonic events to avoid duplicates
              // Transcripts are already handled by the backend's "transcript" type
              console.debug("[Voice] Unhandled message type:", message.type)
          }
        } catch (err) {
          console.error("[Voice] Error parsing message:", err)
        }
      }

      ws.onerror = (error) => {
        console.error("[Voice] ❌ WebSocket error:", error)
        setVoiceError("Connection error")
        stopVoiceSession()
      }

      ws.onclose = () => {
        console.log("[Voice] WebSocket closed")
        setIsVoiceActive(false)
        setIsRecording(false)
      }
    } catch (err: any) {
      console.error("[Voice] ❌ Error starting session:", err)
      setVoiceError(err.message || "Failed to start voice session")
    }
  }

  const startRecording = async () => {
    try {
      console.log("[Voice] 🎤 Requesting microphone access...")
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        } 
      })
      
      audioStreamRef.current = stream
      console.log("[Voice] ✅ Microphone access granted")
      
      // Create AudioContext for processing (matching AWS sample web version)
      // Use 16kHz for input (Nova Sonic expects 16kHz PCM)
      const audioContext = new AudioContext({ sampleRate: 16000 })
      audioContextRef.current = audioContext
      
      const source = audioContext.createMediaStreamSource(stream)
      // Use 2048 buffer size for better quality (AWS sample uses this for web)
      const processor = audioContext.createScriptProcessor(2048, 1, 1)
      
      let chunkCount = 0
      processor.onaudioprocess = (e) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
        
        const inputData = e.inputBuffer.getChannelData(0)
        
        // Convert Float32Array to Int16Array (PCM 16-bit, little-endian)
        // This matches pyaudio.paInt16 format
        const pcmData = new Int16Array(inputData.length)
        for (let i = 0; i < inputData.length; i++) {
          // Clamp to [-1, 1] range
          const s = Math.max(-1, Math.min(1, inputData[i]))
          // Convert to 16-bit signed integer
          pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
        }
        
        // Send as binary (raw PCM data, little-endian Int16)
        sendAudioChunk(wsRef.current, pcmData.buffer)
        
        chunkCount++
        if (chunkCount % 20 === 0) {
          console.log(`[Voice] 🎤 Sent ${chunkCount} audio chunks (${pcmData.length * 2} bytes each)`)
        }
      }
      
      source.connect(processor)
      processor.connect(audioContext.destination)
      
      setIsRecording(true)
      
      // Send start_audio command to backend
      if (wsRef.current) {
        wsRef.current.send("start_audio")
        console.log("[Voice] 📤 Sent start_audio command")
      }
      
      console.log("[Voice] ✅ Recording started")
    } catch (err: any) {
      console.error("[Voice] ❌ Error starting recording:", err)
      setVoiceError("Microphone access denied")
      stopVoiceSession()
    }
  }

  const stopVoiceSession = () => {
    if (wsRef.current) {
      endVoiceSession(wsRef.current)
      wsRef.current.close()
      wsRef.current = null
    }

    // Stop microphone stream
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach((track) => track.stop())
      audioStreamRef.current = null
    }

    // Close recording audio context
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    // Close playback audio context
    if (playbackAudioContextRef.current && playbackAudioContextRef.current.state !== 'closed') {
      playbackAudioContextRef.current.close()
      playbackAudioContextRef.current = null
    }

    audioQueueRef.current = []
    isPlayingRef.current = false
    setIsVoiceActive(false)
    setIsRecording(false)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-500/10 text-green-500 border-green-500/20"
      case "creating":
        return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
      case "failed":
        return "bg-red-500/10 text-red-500 border-red-500/20"
      case "paused":
        return "bg-gray-500/10 text-gray-500 border-gray-500/20"
      default:
        return "bg-neutral-500/10 text-neutral-500 border-neutral-500/20"
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <AITextLoading
            texts={["Loading agent...", "Fetching details...", "Almost there..."]}
            interval={1200}
          />
        </div>
      </DashboardLayout>
    )
  }

  if (error || !agent) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-full gap-4">
          <p className="text-red-400">{error || "Agent not found"}</p>
          <Button onClick={() => router.push("/dashboard/agents")} variant="outline">
            Back to Agents
          </Button>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="border-b border-neutral-800 bg-neutral-900/50 backdrop-blur-sm">
          <div className="p-6 md:p-8">
            <Button
              variant="ghost"
              onClick={() => router.push("/dashboard/agents")}
              className="mb-4 text-neutral-400 hover:text-white"
            >
              <IconArrowLeft className="h-4 w-4 mr-2" />
              Back to Agents
            </Button>
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white">{agent.agent_name}</h1>
                <p className="text-neutral-400 mt-1">
                  {agent.agent_type === "voice" ? "Voice Agent" : "Text Agent"}
                </p>
              </div>
              <Badge className={cn("border", getStatusColor(agent.status))}>
                {agent.status.toUpperCase()}
              </Badge>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6 md:p-8">
          <div className="max-w-7xl mx-auto">
            {/* Bento Grid Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              {/* Agent Info */}
              <Card className="bg-neutral-900 border-neutral-800 p-6 lg:col-span-1">
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <IconSparkles className="h-5 w-5 text-accent" />
                  Agent Info
                </h2>
                <div className="space-y-3 text-sm">
                  <div>
                    <p className="text-neutral-500">Agent ID</p>
                    <p className="text-white font-mono text-xs">{agent.agent_id}</p>
                  </div>
                  <Separator className="bg-neutral-800" />
                  <div>
                    <p className="text-neutral-500">Created</p>
                    <p className="text-white">
                      {new Date(agent.created_at * 1000).toLocaleDateString()}
                    </p>
                  </div>
                  <Separator className="bg-neutral-800" />
                  <div>
                    <p className="text-neutral-500">Knowledge Base</p>
                    <p className="text-white">{agent.knowledge_base_id}</p>
                  </div>
                  {agent.memory_id && (
                    <>
                      <Separator className="bg-neutral-800" />
                      <div>
                        <p className="text-neutral-500">Memory ID</p>
                        <p className="text-white font-mono text-xs">{agent.memory_id}</p>
                      </div>
                    </>
                  )}
                </div>
              </Card>

              {/* SOP & Descriptions */}
              <Card className="bg-neutral-900 border-neutral-800 p-6 lg:col-span-2">
                <h2 className="text-lg font-semibold text-white mb-4">Configuration</h2>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-neutral-500 mb-2">Standard Operating Procedure</p>
                    <p className="text-sm text-white bg-neutral-950 border border-neutral-800 rounded-lg p-3">
                      {agent.sop}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-neutral-500 mb-2">Knowledge Base Description</p>
                    <p className="text-sm text-white bg-neutral-950 border border-neutral-800 rounded-lg p-3">
                      {agent.knowledge_base_description}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-neutral-500 mb-2">Human Handoff</p>
                    <p className="text-sm text-white bg-neutral-950 border border-neutral-800 rounded-lg p-3">
                      {agent.human_handoff_description}
                    </p>
                  </div>
                </div>
              </Card>

              {/* Voice Personality (if applicable) */}
              {agent.agent_type === "voice" && agent.voice_personality && (
                <Card className="bg-neutral-900 border-neutral-800 p-6 lg:col-span-3">
                  <h2 className="text-lg font-semibold text-white mb-4">Voice Personality</h2>
                  <div className="text-sm text-white bg-neutral-950 border border-neutral-800 rounded-lg p-4">
                    {agent.voice_personality.additional_instructions || "No personality instructions provided"}
                  </div>
                </Card>
              )}
            </div>

            {/* Voice Testing Interface - Show for voice agents */}
            {agent.status === "active" && (agent.agent_type === "voice" || agent.voice_prompt) && (
              <Card className="bg-neutral-900 border-neutral-800 p-6 mb-6">
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <IconPhone className="h-5 w-5 text-accent" />
                  Voice Agent Testing (Nova Sonic)
                </h2>
                <p className="text-sm text-neutral-400 mb-4">
                  Test your voice agent with real-time bidirectional audio streaming powered by Nova Sonic.
                </p>

                {voiceError && (
                  <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                    {voiceError}
                  </div>
                )}

                {/* Voice Interface - Side by Side Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Left: Voice Visualizer */}
                  <div className="lg:col-span-1">
                    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-8 h-full flex flex-col items-center justify-center min-h-[500px]">
                      <button
                        onClick={isVoiceActive ? stopVoiceSession : startVoiceSession}
                        disabled={isVoiceActive && !isRecording}
                        className={cn(
                          "group w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 mb-6",
                          isVoiceActive
                            ? "bg-red-500 hover:bg-red-600 shadow-2xl shadow-red-500/50"
                            : "bg-accent hover:bg-accent/90 shadow-2xl shadow-accent/50"
                        )}
                      >
                        {isVoiceActive ? (
                          <IconPhoneOff className="h-10 w-10 text-white" />
                        ) : (
                          <IconPhone className="h-10 w-10 text-white" />
                        )}
                      </button>

                      <span className="font-mono text-2xl text-white/90 mb-8">
                        {formatVoiceTime(voiceTime)}
                      </span>

                      {/* Voice Visualization Bars */}
                      <div className="h-32 w-full flex items-center justify-center gap-1 mb-6">
                        {[...Array(48)].map((_, i) => (
                          <div
                            key={i}
                            className={cn(
                              "w-1 rounded-full transition-all duration-300",
                              isRecording
                                ? "bg-accent animate-pulse"
                                : "bg-neutral-700 h-2"
                            )}
                            style={
                              isRecording
                                ? {
                                    height: `${20 + Math.random() * 80}%`,
                                    animationDelay: `${i * 0.05}s`,
                                  }
                                : undefined
                            }
                          />
                        ))}
                      </div>

                      <p className="text-sm text-neutral-400 text-center">
                        {isVoiceActive
                          ? isRecording
                            ? "🎤 Listening..."
                            : "Connecting..."
                          : "Click to start voice session"}
                      </p>
                    </div>
                  </div>

                  {/* Right: Conversation & Tool Calls */}
                  <div className="lg:col-span-2 space-y-6">
                    {/* Conversation Transcript */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                        <IconMicrophone className="h-5 w-5 text-accent" />
                        Conversation Transcript
                      </h3>
                      <div 
                        ref={voiceTranscriptsContainerRef}
                        className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 h-64 overflow-y-auto space-y-3"
                      >
                        {voiceTranscripts.length === 0 ? (
                          <p className="text-sm text-neutral-500 text-center py-16">
                            No conversation yet
                          </p>
                        ) : (
                          voiceTranscripts.map((transcript, idx) => (
                            <div
                              key={idx}
                              className={cn(
                                "flex gap-3",
                                transcript.role === "user" ? "justify-end" : "justify-start"
                              )}
                            >
                              {transcript.role === "assistant" && (
                                <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0">
                                  <IconRobot className="h-4 w-4 text-accent" />
                                </div>
                              )}
                              <div
                                className={cn(
                                  "max-w-[80%] p-3 rounded-lg",
                                  transcript.role === "user"
                                    ? "bg-accent/20 text-accent border border-accent/30"
                                    : "bg-neutral-800 text-white border border-neutral-700"
                                )}
                              >
                                <p className="text-sm">{transcript.content}</p>
                              </div>
                              {transcript.role === "user" && (
                                <div className="w-8 h-8 rounded-full bg-neutral-700 flex items-center justify-center flex-shrink-0">
                                  <IconUser className="h-4 w-4 text-white" />
                                </div>
                              )}
                            </div>
                          ))
                        )}
                      </div>
                    </div>

                    {/* Tool Invocations */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                        <IconSparkles className="h-5 w-5 text-accent" />
                        Tool Invocations
                      </h3>
                      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 h-48 overflow-y-auto space-y-3">
                        {voiceToolCalls.length === 0 ? (
                          <p className="text-sm text-neutral-500 text-center py-12">
                            No tool calls yet
                          </p>
                        ) : (
                          voiceToolCalls.map((call, idx) => (
                            <div
                              key={idx}
                              className="bg-neutral-800 border border-neutral-700 rounded-lg p-4"
                            >
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-semibold text-accent flex items-center gap-2">
                                  <IconSparkles className="h-4 w-4" />
                                  {call.tool}
                                </span>
                                {call.result ? (
                                  <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
                                    ✓ Complete
                                  </Badge>
                                ) : (
                                  <Badge className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">
                                    ⏳ Running
                                  </Badge>
                                )}
                              </div>
                              <div className="text-sm text-neutral-400 mb-2">
                                <span className="opacity-70">Input:</span>{" "}
                                <code className="text-xs bg-neutral-900 px-2 py-1 rounded">
                                  {JSON.stringify(call.input).slice(0, 100)}...
                                </code>
                              </div>
                              {call.result && (
                                <div className="text-sm text-neutral-300">
                                  <span className="opacity-70">Result:</span>{" "}
                                  <span className="text-green-400">{call.result}</span>
                                </div>
                              )}
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            )}

            {/* Chat Testing Interface - Always show for active agents */}
            {agent.status === "active" && (
              <Card className="bg-neutral-900 border-neutral-800 p-6">
                <h2 className="text-lg font-semibold text-white mb-4">
                  {agent.agent_type === "voice" ? "Text Testing (Fallback)" : "Test Agent"}
                </h2>
                <p className="text-sm text-neutral-400 mb-4">
                  Send messages to test your agent. This is a test session and won't affect production data.
                </p>

                {/* Messages */}
                <div
                  ref={scrollAreaRef}
                  className="h-[400px] overflow-y-auto bg-neutral-950 border border-neutral-800 rounded-lg p-4 mb-4 space-y-4"
                >
                  {messages.length === 0 && (
                    <div className="flex items-center justify-center h-full text-neutral-500 text-sm">
                      Start a conversation with your agent
                    </div>
                  )}
                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={cn(
                        "flex gap-3",
                        message.role === "user" ? "justify-end" : "justify-start"
                      )}
                    >
                      {message.role === "assistant" && (
                        <div className="flex-shrink-0 h-8 w-8 rounded-full bg-accent/20 flex items-center justify-center">
                          <IconRobot className="h-5 w-5 text-accent" />
                        </div>
                      )}
                      <div
                        className={cn(
                          "max-w-[70%] rounded-lg p-3 text-sm",
                          message.role === "user"
                            ? "bg-accent text-white"
                            : "bg-neutral-800 text-white"
                        )}
                      >
                        {message.content}
                      </div>
                      {message.role === "user" && (
                        <div className="flex-shrink-0 h-8 w-8 rounded-full bg-neutral-700 flex items-center justify-center">
                          <IconUser className="h-5 w-5 text-white" />
                        </div>
                      )}
                    </div>
                  ))}
                  {isSending && (
                    <div className="flex gap-3 justify-start">
                      <div className="flex-shrink-0 h-8 w-8 rounded-full bg-accent/20 flex items-center justify-center">
                        <IconRobot className="h-5 w-5 text-accent" />
                      </div>
                      <div className="bg-neutral-800 rounded-lg p-3">
                        <div className="flex gap-1">
                          <div className="h-2 w-2 bg-neutral-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                          <div className="h-2 w-2 bg-neutral-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                          <div className="h-2 w-2 bg-neutral-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="flex gap-2">
                  <Input
                    placeholder="Type your message..."
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault()
                        handleSendMessage()
                      }
                    }}
                    disabled={isSending}
                    className="bg-neutral-950 border-neutral-800 text-white"
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isSending}
                    className="bg-accent hover:bg-accent/90 text-white"
                  >
                    <IconSend className="h-4 w-4" />
                  </Button>
                </div>

                {/* Test Mode Indicator */}
                <div className="mt-4 text-xs text-neutral-500 flex items-center gap-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                  Testing Mode - Session: {sessionId.slice(0, 20)}...
                </div>
              </Card>
            )}

            {agent.status !== "active" && (
              <Card className="bg-neutral-900 border-neutral-800 p-6">
                <div className="text-center py-8">
                  <p className="text-neutral-400 mb-2">
                    Agent is not active yet. Current status: <span className="font-semibold">{agent.status}</span>
                  </p>
                  <p className="text-sm text-neutral-500">
                    Please wait for the agent to be deployed before testing.
                  </p>
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}

