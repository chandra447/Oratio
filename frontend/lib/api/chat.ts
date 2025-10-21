/**
 * Chat API client for conversational agents
 */

import { getAccessToken } from '../auth/token-storage';
import { getApiBaseUrl } from './config';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface ChatRequest {
  message: string;
  metadata?: Record<string, any>;
}

export interface ChatResponse {
  result: string;
  stop_reason: string;
  metrics?: Record<string, any>;
  metadata?: Record<string, any>;
}

/**
 * Send a message to an agent
 */
export async function sendMessage(
  agentId: string,
  actorId: string,
  sessionId: string,
  message: string,
  testMode: boolean = false
): Promise<ChatResponse> {
  const accessToken = getAccessToken();
  
  if (!accessToken && !testMode) {
    throw new Error('No authentication token found');
  }

  const url = `${getApiBaseUrl()}/api/v1/chat/${agentId}/${actorId}/${sessionId}${testMode ? '?test=true' : ''}`;
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (testMode && accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  } else if (!testMode) {
    // In production mode, use X-API-Key header
    // For now, we'll use the access token
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `Request failed with status ${response.status}`
    }));
    throw new Error(error.detail || 'Failed to send message');
  }

  return response.json();
}

