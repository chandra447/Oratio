"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import DashboardLayout from "@/components/dashboard-layout"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import {
  IconKey,
  IconPlus,
  IconTrash,
  IconCopy,
  IconCheck,
  IconAlertCircle,
} from "@tabler/icons-react"
import {
  type APIKey,
  type APIKeyResponse,
  type CreateAPIKeyData,
  type APIKeyPermission,
  createAPIKey,
  listAPIKeys,
  revokeAPIKey,
} from "@/lib/api/api-keys"
import { getAgents, type Agent } from "@/lib/api/agents"

export default function APIKeysPage() {
  const router = useRouter()
  const [apiKeys, setApiKeys] = useState<APIKey[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newKey, setNewKey] = useState<APIKeyResponse | null>(null)
  const [copiedKey, setCopiedKey] = useState(false)

  // Form state
  const [keyName, setKeyName] = useState("")
  const [selectedAgent, setSelectedAgent] = useState("")
  const [permissions, setPermissions] = useState<APIKeyPermission[]>(["chat"])
  const [expiresInDays, setExpiresInDays] = useState<number | undefined>(undefined)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [keysData, agentsData] = await Promise.all([
        listAPIKeys(),
        getAgents(),
      ])
      setApiKeys(keysData)
      setAgents(agentsData)
    } catch (err: any) {
      console.error("Error loading data:", err)
      setError(err.message || "Failed to load data")
    } finally {
      setLoading(false)
    }
  }

  const handleCreateKey = async () => {
    if (!keyName.trim() || !selectedAgent) {
      setError("Please fill in all required fields")
      return
    }

    try {
      setCreating(true)
      setError(null)

      const data: CreateAPIKeyData = {
        agent_id: selectedAgent,
        key_name: keyName,
        permissions,
        expires_in_days: expiresInDays,
      }

      const response = await createAPIKey(data)
      setNewKey(response)
      setShowCreateForm(false)
      
      // Reload keys
      await loadData()
      
      // Reset form
      setKeyName("")
      setSelectedAgent("")
      setPermissions(["chat"])
      setExpiresInDays(undefined)
    } catch (err: any) {
      console.error("Error creating API key:", err)
      setError(err.message || "Failed to create API key")
    } finally {
      setCreating(false)
    }
  }

  const handleRevokeKey = async (keyHash: string) => {
    if (!confirm("Are you sure you want to revoke this API key? This action cannot be undone.")) {
      return
    }

    try {
      await revokeAPIKey(keyHash)
      await loadData()
    } catch (err: any) {
      console.error("Error revoking API key:", err)
      setError(err.message || "Failed to revoke API key")
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(true)
    setTimeout(() => setCopiedKey(false), 2000)
  }

  const saveToLocalStorage = (key: APIKeyResponse) => {
    // Store agent-specific key
    localStorage.setItem(`oratio_api_key_${key.agent_id}`, key.api_key)
    // Also store as global fallback
    localStorage.setItem("oratio_api_key", key.api_key)
    
    // Close the new key display
    setNewKey(null)
    
    // Navigate to the agent page
    router.push(`/dashboard/agents/${key.agent_id}`)
  }

  const togglePermission = (permission: APIKeyPermission) => {
    setPermissions((prev) =>
      prev.includes(permission)
        ? prev.filter((p) => p !== permission)
        : [...prev, permission]
    )
  }

  const getAgentName = (agentId: string) => {
    const agent = agents.find((a) => a.agent_id === agentId)
    return agent?.agent_name || agentId
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[calc(100vh-200px)]">
          <div className="text-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="text-muted-foreground">Loading API keys...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="border-b border-neutral-800/50 bg-neutral-900/30 backdrop-blur-sm">
          <div className="p-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white">API Keys</h1>
                <p className="text-neutral-400 mt-1">
                  Manage API keys for your agents
                </p>
              </div>
              <Button onClick={() => setShowCreateForm(true)} className="bg-accent hover:bg-accent/90 text-white shadow-lg shadow-accent/20 gap-2">
                <IconPlus className="w-4 h-4" />
                Create API Key
              </Button>
            </div>
          </div>
        </div>

        {/* Content Area with Padding */}
        <div className="flex-1 overflow-auto p-8">
          <div className="max-w-4xl space-y-6">
            {error && (
              <Card className="p-4 bg-red-500/10 border-red-500/50">
                <div className="flex items-center gap-2 text-red-400">
                  <IconAlertCircle className="w-5 h-5" />
                  <p>{error}</p>
                </div>
              </Card>
            )}

            {/* New Key Display */}
            {newKey && (
              <Card className="p-6 bg-accent/10 border-accent/50">
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-accent">
                    <IconKey className="w-5 h-5" />
                    <h3 className="font-semibold text-white">API Key Created Successfully!</h3>
                  </div>
                  <p className="text-sm text-neutral-400">
                    Make sure to copy your API key now. You won't be able to see it again!
                  </p>
                  <div className="flex gap-2">
                    <Input
                      value={newKey.api_key}
                      readOnly
                      className="font-mono text-sm bg-neutral-900/50 border-neutral-800/50 text-white"
                    />
                    <Button
                      onClick={() => copyToClipboard(newKey.api_key)}
                      variant="outline"
                      size="icon"
                      className="border-neutral-800/50 hover:bg-neutral-800/50"
                    >
                      {copiedKey ? (
                        <IconCheck className="w-4 h-4 text-green-400" />
                      ) : (
                        <IconCopy className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => saveToLocalStorage(newKey)}
                      className="flex-1 bg-accent hover:bg-accent/90 text-white"
                    >
                      Save & Test Agent
                    </Button>
                    <Button
                      onClick={() => {
                        copyToClipboard(newKey.api_key)
                        setNewKey(null)
                      }}
                      variant="outline"
                      className="flex-1 border-neutral-800/50 hover:bg-neutral-800/50"
                    >
                      Copy & Close
                    </Button>
                  </div>
                </div>
              </Card>
            )}

            {/* Create Form */}
            {showCreateForm && (
              <Card className="p-6 bg-neutral-900/50 border-neutral-800/50">
                <h3 className="text-xl font-semibold mb-4 text-white">Create New API Key</h3>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="key-name" className="text-neutral-200">Key Name *</Label>
                    <Input
                      id="key-name"
                      value={keyName}
                      onChange={(e) => setKeyName(e.target.value)}
                      placeholder="e.g., Production Key"
                      className="mt-1 bg-neutral-900/50 border-neutral-800/50 text-white"
                    />
                  </div>

                  <div>
                    <Label htmlFor="agent" className="text-neutral-200">Agent *</Label>
                    <select
                      id="agent"
                      value={selectedAgent}
                      onChange={(e) => setSelectedAgent(e.target.value)}
                      className="w-full mt-1 px-3 py-2 border rounded-md bg-neutral-900/50 border-neutral-800/50 text-white"
                    >
                      <option value="" className="bg-neutral-900">Select an agent...</option>
                      {agents.map((agent) => (
                        <option key={agent.agent_id} value={agent.agent_id} className="bg-neutral-900">
                          {agent.agent_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <Label className="text-neutral-200">Permissions *</Label>
                    <div className="mt-2 space-y-2">
                      {(['chat', 'voice', 'admin'] as APIKeyPermission[]).map((permission) => (
                        <div key={permission} className="flex items-center gap-2">
                          <Checkbox
                            id={permission}
                            checked={permissions.includes(permission)}
                            onCheckedChange={() => togglePermission(permission)}
                          />
                          <label htmlFor={permission} className="text-sm capitalize cursor-pointer text-neutral-200">
                            {permission}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="expires" className="text-neutral-200">Expires In (days, optional)</Label>
                    <Input
                      id="expires"
                      type="number"
                      value={expiresInDays || ""}
                      onChange={(e) =>
                        setExpiresInDays(e.target.value ? parseInt(e.target.value) : undefined)
                      }
                      placeholder="Leave empty for no expiration"
                      className="mt-1 bg-neutral-900/50 border-neutral-800/50 text-white"
                    />
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={handleCreateKey}
                      disabled={creating || !keyName.trim() || !selectedAgent}
                      className="flex-1 bg-accent hover:bg-accent/90 text-white"
                    >
                      {creating ? "Creating..." : "Create API Key"}
                    </Button>
                    <Button
                      onClick={() => setShowCreateForm(false)}
                      variant="outline"
                      className="flex-1 border-neutral-800/50 hover:bg-neutral-800/50"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              </Card>
            )}

            {/* API Keys List */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-white">Your API Keys</h2>
              {apiKeys.length === 0 ? (
                <Card className="p-12 text-center bg-neutral-900/50 border-neutral-800/50">
                  <div className="h-16 w-16 rounded-xl bg-neutral-800/50 flex items-center justify-center mx-auto mb-4">
                    <IconKey className="w-8 h-8 text-neutral-600" />
                  </div>
                  <p className="text-neutral-400">No API keys yet</p>
                  <p className="text-sm text-neutral-500 mt-1">
                    Create your first API key to start using the API
                  </p>
                </Card>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {apiKeys.map((key) => (
                    <Card key={key.api_key_hash} className="p-6 bg-neutral-900/50 border-neutral-800/50 hover:border-accent/50 hover:shadow-lg hover:shadow-accent/10 transition-all">
                      <div className="space-y-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <div className="h-10 w-10 rounded-xl bg-neutral-800/50 flex items-center justify-center shrink-0">
                                <IconKey className="h-5 w-5 text-accent" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <h3 className="font-semibold text-white truncate">{key.key_name}</h3>
                                <Badge
                                  variant="secondary"
                                  className={
                                    key.status === "active"
                                      ? "bg-green-500/10 text-green-400 border-green-500/20"
                                      : key.status === "expired"
                                      ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                                      : "bg-red-500/10 text-red-400 border-red-500/20"
                                  }
                                >
                                  {key.status.toUpperCase()}
                                </Badge>
                              </div>
                            </div>
                          </div>
                          {key.status === "active" && (
                            <Button
                              onClick={() => handleRevokeKey(key.api_key_hash)}
                              variant="destructive"
                              size="sm"
                              className="gap-2 shrink-0 bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/50"
                            >
                              <IconTrash className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                        <div className="text-sm text-neutral-400 space-y-1.5">
                          <p>
                            <span className="font-medium text-neutral-300">Agent:</span> {getAgentName(key.agent_id)}
                          </p>
                          <p>
                            <span className="font-medium text-neutral-300">Permissions:</span>{" "}
                            {key.permissions.join(", ")}
                          </p>
                          <p>
                            <span className="font-medium text-neutral-300">Created:</span>{" "}
                            {new Date(key.created_at * 1000).toLocaleDateString()}
                          </p>
                          {key.expires_at && (
                            <p>
                              <span className="font-medium text-neutral-300">Expires:</span>{" "}
                              {new Date(key.expires_at * 1000).toLocaleDateString()}
                            </p>
                          )}
                          {key.last_used_at && (
                            <p>
                              <span className="font-medium text-neutral-300">Last used:</span>{" "}
                              {new Date(key.last_used_at * 1000).toLocaleDateString()}
                            </p>
                          )}
                          <p className="font-mono text-xs text-neutral-500">
                            {key.api_key_hash.substring(0, 20)}...
                          </p>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
