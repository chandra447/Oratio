"use client"
import DashboardLayout from "@/components/dashboard-layout"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { IconPlus, IconDatabase, IconSearch, IconFile, IconFolder } from "@tabler/icons-react"
import { Input } from "@/components/ui/input"
import Link from "next/link"
import { useState, useEffect } from "react"
import { Loader2 } from "lucide-react"
import { 
  listKnowledgeBases, 
  getFileCount, 
  formatRelativeTime, 
  getStatusColor,
  type KnowledgeBase 
} from "@/lib/api/knowledge-bases"
import { useAuth } from "@/lib/auth/auth-context"

export default function KnowledgeBasePage() {
  const { user } = useAuth()
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchKnowledgeBases = async () => {
      if (!user) return
      
      try {
        setIsLoading(true)
        setError(null)
        const data = await listKnowledgeBases()
        setKnowledgeBases(data)
      } catch (err: any) {
        console.error("Failed to fetch knowledge bases:", err)
        setError(err.message || "Failed to load knowledge bases")
      } finally {
        setIsLoading(false)
      }
    }

    fetchKnowledgeBases()
  }, [user])

  const filteredKnowledgeBases = knowledgeBases.filter((kb) =>
    kb.s3Path.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  // Loading state
  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-accent" />
            <p className="text-neutral-400">Loading knowledge bases...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  // Error state
  if (error) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <div className="flex flex-col items-center gap-4 max-w-md text-center">
            <div className="h-16 w-16 rounded-full bg-red-500/10 flex items-center justify-center">
              <span className="text-2xl">⚠️</span>
            </div>
            <h2 className="text-xl font-semibold text-white">Error Loading Knowledge Bases</h2>
            <p className="text-neutral-400">{error}</p>
            <Button onClick={() => window.location.reload()} className="bg-accent hover:bg-accent/90">
              Retry
            </Button>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  // Empty state
  if (knowledgeBases.length === 0) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-full p-8">
          <div className="flex flex-col items-center max-w-md text-center space-y-4">
            <div className="h-24 w-24 rounded-2xl bg-neutral-900/50 border-2 border-dashed border-neutral-700/50 flex items-center justify-center">
              <IconDatabase className="h-12 w-12 text-neutral-600" />
            </div>
            <h2 className="text-2xl font-bold text-white">No knowledge bases yet</h2>
            <p className="text-neutral-400">
              Upload documents and files to create a knowledge base for your AI agents.
            </p>
            <Link href="/dashboard/knowledge-base/create">
              <Button className="bg-accent hover:bg-accent/90 text-white shadow-lg shadow-accent/20">
                <IconPlus className="h-4 w-4 mr-2" />
                Create Knowledge Base
              </Button>
            </Link>
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
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold text-white">Knowledge Base</h1>
                <p className="text-neutral-400 mt-1">Manage documents and data sources for your AI agents.</p>
              </div>
              <Link href="/dashboard/knowledge-base/create">
                <Button className="bg-accent hover:bg-accent/90 text-white shadow-lg shadow-accent/20">
                  <IconPlus className="h-4 w-4 mr-2" />
                  Add Knowledge Base
                </Button>
              </Link>
            </div>

            {/* Search */}
            <div className="mt-6 relative">
              <IconSearch className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-neutral-500" />
              <Input
                placeholder="Search knowledge bases..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-neutral-900/50 border-neutral-800/50 text-white placeholder:text-neutral-500 focus:border-accent/50"
              />
            </div>
          </div>
        </div>

        {/* Knowledge Bases Grid */}
        <div className="flex-1 overflow-auto p-8">
          {filteredKnowledgeBases.length === 0 && searchQuery ? (
            <div className="flex flex-col items-center justify-center h-64">
              <IconSearch className="h-12 w-12 text-neutral-600 mb-4" />
              <p className="text-neutral-400">No knowledge bases found matching "{searchQuery}"</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredKnowledgeBases.map((kb) => (
                <Link key={kb.knowledgeBaseId} href={`/dashboard/knowledge-base/${kb.knowledgeBaseId}`}>
                  <Card className="bg-neutral-900/50 border-neutral-800/50 p-6 hover:border-accent/50 hover:shadow-lg hover:shadow-accent/10 transition-all cursor-pointer">
                    <div className="flex items-start gap-4">
                      <div className="h-12 w-12 rounded-xl bg-neutral-800/50 flex items-center justify-center shrink-0">
                        <IconDatabase className="h-6 w-6 text-accent" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="text-lg font-semibold text-white truncate flex-1">
                            {kb.s3Path.split('/').pop() || 'Knowledge Base'}
                          </h3>
                          <Badge variant="secondary" className={getStatusColor(kb.status)}>
                            {kb.status.toUpperCase()}
                          </Badge>
                        </div>
                        <p className="text-sm text-neutral-400 line-clamp-2 mb-4">
                          {kb.s3Path}
                        </p>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2 text-xs text-neutral-500">
                            <IconFile className="h-4 w-4" />
                            <span>{getFileCount(kb)} files</span>
                          </div>
                          <span className="text-xs text-neutral-500">
                            {formatRelativeTime(kb.updatedAt)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </Card>
                </Link>
              ))}

              {/* Create New Knowledge Base Card */}
              <Link href="/dashboard/knowledge-base/create">
                <Card className="bg-neutral-900/30 border-2 border-dashed border-neutral-700/50 hover:border-accent/50 hover:bg-neutral-900/50 transition-all p-6 h-full flex items-center justify-center cursor-pointer group">
                  <div className="text-center">
                    <div className="h-12 w-12 rounded-xl bg-neutral-800/50 group-hover:bg-accent/10 flex items-center justify-center mx-auto mb-3 transition-colors">
                      <IconPlus className="h-6 w-6 text-neutral-600 group-hover:text-accent transition-colors" />
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-1">Add Knowledge Base</h3>
                    <p className="text-sm text-neutral-400">Upload documents and files for your agents.</p>
                  </div>
                </Card>
              </Link>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
