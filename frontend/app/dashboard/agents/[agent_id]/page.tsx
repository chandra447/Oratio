"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import DashboardLayout from "@/components/dashboard-layout"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import AITextLoading from "@/components/kokonutui/ai-text-loading"
import { cn } from "@/lib/utils"
import { IconArrowLeft } from "@tabler/icons-react"
import type { Agent } from "@/lib/api/agents"
import { getAgent } from "@/lib/api/agents"
import { getApiBaseUrl } from "@/lib/api/config"
import {
  AgentDetailsCard,
  VoiceTestingInterface,
  TextTestingInterface,
  ApiDocumentation,
} from "@/components/agent-testing"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"

export default function AgentDetailPage() {
  const params = useParams()
  const router = useRouter()
  const agentId = params.agent_id as string

  // Agent data
  const [agent, setAgent] = useState<Agent | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actorId] = useState(`test-user-${Date.now()}`)
  const [sessionId] = useState(`test-session-${Date.now()}`)

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
      <div className="flex flex-col h-full overflow-hidden">
        {/* Header - stays the same */}
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

        {/* Content - Fixed overflow strategy */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden p-6 md:p-8 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          <div className="max-w-7xl mx-auto">
            {/* Agent Details - Single Collapsible Container */}
            <div className="mb-6">
              <AgentDetailsCard agent={agent} defaultOpen={true} />
            </div>

            {/* Testing Interface - Tabbed */}
            {agent.status === "active" ? (
              <Tabs defaultValue="voice" className="w-full">
                <TabsList className="grid w-full grid-cols-2 mb-6">
                  <TabsTrigger value="voice">
                    Voice Testing
                  </TabsTrigger>
                  <TabsTrigger value="text">
                    Text Testing
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="voice" className="mt-0">
                  <VoiceTestingInterface
                    agent={agent}
                    agentId={agentId}
                    actorId={actorId}
                    sessionId={sessionId}
                  />
                </TabsContent>

                <TabsContent value="text" className="mt-0">
                  <TextTestingInterface
                    agent={agent}
                    agentId={agentId}
                    actorId={actorId}
                    sessionId={sessionId}
                  />
                </TabsContent>
              </Tabs>
            ) : (
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

            {/* API Documentation Section */}
            <div className="mt-6">
              <ApiDocumentation
                agent={agent}
                apiEndpoint={getApiBaseUrl() + "/api/v1"}
              />
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
