/**
 * Agents API client.
 * Example of using the authenticated API client.
 */

import { get, post, patch, del } from './client';

export interface Agent {
  user_id: string;
  agent_id: string;
  agent_name: string;
  agent_type: string;
  status: string;
  created_at: number;
  updated_at: number;
}

/**
 * Get all agents for the current user
 */
export async function getAgents(): Promise<Agent[]> {
  return get<Agent[]>('/api/agents');
}

/**
 * Get a specific agent by ID
 */
export async function getAgent(agentId: string): Promise<Agent> {
  return get<Agent>(`/api/agents/${agentId}`);
}

/**
 * Create a new agent
 */
export async function createAgent(data: {
  agent_name: string;
  agent_type: string;
  sop: string;
}): Promise<Agent> {
  return post<Agent>('/api/agents/create', data);
}

/**
 * Update an agent
 */
export async function updateAgent(
  agentId: string,
  data: Partial<Agent>
): Promise<Agent> {
  return patch<Agent>(`/api/agents/${agentId}`, data);
}

/**
 * Delete an agent
 */
export async function deleteAgent(agentId: string): Promise<{ message: string }> {
  return del<{ message: string }>(`/api/agents/${agentId}`);
}
