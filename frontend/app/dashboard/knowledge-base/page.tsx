"use client"
import DashboardLayout from "@/components/dashboard-layout"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { IconPlus, IconDatabase, IconSearch, IconFile, IconFolder } from "@tabler/icons-react"
import { Input } from "@/components/ui/input"
import Link from "next/link"
import { useState } from "react"

// Mock data
const mockKnowledgeBases = [
  {
    id: "1",
    name: "Product Documentation",
    description: "Complete product documentation and user guides",
    fileCount: 24,
    type: "folder",
    lastUpdated: "2d ago",
  },
  {
    id: "2",
    name: "FAQ Database",
    description: "Frequently asked questions and answers",
    fileCount: 156,
    type: "folder",
    lastUpdated: "5d ago",
  },
]

export default function KnowledgeBasePage() {
  const [knowledgeBases] = useState(mockKnowledgeBases)
  const [searchQuery, setSearchQuery] = useState("")

  const filteredKnowledgeBases = knowledgeBases.filter((kb) =>
    kb.name.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  // Empty state
  if (knowledgeBases.length === 0) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-full p-8">
          <div className="flex flex-col items-center max-w-md text-center space-y-4">
            <div className="h-24 w-24 rounded-full bg-neutral-900 border-2 border-dashed border-neutral-700 flex items-center justify-center">
              <IconDatabase className="h-12 w-12 text-neutral-600" />
            </div>
            <h2 className="text-2xl font-bold text-white">No knowledge bases yet</h2>
            <p className="text-neutral-400">
              Upload documents and files to create a knowledge base for your AI agents.
            </p>
            <Link href="/dashboard/knowledge-base/create">
              <Button className="bg-accent hover:bg-accent/90 text-white">
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
        <div className="border-b border-neutral-800 bg-neutral-900/50 backdrop-blur-sm">
          <div className="p-6 md:p-8">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold text-white">Knowledge Base</h1>
                <p className="text-neutral-400 mt-1">Manage documents and data sources for your AI agents.</p>
              </div>
              <Link href="/dashboard/knowledge-base/create">
                <Button className="bg-accent hover:bg-accent/90 text-white">
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
                className="pl-10 bg-neutral-900 border-neutral-800 text-white placeholder:text-neutral-500"
              />
            </div>
          </div>
        </div>

        {/* Knowledge Bases Grid */}
        <div className="flex-1 overflow-auto p-6 md:p-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredKnowledgeBases.map((kb) => (
              <Card
                key={kb.id}
                className="bg-neutral-900 border-neutral-800 p-6 hover:border-accent/50 transition-colors"
              >
                <div className="flex items-start gap-4">
                  <div className="h-12 w-12 rounded-full bg-neutral-800 flex items-center justify-center shrink-0">
                    <IconFolder className="h-6 w-6 text-accent" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-white truncate mb-2">{kb.name}</h3>
                    <p className="text-sm text-neutral-400 line-clamp-2 mb-4">{kb.description}</p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs text-neutral-500">
                        <IconFile className="h-4 w-4" />
                        <span>{kb.fileCount} files</span>
                      </div>
                      <span className="text-xs text-neutral-500">Updated {kb.lastUpdated}</span>
                    </div>
                  </div>
                </div>
              </Card>
            ))}

            {/* Create New Knowledge Base Card */}
            <Link href="/dashboard/knowledge-base/create">
              <Card className="bg-neutral-900 border-2 border-dashed border-neutral-700 hover:border-accent/50 transition-colors p-6 h-full flex items-center justify-center cursor-pointer group">
                <div className="text-center">
                  <div className="h-12 w-12 rounded-full bg-neutral-800 group-hover:bg-accent/10 flex items-center justify-center mx-auto mb-3 transition-colors">
                    <IconPlus className="h-6 w-6 text-neutral-600 group-hover:text-accent transition-colors" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-1">Add Knowledge Base</h3>
                  <p className="text-sm text-neutral-400">Upload documents and files for your agents.</p>
                </div>
              </Card>
            </Link>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
