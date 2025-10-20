/**
 * API Keys API client
 */

import { get, post, del } from './client';

export type APIKeyStatus = 'active' | 'revoked' | 'expired';
export type APIKeyPermission = 'chat' | 'voice' | 'admin';

export interface APIKey {
  api_key_hash: string;
  user_id: string;
  agent_id: string;
  key_name: string;
  permissions: APIKeyPermission[];
  status: APIKeyStatus;
  rate_limit?: number;
  created_at: number;
  expires_at?: number;
  last_used_at?: number;
}

export interface APIKeyResponse extends APIKey {
  api_key: string; // Only returned on creation
}

export interface CreateAPIKeyData {
  agent_id: string;
  key_name: string;
  permissions: APIKeyPermission[];
  rate_limit?: number;
  expires_in_days?: number;
}

/**
 * Create a new API key
 */
export async function createAPIKey(data: CreateAPIKeyData): Promise<APIKeyResponse> {
  return post<APIKeyResponse>('/api/v1/api-keys', data);
}

/**
 * List all API keys for the current user
 */
export async function listAPIKeys(agentId?: string): Promise<APIKey[]> {
  const params = agentId ? `?agent_id=${agentId}` : '';
  return get<APIKey[]>(`/api/v1/api-keys${params}`);
}

/**
 * Revoke an API key
 */
export async function revokeAPIKey(keyHash: string): Promise<void> {
  return del<void>(`/api/v1/api-keys/${keyHash}`);
}

