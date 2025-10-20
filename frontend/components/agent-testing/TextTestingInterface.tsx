"use client"

import { useEffect, useState, useRef } from "react"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { IconSend, IconRobot, IconUser } from "@tabler/icons-react"
import type { Agent } from "@/lib/api/agents"
import { sendMessage, type ChatMessage } from "@/lib/api/chat"

interface TextTestingInterfaceProps {
  agent: Agent
  agentId: string
  actorId: string
  sessionId: string
}

export default function TextTestingInterface({
  agent,
  agentId,
  actorId,
  sessionId,
}: TextTestingInterfaceProps) {
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const [isSending, setIsSending] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

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

  return (
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
        className="h-[400px] overflow-y-auto bg-neutral-950 border border-neutral-800 rounded-lg p-4 mb-4 space-y-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
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
  )
}
