/**
 * Agents API client.
 * Example of using the authenticated API client.
 */

import { get, patch, del, uploadFiles } from './client';

// Type definitions matching backend models
export type AgentStatus = 'creating' | 'active' | 'failed' | 'paused';
export type AgentType = 'voice' | 'text' | 'both';

export interface VoicePersonality {
  identity?: string;
  task?: string;
  demeanor?: string;
  tone?: string;
  formality_level?: string;
  enthusiasm_level?: string;
  filler_words?: string;
  pacing?: string;
  additional_instructions?: string;
}

export interface KnowledgeBase {
  knowledge_base_id: string;
  user_id: string;
  s3_path: string;
  folder_file_descriptions: string;
  created_at: number;
  updated_at: number;
}

export interface Agent {
  agent_id: string;
  user_id: string;
  agent_name: string;
  agent_type: AgentType;
  sop: string;
  knowledge_base_id: string;
  knowledge_base_description: string;
  human_handoff_description: string;
  voice_personality?: VoicePersonality;
  voice_config?: Record<string, any>;
  text_config?: Record<string, any>;
  bedrock_knowledge_base_arn?: string;
  agentcore_runtime_arn?: string;
  generated_prompt?: string;
  voice_prompt?: string;
  agent_code_s3_path?: string;
  memory_id?: string;
  status: AgentStatus;
  created_at: number;
  updated_at: number;
  knowledge_base?: KnowledgeBase;
}

export interface CreateAgentData {
  agent_name: string;
  agent_type: AgentType;
  sop: string;
  knowledge_base_description: string;
  human_handoff_description: string;
  voice_personality?: VoicePersonality;
  voice_config?: Record<string, any>;
  text_config?: Record<string, any>;
  files: File[];
  file_descriptions?: Record<string, string>;
}

/**
 * Get all agents for the current user
 */
export async function getAgents(): Promise<Agent[]> {
  return get<Agent[]>('/api/v1/agents');
}

/**
 * Alias for getAgents (for consistency)
 */
export const listAgents = getAgents;

/**
 * Get a specific agent by ID
 */
export async function getAgent(agentId: string): Promise<Agent> {
  return get<Agent>(`/api/v1/agents/${agentId}`);
}

/**
 * Create a new agent with files
 */
export async function createAgent(data: CreateAgentData): Promise<Agent> {
  const formData = new FormData();
  
  // Add text fields
  formData.append('agent_name', data.agent_name);
  formData.append('agent_type', data.agent_type);
  formData.append('sop', data.sop);
  formData.append('knowledge_base_description', data.knowledge_base_description);
  formData.append('human_handoff_description', data.human_handoff_description);
  
  // Add optional JSON fields
  if (data.voice_personality) {
    formData.append('voice_personality', JSON.stringify(data.voice_personality));
  }
  if (data.voice_config) {
    formData.append('voice_config', JSON.stringify(data.voice_config));
  }
  if (data.text_config) {
    formData.append('text_config', JSON.stringify(data.text_config));
  }
  if (data.file_descriptions) {
    formData.append('file_descriptions', JSON.stringify(data.file_descriptions));
  }
  
  // Add files
  data.files.forEach(file => {
    formData.append('files', file);
  });
  
  return uploadFiles<Agent>('/api/v1/agents', formData);
}

/**
 * Update an agent
 */
export async function updateAgent(
  agentId: string,
  data: Partial<Agent>
): Promise<Agent> {
  return patch<Agent>(`/api/v1/agents/${agentId}`, data);
}

/**
 * Delete an agent
 */
export async function deleteAgent(agentId: string): Promise<{ message: string }> {
  return del<{ message: string }>(`/api/v1/agents/${agentId}`);
}
