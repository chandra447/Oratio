"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Phone, PhoneOff, Volume2, Loader2 } from "lucide-react"
import { connectVoiceAgent, sendAudioChunk, endVoiceSession, type VoiceMessage as VoiceAPIMessage } from "@/lib/api/voice"
import { MicSparklesIcon } from "@/components/ui/mic-sparkles-icon"

interface VoiceMessage {
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

interface ToolCall {
  tool: string
  input: Record<string, any>
  result?: string
  timestamp: Date
}

interface VoiceTestProps {
  agentId: string
  apiKey: string
}

export function VoiceTest({ agentId, apiKey }: VoiceTestProps) {
  const [isVoiceActive, setIsVoiceActive] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [voiceTranscripts, setVoiceTranscripts] = useState<VoiceMessage[]>([])
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([])
  const [voiceTime, setVoiceTime] = useState(0)
  const [voiceError, setVoiceError] = useState<string | null>(null)
  const [isBargeIn, setIsBargeIn] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const audioStreamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const playbackAudioContextRef = useRef<AudioContext | null>(null)
  const audioQueueRef = useRef<ArrayBuffer[]>([])
  const isPlayingRef = useRef(false)
  const nextPlayTimeRef = useRef(0)
  const activeSourcesRef = useRef<AudioBufferSourceNode[]>([])
  const timerRef = useRef<NodeJS.Timeout | null>(null)

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
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [])

  const playAudioChunk = async (arrayBuffer: ArrayBuffer) => {
    try {
      if (!playbackAudioContextRef.current) {
        playbackAudioContextRef.current = new AudioContext({ sampleRate: 24000 })
        nextPlayTimeRef.current = 0
        console.log("[Voice] 🔊 Created playback AudioContext (24kHz)")
      }

      if (playbackAudioContextRef.current.state === 'suspended') {
        console.log("[Voice] ▶️ Resuming suspended AudioContext")
        await playbackAudioContextRef.current.resume()
      }

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
      const audioBuffer = playbackAudioContextRef.current.createBuffer(
        1,
        arrayBuffer.byteLength / 2,
        24000
      )

      const channelData = audioBuffer.getChannelData(0)
      const view = new DataView(arrayBuffer)

      for (let i = 0; i < channelData.length; i++) {
        const sample = view.getInt16(i * 2, true)
        channelData[i] = sample / 32768.0
      }

      const source = playbackAudioContextRef.current.createBufferSource()
      source.buffer = audioBuffer
      source.connect(playbackAudioContextRef.current.destination)

      activeSourcesRef.current.push(source)

      source.onended = () => {
        const index = activeSourcesRef.current.indexOf(source)
        if (index > -1) {
          activeSourcesRef.current.splice(index, 1)
        }
        if (!isPlayingRef.current && audioQueueRef.current.length > 0) {
          isPlayingRef.current = true
          playNextAudioChunk()
        }
      }

      const currentTime = playbackAudioContextRef.current.currentTime
      if (nextPlayTimeRef.current < currentTime) {
        nextPlayTimeRef.current = currentTime + 0.01
      }

      source.start(nextPlayTimeRef.current)
      nextPlayTimeRef.current += audioBuffer.duration

      console.log(`[Voice] 🎵 Playing audio chunk: ${audioBuffer.duration.toFixed(3)}s, next at ${nextPlayTimeRef.current.toFixed(3)}s`)

      if (audioQueueRef.current.length > 0) {
        playNextAudioChunk()
      } else {
        isPlayingRef.current = false
      }
    } catch (err) {
      console.error("[Voice] ❌ Error playing audio chunk:", err)
      isPlayingRef.current = false
      if (audioQueueRef.current.length > 0) {
        playNextAudioChunk()
      }
    }
  }

  const startVoiceSession = async () => {
    if (!agentId) return

    try {
      console.log("[Voice] Starting voice session...")
      setVoiceError(null)
      setVoiceTranscripts([])
      setToolCalls([])
      setVoiceTime(0)

      // Generate session details
      const actorId = "test-user"
      const sessionId = `voice-session-${Date.now()}`
      const testMode = !apiKey || apiKey.trim() === ""

      const ws = connectVoiceAgent(agentId, actorId, sessionId, testMode)
      wsRef.current = ws

      ws.onopen = () => {
        console.log("[Voice] ✅ WebSocket connected")
      }

      ws.onmessage = async (event) => {
        if (event.data instanceof Blob || event.data instanceof ArrayBuffer) {
          console.log("[Voice] 🔊 Received binary audio")
          const arrayBuffer = event.data instanceof Blob ? await event.data.arrayBuffer() : event.data

          if (!isBargeIn) {
            await playAudioChunk(arrayBuffer)
          } else {
            console.log("[Voice] Skipping audio chunk due to barge-in")
          }
          return
        }

        console.log("[Voice] 📥 Received message:", event.data.substring(0, 100))

        try {
          const message: VoiceAPIMessage = JSON.parse(event.data)
          console.log("[Voice] 📥 Received message:", message.type, message)

          switch (message.type) {
            case "ready":
              console.log("[Voice] ✅ Agent ready, starting recording...")
              setIsBargeIn(false)
              setIsVoiceActive(true)
              await startRecording()
              timerRef.current = setInterval(() => {
                setVoiceTime((prev) => prev + 1)
              }, 1000)
              break

            case "transcript":
              console.log("[Voice] 💬 Transcript (" + message.role + "):", message.content)
              setVoiceTranscripts((prev) => [
                ...prev,
                {
                  role: message.role!,
                  content: message.content!,
                  timestamp: new Date(),
                },
              ])
              break

            case "tool_call":
              console.log("[Voice] 🔧 Tool call:", message.tool, message.input)
              setToolCalls((prev) => [
                ...prev,
                {
                  tool: message.tool!,
                  input: message.input!,
                  timestamp: new Date(),
                },
              ])
              break

            case "tool_result":
              console.log("[Voice] ✅ Tool result:", message.result)
              setToolCalls((prev) => {
                const updated = [...prev]
                const lastTool = updated[updated.length - 1]
                if (lastTool && !lastTool.result) {
                  lastTool.result = message.result
                }
                return updated
              })
              break

            case "barge_in":
              console.log("[Voice] 🛑 Barge-in detected! Stopping all audio")
              setIsBargeIn(true)

              activeSourcesRef.current.forEach(source => {
                try {
                  source.stop()
                  source.disconnect()
                } catch (e) {
                  // Source might already be stopped
                }
              })
              activeSourcesRef.current = []

              audioQueueRef.current = []
              isPlayingRef.current = false

              if (playbackAudioContextRef.current) {
                nextPlayTimeRef.current = playbackAudioContextRef.current.currentTime
              }

              console.log("[Voice] ✅ Audio cleared, ready for new input")

              setTimeout(() => {
                setIsBargeIn(false)
                console.log("[Voice] Barge-in flag reset, ready for new audio")
              }, 100)
              break

            case "error":
              console.error("[Voice] ❌ Error:", message.message)
              setVoiceError(message.message || "Unknown error")
              break
          }
        } catch (err) {
          console.error("[Voice] ❌ Error parsing message:", err)
        }
      }

      ws.onerror = (error) => {
        console.error("[Voice] ❌ WebSocket error:", error)
        setVoiceError("Connection error")
      }

      ws.onclose = () => {
        console.log("[Voice] WebSocket closed")
        stopVoiceSession()
      }
    } catch (error) {
      console.error("[Voice] ❌ Error starting voice session:", error)
      setVoiceError("Failed to start voice session")
    }
  }

  const startRecording = async () => {
    try {
      console.log("[Voice] 🎤 Requesting microphone access...")
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })

      console.log("[Voice] ✅ Microphone access granted")
      audioStreamRef.current = stream

      audioContextRef.current = new AudioContext({ sampleRate: 16000 })
      const source = audioContextRef.current.createMediaStreamSource(stream)
      const processor = audioContextRef.current.createScriptProcessor(4096, 1, 1)

      let chunkCount = 0
      processor.onaudioprocess = (e) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

        const inputData = e.inputBuffer.getChannelData(0)
        const pcmData = new Int16Array(inputData.length)

        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]))
          pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7fff
        }

        sendAudioChunk(wsRef.current, pcmData.buffer)
        chunkCount++

        if (chunkCount % 20 === 0) {
          console.log(`[Voice] 🎤 Sent ${chunkCount} audio chunks (4096 bytes each)`)
        }
      }

      source.connect(processor)
      processor.connect(audioContextRef.current.destination)

      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ command: "start_audio" }))
        console.log("[Voice] 📤 Sent start_audio command")
      }

      setIsRecording(true)
      console.log("[Voice] ✅ Recording started")
    } catch (error) {
      console.error("[Voice] ❌ Error accessing microphone:", error)
      setVoiceError("Microphone access denied")
    }
  }

  const stopVoiceSession = () => {
    if (wsRef.current) {
      endVoiceSession(wsRef.current)
      wsRef.current.close()
      wsRef.current = null
    }

    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach((track) => track.stop())
      audioStreamRef.current = null
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    if (playbackAudioContextRef.current && playbackAudioContextRef.current.state !== 'closed') {
      playbackAudioContextRef.current.close()
      playbackAudioContextRef.current = null
    }

    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }

    audioQueueRef.current = []
    isPlayingRef.current = false
    setIsVoiceActive(false)
    setIsRecording(false)
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  return (
    <div className="space-y-6">
      {/* Voice Controls */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h3 className="font-semibold">Voice Session</h3>
            <p className="text-sm text-muted-foreground">
              {isVoiceActive ? `Active • ${formatTime(voiceTime)}` : "Not connected"}
            </p>
          </div>
          <div className="flex gap-2">
            {!isVoiceActive ? (
              <Button onClick={startVoiceSession} size="lg" className="gap-2">
                <Phone className="w-4 h-4" />
                Start Voice Chat
              </Button>
            ) : (
              <Button onClick={stopVoiceSession} size="lg" variant="destructive" className="gap-2">
                <PhoneOff className="w-4 h-4" />
                End Call
              </Button>
            )}
          </div>
        </div>

        {voiceError && (
          <div className="mt-4 p-3 bg-destructive/10 text-destructive rounded-lg text-sm">
            {voiceError}
          </div>
        )}

        {isVoiceActive && (
          <div className="mt-4 flex gap-4">
            <Badge variant={isRecording ? "default" : "secondary"} className="gap-1">
              <MicSparklesIcon size={12} />
              {isRecording ? "Recording" : "Paused"}
            </Badge>
            <Badge variant={isPlayingRef.current ? "default" : "secondary"} className="gap-1">
              <Volume2 className="w-3 h-3" />
              {isPlayingRef.current ? "Playing" : "Silent"}
            </Badge>
          </div>
        )}
      </Card>

      {/* Transcripts */}
      <Card className="p-6">
        <h3 className="font-semibold mb-4">Conversation</h3>
        <div className="space-y-3 max-h-[300px] overflow-y-auto">
          {voiceTranscripts.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No conversation yet. Start a voice session to begin.
            </p>
          ) : (
            voiceTranscripts.map((transcript, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg ${
                  transcript.role === "user" ? "bg-primary/10 ml-8" : "bg-muted mr-8"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant={transcript.role === "user" ? "default" : "secondary"} className="text-xs">
                    {transcript.role === "user" ? "You" : "Agent"}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {transcript.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-sm">{transcript.content}</p>
              </div>
            ))
          )}
        </div>
      </Card>

      {/* Tool Calls */}
      {toolCalls.length > 0 && (
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Tool Invocations</h3>
          <div className="space-y-3">
            {toolCalls.map((call, index) => (
              <div key={index} className="p-3 bg-muted rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="outline">{call.tool}</Badge>
                  <span className="text-xs text-muted-foreground">
                    {call.timestamp.toLocaleTimeString()}
                  </span>
                  {!call.result && <Loader2 className="w-3 h-3 animate-spin" />}
                </div>
                <div className="text-xs space-y-1">
                  <div>
                    <span className="font-medium">Input:</span>
                    <pre className="mt-1 p-2 bg-background rounded text-xs overflow-x-auto">
                      {JSON.stringify(call.input, null, 2)}
                    </pre>
                  </div>
                  {call.result && (
                    <div>
                      <span className="font-medium">Result:</span>
                      <pre className="mt-1 p-2 bg-background rounded text-xs overflow-x-auto">
                        {call.result}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

