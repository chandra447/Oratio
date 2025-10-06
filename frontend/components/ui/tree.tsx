"use client"

import * as React from "react"
import { ChevronRight, Folder, File } from "lucide-react"
import { cn } from "@/lib/utils"

interface TreeContextValue {
  expandedIds: Set<string>
  selectedIds: Set<string>
  toggleExpand: (id: string) => void
  toggleSelect: (id: string) => void
}

const TreeContext = React.createContext<TreeContextValue | undefined>(undefined)

function useTree() {
  const context = React.useContext(TreeContext)
  if (!context) {
    throw new Error("Tree components must be used within TreeProvider")
  }
  return context
}

interface TreeProviderProps {
  children: React.ReactNode
  defaultExpandedIds?: string[]
  defaultSelectedIds?: string[]
  onSelectionChange?: (ids: string[]) => void
}

export function TreeProvider({
  children,
  defaultExpandedIds = [],
  defaultSelectedIds = [],
  onSelectionChange,
}: TreeProviderProps) {
  const [expandedIds, setExpandedIds] = React.useState(new Set(defaultExpandedIds))
  const [selectedIds, setSelectedIds] = React.useState(new Set(defaultSelectedIds))

  const toggleExpand = React.useCallback((id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  const toggleSelect = React.useCallback(
    (id: string) => {
      setSelectedIds((prev) => {
        const next = new Set(prev)
        if (next.has(id)) {
          next.delete(id)
        } else {
          next.add(id)
        }
        onSelectionChange?.(Array.from(next))
        return next
      })
    },
    [onSelectionChange],
  )

  return (
    <TreeContext.Provider value={{ expandedIds, selectedIds, toggleExpand, toggleSelect }}>
      {children}
    </TreeContext.Provider>
  )
}

export function TreeView({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("text-sm", className)}>{children}</div>
}

interface TreeNodeProps {
  nodeId: string
  children: React.ReactNode
  level?: number
  isLast?: boolean
}

export function TreeNode({ nodeId, children, level = 0, isLast }: TreeNodeProps) {
  return (
    <div className="relative" data-node-id={nodeId} data-level={level} data-last={isLast}>
      {children}
    </div>
  )
}

interface TreeNodeTriggerProps {
  children: React.ReactNode
  className?: string
}

export function TreeNodeTrigger({ children, className }: TreeNodeTriggerProps) {
  return (
    <div className={cn("flex items-center gap-1 py-1 px-2 rounded hover:bg-neutral-800/50 cursor-pointer", className)}>
      {children}
    </div>
  )
}

interface TreeNodeContentProps {
  children: React.ReactNode
  hasChildren?: boolean
}

export function TreeNodeContent({ children, hasChildren }: TreeNodeContentProps) {
  const node = React.useContext(TreeNodeContext)
  const { expandedIds } = useTree()
  const isExpanded = node?.nodeId ? expandedIds.has(node.nodeId) : false

  if (!hasChildren || !isExpanded) return null

  return <div className="ml-4 border-l border-neutral-800 pl-2">{children}</div>
}

interface TreeExpanderProps {
  hasChildren?: boolean
}

export function TreeExpander({ hasChildren }: TreeExpanderProps) {
  const node = React.useContext(TreeNodeContext)
  const { expandedIds, toggleExpand } = useTree()
  const isExpanded = node?.nodeId ? expandedIds.has(node.nodeId) : false

  if (!hasChildren) {
    return <div className="w-4 h-4" />
  }

  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation()
        if (node?.nodeId) toggleExpand(node.nodeId)
      }}
      className="w-4 h-4 flex items-center justify-center hover:bg-neutral-700 rounded"
    >
      <ChevronRight className={cn("h-3 w-3 text-neutral-400 transition-transform", isExpanded && "rotate-90")} />
    </button>
  )
}

interface TreeIconProps {
  hasChildren?: boolean
  icon?: React.ReactNode
}

export function TreeIcon({ hasChildren, icon }: TreeIconProps) {
  if (icon) return <>{icon}</>
  return hasChildren ? <Folder className="h-4 w-4 text-blue-400" /> : <File className="h-4 w-4 text-neutral-400" />
}

export function TreeLabel({ children }: { children: React.ReactNode }) {
  return <span className="text-neutral-200 flex-1">{children}</span>
}

const TreeNodeContext = React.createContext<{ nodeId: string } | undefined>(undefined)

// Wrapper to provide nodeId context
export function TreeNodeWrapper({ nodeId, children }: { nodeId: string; children: React.ReactNode }) {
  return <TreeNodeContext.Provider value={{ nodeId }}>{children}</TreeNodeContext.Provider>
}
