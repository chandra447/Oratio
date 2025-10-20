import { z } from 'zod';

// Agent Type enum
export const AgentTypeSchema = z.enum(['voice', 'text', 'both']);

// Agent Status enum
export const AgentStatusSchema = z.enum(['creating', 'active', 'failed', 'paused']);

// Voice Personality schema
export const VoicePersonalitySchema = z.object({
  identity: z.string().optional(),
  task: z.string().optional(),
  demeanor: z.string().optional(),
  tone: z.string().optional(),
  formality_level: z.string().optional(),
  enthusiasm_level: z.string().optional(),
  filler_words: z.string().optional(),
  pacing: z.string().optional(),
  additional_instructions: z.string().optional(),
});

// Create Agent schema
export const CreateAgentSchema = z.object({
  agent_name: z.string().min(3, 'Agent name must be at least 3 characters').max(100, 'Agent name must be less than 100 characters'),
  agent_type: AgentTypeSchema,
  sop: z.string().min(10, 'SOP must be at least 10 characters'),
  knowledge_base_description: z.string().min(10, 'Knowledge base description must be at least 10 characters'),
  human_handoff_description: z.string().min(10, 'Human handoff description must be at least 10 characters'),
  voice_personality: VoicePersonalitySchema.optional(),
  voice_config: z.record(z.any()).optional(),
  text_config: z.record(z.any()).optional(),
  files: z.array(z.instanceof(File)).min(1, 'At least one file is required'),
  file_descriptions: z.record(z.string()).optional(),
});

export type CreateAgentFormData = z.infer<typeof CreateAgentSchema>;

