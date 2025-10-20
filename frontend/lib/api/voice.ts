/**
 * Voice API client for Nova Sonic voice agents
 */

import { getAccessToken } from '../auth/token-storage';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface VoiceTranscript {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface VoiceToolCall {
  tool: string;
  input: Record<string, any>;
  result?: string;
  timestamp: number;
}

export interface VoiceMessage {
  type: 'ready' | 'audio' | 'transcript' | 'tool_call' | 'tool_result' | 'barge_in' | 'error';
  role?: 'user' | 'assistant';
  content?: string;
  data?: string; // base64 audio
  tool?: string;
  input?: Record<string, any>;
  result?: string;
  message?: string;
}

/**
 * Create WebSocket connection for voice agent
 */
export function connectVoiceAgent(
  agentId: string,
  actorId: string,
  sessionId: string,
  testMode: boolean = false
): WebSocket {
  const accessToken = getAccessToken();
  
  // WebSocket URL (ws:// for http, wss:// for https)
  const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
  const wsBaseUrl = API_BASE_URL.replace(/^https?:\/\//, '');
  
  // Build URL with test mode or API key
  let url = `${wsProtocol}://${wsBaseUrl}/api/v1/voice/${agentId}/${actorId}/${sessionId}`;
  
  if (testMode) {
    url += '?test=true';
  } else if (accessToken) {
    url += `?api_key=${accessToken}`;
  }
  
  return new WebSocket(url);
}

/**
 * Send audio chunk to voice agent (as binary)
 */
export function sendAudioChunk(ws: WebSocket, audioData: ArrayBuffer) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(audioData);
  }
}

/**
 * End voice session
 */
export function endVoiceSession(ws: WebSocket) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'end'
    }));
  }
}

/**
 * Convert audio buffer to base64
 */
export function audioBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Convert base64 to audio buffer
 */
export function base64ToAudioBuffer(base64: string): ArrayBuffer {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

