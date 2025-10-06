"use client"
import DashboardLayout from "@/components/dashboard-layout"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { IconPlus, IconKey, IconCopy, IconEye, IconEyeOff } from "@tabler/icons-react"
import { useState } from "react"

// Mock data
const mockApiKeys = [
  {
    id: "1",
    name: "Production API Key",
    key: "sk_live_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
    created: "2024-01-15",
    lastUsed: "2h ago",
  },
  {
    id: "2",
    name: "Development API Key",
    key: "sk_test_xyz987wvu654tsr321qpo098nml765kji432hgf210edc098ba",
    created: "2024-01-10",
    lastUsed: "1d ago",
  },
]

export default function ApiKeysPage() {
  const [apiKeys] = useState(mockApiKeys)
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set())

  const toggleKeyVisibility = (id: string) => {
    setVisibleKeys((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      return newSet
    })
  }

  const copyToClipboard = (key: string) => {
    navigator.clipboard.writeText(key)
  }

  const maskKey = (key: string) => {
    return key.slice(0, 12) + "•".repeat(20) + key.slice(-4)
  }

  // Empty state
  if (apiKeys.length === 0) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-full p-8">
          <div className="flex flex-col items-center max-w-md text-center space-y-4">
            <div className="h-24 w-24 rounded-full bg-neutral-900 border-2 border-dashed border-neutral-700 flex items-center justify-center">
              <IconKey className="h-12 w-12 text-neutral-600" />
            </div>
            <h2 className="text-2xl font-bold text-white">No API keys yet</h2>
            <p className="text-neutral-400">Create an API key to integrate Oratio with your applications.</p>
            <Button className="bg-accent hover:bg-accent/90 text-white">
              <IconPlus className="h-4 w-4 mr-2" />
              Create API Key
            </Button>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="border-b border-neutral-800 bg-neutral-900/50 backdrop-blur-sm">
          <div className="p-6 md:p-8">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold text-white">API Keys</h1>
                <p className="text-neutral-400 mt-1">Manage API keys for integrating with your applications.</p>
              </div>
              <Button className="bg-accent hover:bg-accent/90 text-white">
                <IconPlus className="h-4 w-4 mr-2" />
                Create API Key
              </Button>
            </div>
          </div>
        </div>

        {/* API Keys List */}
        <div className="flex-1 overflow-auto p-6 md:p-8">
          <div className="max-w-4xl space-y-4">
            {apiKeys.map((apiKey) => (
              <Card key={apiKey.id} className="bg-neutral-900 border-neutral-800 p-6">
                <div className="flex flex-col gap-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-1">{apiKey.name}</h3>
                      <div className="flex items-center gap-2 text-sm text-neutral-400">
                        <span>Created {apiKey.created}</span>
                        <span>•</span>
                        <span>Last used {apiKey.lastUsed}</span>
                      </div>
                    </div>
                    <Badge variant="secondary" className="bg-green-500/10 text-green-400 border-green-500/20">
                      ACTIVE
                    </Badge>
                  </div>

                  <div className="flex items-center gap-2 bg-neutral-950 border border-neutral-800 rounded-lg p-3">
                    <code className="flex-1 text-sm text-neutral-300 font-mono">
                      {visibleKeys.has(apiKey.id) ? apiKey.key : maskKey(apiKey.key)}
                    </code>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => toggleKeyVisibility(apiKey.id)}
                      className="text-neutral-400 hover:text-white"
                    >
                      {visibleKeys.has(apiKey.id) ? (
                        <IconEyeOff className="h-4 w-4" />
                      ) : (
                        <IconEye className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => copyToClipboard(apiKey.key)}
                      className="text-neutral-400 hover:text-white"
                    >
                      <IconCopy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
