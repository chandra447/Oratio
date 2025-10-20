"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import DashboardLayout from "@/components/dashboard-layout"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  IconArrowLeft,
  IconDatabase,
  IconFile,
  IconFolder,
  IconTrash,
  IconDownload,
} from "@tabler/icons-react"
import { Loader2 } from "lucide-react"
import Link from "next/link"
import {
  getKnowledgeBase,
  deleteKnowledgeBase,
  getStatusColor,
  formatRelativeTime,
  type KnowledgeBase,
} from "@/lib/api/knowledge-bases"

export default function KnowledgeBaseDetailPage() {
  const params = useParams()
  const router = useRouter()
  const knowledgeBaseId = params.knowledgeBaseId as string

  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    const fetchKnowledgeBase = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const data = await getKnowledgeBase(knowledgeBaseId)
        setKnowledgeBase(data)
      } catch (err: any) {
        console.error("Failed to fetch knowledge base:", err)
        setError(err.message || "Failed to load knowledge base")
      } finally {
        setIsLoading(false)
      }
    }

    if (knowledgeBaseId) {
      fetchKnowledgeBase()
    }
  }, [knowledgeBaseId])

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this knowledge base? This action cannot be undone.")) {
      return
    }

    try {
      setIsDeleting(true)
      await deleteKnowledgeBase(knowledgeBaseId)
      router.push("/dashboard/knowledge-base")
    } catch (err: any) {
      console.error("Failed to delete knowledge base:", err)
      alert(err.message || "Failed to delete knowledge base")
      setIsDeleting(false)
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-accent" />
            <p className="text-neutral-400">Loading knowledge base...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  // Error state
  if (error || !knowledgeBase) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <div className="flex flex-col items-center gap-4 max-w-md text-center">
            <div className="h-16 w-16 rounded-full bg-red-500/10 flex items-center justify-center">
              <span className="text-2xl">⚠️</span>
            </div>
            <h2 className="text-xl font-semibold text-white">Error Loading Knowledge Base</h2>
            <p className="text-neutral-400">{error || "Knowledge base not found"}</p>
            <Link href="/dashboard/knowledge-base">
              <Button className="bg-accent hover:bg-accent/90">
                <IconArrowLeft className="h-4 w-4 mr-2" />
                Back to Knowledge Bases
              </Button>
            </Link>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  const files = Object.entries(knowledgeBase.folderFileDescriptions || {})

  return (
    <DashboardLayout>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="border-b border-neutral-800/50 bg-neutral-900/30 backdrop-blur-sm">
          <div className="p-8">
            <div className="flex items-start gap-4 mb-6">
              <Link href="/dashboard/knowledge-base">
                <Button variant="outline" size="icon" className="border-neutral-800/50 hover:bg-neutral-800/50">
                  <IconArrowLeft className="h-4 w-4" />
                </Button>
              </Link>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <div className="h-12 w-12 rounded-xl bg-neutral-800/50 flex items-center justify-center shrink-0">
                    <IconDatabase className="h-6 w-6 text-accent" />
                  </div>
                  <div className="flex-1">
                    <h1 className="text-3xl font-bold text-white">
                      {knowledgeBase.s3Path.split('/').pop() || 'Knowledge Base'}
                    </h1>
                    <p className="text-neutral-400 mt-1">{knowledgeBase.s3Path}</p>
                  </div>
                  <Badge variant="secondary" className={getStatusColor(knowledgeBase.status)}>
                    {knowledgeBase.status.toUpperCase()}
                  </Badge>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-sm text-neutral-400">
                <span className="font-medium text-neutral-300">Created:</span>{" "}
                {new Date(knowledgeBase.createdAt * 1000).toLocaleDateString()}
              </div>
              <div className="text-sm text-neutral-400">
                <span className="font-medium text-neutral-300">Updated:</span>{" "}
                {formatRelativeTime(knowledgeBase.updatedAt)}
              </div>
              <div className="text-sm text-neutral-400">
                <span className="font-medium text-neutral-300">Files:</span>{" "}
                {files.length}
              </div>
              <div className="ml-auto">
                <Button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  variant="destructive"
                  className="gap-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/50"
                >
                  {isDeleting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Deleting...
                    </>
                  ) : (
                    <>
                      <IconTrash className="h-4 w-4" />
                      Delete
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-8">
          <div className="max-w-5xl">
            <h2 className="text-xl font-semibold text-white mb-4">Files & Documents</h2>
            
            {files.length === 0 ? (
              <Card className="p-12 text-center bg-neutral-900/50 border-neutral-800/50">
                <IconFolder className="h-12 w-12 mx-auto text-neutral-600 mb-4" />
                <p className="text-neutral-400">No files in this knowledge base</p>
                <p className="text-sm text-neutral-500 mt-1">
                  Upload documents to add knowledge for your agents
                </p>
              </Card>
            ) : (
              <div className="grid gap-3">
                {files.map(([path, description]) => {
                  const fileName = path.split('/').pop() || path
                  const isFolder = !fileName.includes('.')
                  
                  return (
                    <Card
                      key={path}
                      className="bg-neutral-900/50 border-neutral-800/50 p-4 hover:border-accent/50 transition-all"
                    >
                      <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-lg bg-neutral-800/50 flex items-center justify-center shrink-0">
                          {isFolder ? (
                            <IconFolder className="h-5 w-5 text-accent" />
                          ) : (
                            <IconFile className="h-5 w-5 text-accent" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-white truncate">{fileName}</h3>
                          {description && (
                            <p className="text-sm text-neutral-400 truncate">{description}</p>
                          )}
                          <p className="text-xs text-neutral-500 truncate mt-1">{path}</p>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          className="border-neutral-800/50 hover:bg-neutral-800/50 gap-2 shrink-0"
                        >
                          <IconDownload className="h-4 w-4" />
                          Download
                        </Button>
                      </div>
                    </Card>
                  )
                })}
              </div>
            )}

            {/* Bedrock Info */}
            {knowledgeBase.bedrockKnowledgeBaseId && (
              <div className="mt-8">
                <h2 className="text-xl font-semibold text-white mb-4">Bedrock Configuration</h2>
                <Card className="bg-neutral-900/50 border-neutral-800/50 p-6">
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="font-medium text-neutral-300">Bedrock KB ID:</span>{" "}
                      <span className="text-neutral-400 font-mono">{knowledgeBase.bedrockKnowledgeBaseId}</span>
                    </div>
                    <div>
                      <span className="font-medium text-neutral-300">S3 Path:</span>{" "}
                      <span className="text-neutral-400 font-mono">{knowledgeBase.s3Path}</span>
                    </div>
                  </div>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}

