"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { IconChevronDown, IconInfoCircle } from "@tabler/icons-react"
import { cn } from "@/lib/utils"
import type { Agent } from "@/lib/api/agents"
import { AgentInfoCard } from "./AgentInfoCard"
import { AgentConfigCard } from "./AgentConfigCard"
import { VoicePersonalityCard } from "./VoicePersonalityCard"

interface AgentDetailsCardProps {
  agent: Agent
  defaultOpen?: boolean
}

export function AgentDetailsCard({ agent, defaultOpen = true }: AgentDetailsCardProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} defaultOpen={defaultOpen}>
      <Card className="bg-neutral-900 border-neutral-800 overflow-hidden">
        <CollapsibleTrigger className="w-full px-6 py-4 flex items-center justify-between hover:bg-neutral-800/50 transition-colors">
          <div className="flex items-center gap-2">
            <IconInfoCircle className="h-5 w-5 text-accent" />
            <h2 className="text-lg font-semibold text-white">Agent Details</h2>
          </div>
          <IconChevronDown
            className={cn(
              "h-5 w-5 text-neutral-400 transition-transform duration-200",
              isOpen && "transform rotate-180"
            )}
          />
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="p-6 space-y-6">
            {/* Grid for Info + Config */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1">
                <AgentInfoCard agent={agent} />
              </div>
              <div className="lg:col-span-2">
                <AgentConfigCard agent={agent} />
              </div>
            </div>

            {/* Voice Personality (conditional) */}
            {agent.agent_type === "voice" && agent.voice_personality && (
              <VoicePersonalityCard agent={agent} />
            )}
          </div>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  )
}
