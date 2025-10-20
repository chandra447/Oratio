'use client';

import { IconMicrophone } from '@tabler/icons-react';
import type { Agent } from '@/lib/api/agents';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

interface VoicePersonalityCardProps {
  agent: Agent;
}

export function VoicePersonalityCard({
  agent,
}: VoicePersonalityCardProps) {
  const instructions =
    agent.voice_personality?.additional_instructions ||
    'No personality instructions provided';

  return (
    <Card className="bg-neutral-900 border-neutral-800">
      <div className="flex items-center gap-2 mb-4 px-6 pt-6">
        <IconMicrophone className="h-5 w-5 text-accent" />
        <h2 className="text-lg font-semibold text-white">Voice Personality</h2>
      </div>

      <Separator className="bg-neutral-800" />
      <div className="p-6">
        <h4 className="text-lg font-semibold text-white mb-4">
          Personality Instructions
        </h4>
        <div className="text-sm text-white bg-neutral-950 border border-neutral-800 rounded-lg p-4 whitespace-pre-wrap break-words">
          {instructions}
        </div>
      </div>
    </Card>
  );
}
