'use client';

import { IconSettings } from '@tabler/icons-react';
import type { Agent } from '@/lib/api/agents';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

interface AgentConfigCardProps {
  agent: Agent;
}

export function AgentConfigCard({ agent }: AgentConfigCardProps) {
  return (
    <Card className="bg-neutral-900 border-neutral-800">
      <div className="px-6 py-4">
        <div className="flex items-center gap-2 mb-4">
          <IconSettings className="h-5 w-5 text-accent" />
          <h2 className="text-lg font-semibold text-white">Agent Configuration</h2>
        </div>

        <Separator className="bg-neutral-800" />
        <div className="px-0 py-4 space-y-4">
          {/* Standard Operating Procedure */}
          <div>
            <p className="text-sm text-neutral-500 mb-2">Standard Operating Procedure</p>
            <div className="text-sm text-white bg-neutral-950 border border-neutral-800 rounded-lg p-3 whitespace-pre-wrap break-words">
              {agent.sop}
            </div>
          </div>

          <Separator className="bg-neutral-800" />

          {/* Knowledge Base Description */}
          <div>
            <p className="text-sm text-neutral-500 mb-2">Knowledge Base Description</p>
            <div className="text-sm text-white bg-neutral-950 border border-neutral-800 rounded-lg p-3 whitespace-pre-wrap break-words">
              {agent.knowledge_base_description}
            </div>
          </div>

          <Separator className="bg-neutral-800" />

          {/* Human Handoff Description */}
          <div>
            <p className="text-sm text-neutral-500 mb-2">Human Handoff Description</p>
            <div className="text-sm text-white bg-neutral-950 border border-neutral-800 rounded-lg p-3 whitespace-pre-wrap break-words">
              {agent.human_handoff_description}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
