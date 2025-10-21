/**
 * Knowledge Base API client for Oratio platform.
 * Handles knowledge base listing, retrieval, and management.
 */

import { getAccessToken } from '../auth/token-storage'
import { getApiBaseUrl } from './config'

export interface KnowledgeBase {
  knowledgeBaseId: string
  userId: string
  s3Path: string
  bedrockKnowledgeBaseId?: string
  status: 'notready' | 'ready' | 'error'
  folderFileDescriptions: Record<string, string>
  createdAt: number
  updatedAt: number
}

export interface ApiError {
  detail: string
}

/**
 * List all knowledge bases for the current user
 */
export async function listKnowledgeBases(): Promise<KnowledgeBase[]> {
  const token = getAccessToken()

  if (!token) {
    throw new Error('No access token found')
  }

  const response = await fetch(`${getApiBaseUrl()}/api/v1/knowledge-bases`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error: ApiError = await response.json()
    throw new Error(error.detail || 'Failed to fetch knowledge bases')
  }

  return response.json()
}

/**
 * Get a specific knowledge base by ID
 */
export async function getKnowledgeBase(knowledgeBaseId: string): Promise<KnowledgeBase> {
  const token = getAccessToken()

  if (!token) {
    throw new Error('No access token found')
  }

  const response = await fetch(`${getApiBaseUrl()}/api/v1/knowledge-bases/${knowledgeBaseId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error: ApiError = await response.json()
    throw new Error(error.detail || 'Failed to fetch knowledge base')
  }

  return response.json()
}

/**
 * Upload files to create a new knowledge base
 */
export async function uploadFiles(files: File[]): Promise<KnowledgeBase> {
  const token = getAccessToken()

  if (!token) {
    throw new Error('No access token found')
  }

  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })

  const response = await fetch(`${getApiBaseUrl()}/api/v1/knowledge-bases/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  })

  if (!response.ok) {
    const error: ApiError = await response.json()
    throw new Error(error.detail || 'Failed to upload files')
  }

  return response.json()
}

/**
 * Delete a knowledge base
 */
export async function deleteKnowledgeBase(knowledgeBaseId: string): Promise<void> {
  const token = getAccessToken()

  if (!token) {
    throw new Error('No access token found')
  }

  const response = await fetch(`${getApiBaseUrl()}/api/v1/knowledge-bases/${knowledgeBaseId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    const error: ApiError = await response.json()
    throw new Error(error.detail || 'Failed to delete knowledge base')
  }
}

/**
 * Get file count from folderFileDescriptions
 */
export function getFileCount(kb: KnowledgeBase): number {
  return Object.keys(kb.folderFileDescriptions || {}).length
}

/**
 * Format timestamp to relative time
 */
export function formatRelativeTime(timestamp: number): string {
  const now = Date.now() / 1000
  const diff = now - timestamp

  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`
  if (diff < 2592000) return `${Math.floor(diff / 604800)}w ago`

  return new Date(timestamp * 1000).toLocaleDateString()
}

/**
 * Get status badge color
 */
export function getStatusColor(status: KnowledgeBase['status']): string {
  switch (status) {
    case 'ready':
      return 'bg-green-500/10 text-green-400 border-green-500/20'
    case 'notready':
      return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
    case 'error':
      return 'bg-red-500/10 text-red-400 border-red-500/20'
    default:
      return 'bg-neutral-500/10 text-neutral-400 border-neutral-500/20'
  }
}

