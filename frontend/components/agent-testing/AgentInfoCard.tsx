'use client';

import { IconSparkles } from '@tabler/icons-react';
import type { Agent } from '@/lib/api/agents';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

interface AgentInfoCardProps {
  agent: Agent;
}

export function AgentInfoCard({ agent }: AgentInfoCardProps) {
  const createdDate = new Date(agent.created_at * 1000).toLocaleDateString();

  return (
    <Card className="bg-neutral-900 border-neutral-800">
      <div className="px-6 py-4">
        <div className="flex items-center gap-2 mb-4">
          <IconSparkles className="h-5 w-5 text-accent" />
          <h2 className="text-lg font-semibold text-white">Agent Information</h2>
        </div>

        <Separator className="bg-neutral-800 mb-4" />

        <div className="space-y-4">
          {/* Agent ID */}
          <div>
            <p className="text-neutral-500 text-sm mb-1">Agent ID</p>
            <p className="font-mono text-xs text-white break-all">
              {agent.agent_id}
            </p>
          </div>

          <Separator className="bg-neutral-800" />

          {/* Created Date */}
          <div>
            <p className="text-neutral-500 text-sm mb-1">Created Date</p>
            <p className="text-white">{createdDate}</p>
          </div>

          <Separator className="bg-neutral-800" />

          {/* Knowledge Base ID */}
          <div>
            <p className="text-neutral-500 text-sm mb-1">Knowledge Base ID</p>
            <p className="font-mono text-xs text-white break-all">
              {agent.knowledge_base_id}
            </p>
          </div>

          {/* Memory ID - only show if it exists */}
          {agent.memory_id && (
            <>
              <Separator className="bg-neutral-800" />
              <div>
                <p className="text-neutral-500 text-sm mb-1">Memory ID</p>
                <p className="font-mono text-xs text-white break-all">
                  {agent.memory_id}
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </Card>
  );
}
