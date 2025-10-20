"use client"
import DashboardLayout from "@/components/dashboard-layout"
import type React from "react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Checkbox } from "@/components/ui/checkbox"
import { IconCheck, IconMicrophone, IconMessage, IconFolder, IconFile, IconX } from "@tabler/icons-react"
import { useState, useCallback, useRef } from "react"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  TreeProvider,
  TreeView,
  TreeNode,
  TreeNodeTrigger,
  TreeNodeContent,
  TreeExpander,
  TreeIcon,
  TreeLabel,
  TreeNodeWrapper,
} from "@/components/ui/tree"

type Step = "description" | "knowledge-base" | "mode"

interface TreeNodeData {
  id: string
  name: string
  type: "file" | "folder"
  path: string
  description: string
  children?: TreeNodeData[]
  file?: File
}

export default function CreateAgentPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState<Step>("description")
  const [agentName, setAgentName] = useState("")
  const [agentDescription, setAgentDescription] = useState("")
  const [sop, setSop] = useState("")
  const [humanInLoop, setHumanInLoop] = useState(false)
  const [humanInLoopScenarios, setHumanInLoopScenarios] = useState("")
  const [fileTree, setFileTree] = useState<TreeNodeData[]>([])
  const [selectedMode, setSelectedMode] = useState<"voice" | "conversational" | null>(null)
  const [voicePersonality, setVoicePersonality] = useState("")
  const [showVoicePersonality, setShowVoicePersonality] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const folderInputRef = useRef<HTMLInputElement>(null)

  const steps: { id: Step; label: string }[] = [
    { id: "description", label: "Agent Description" },
    { id: "knowledge-base", label: "Knowledge Base" },
    { id: "mode", label: "Voice/Conversational Mode" },
  ]

  const currentStepIndex = steps.findIndex((s) => s.id === currentStep)

  const buildTreeFromFiles = useCallback((files: FileList): TreeNodeData[] => {
    const root: TreeNodeData[] = []
    const nodeMap = new Map<string, TreeNodeData>()

    Array.from(files).forEach((file) => {
      const path = (file as any).webkitRelativePath || file.name
      const parts = path.split("/")

      parts.forEach((part, index) => {
        const isFile = index === parts.length - 1
        const fullPath = parts.slice(0, index + 1).join("/")
        const parentPath = index > 0 ? parts.slice(0, index).join("/") : null

        // Skip if we've already created this node
        if (nodeMap.has(fullPath)) {
          return
        }

        // Create the node
        const node: TreeNodeData = {
          id: fullPath,
          name: part,
          type: isFile ? "file" : "folder",
          path: fullPath,
          description: "",
          children: isFile ? undefined : [],
          file: isFile ? file : undefined,
        }

        nodeMap.set(fullPath, node)

        // Add to parent or root
        if (parentPath) {
          const parent = nodeMap.get(parentPath)
          if (parent && parent.children) {
            parent.children.push(node)
          }
        } else {
          root.push(node)
        }
      })
    })

    return root
  }, [])

  const handleFolderUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (!files || files.length === 0) return

      const tree = buildTreeFromFiles(files)
      setFileTree((prev) => [...prev, ...tree])

      // Reset input
      if (e.target) e.target.value = ""
    },
    [buildTreeFromFiles],
  )

  const updateNodeDescription = useCallback((nodeId: string, description: string) => {
    const updateNode = (nodes: TreeNodeData[]): TreeNodeData[] => {
      return nodes.map((node) => {
        if (node.id === nodeId) {
          return { ...node, description }
        }
        if (node.children) {
          return { ...node, children: updateNode(node.children) }
        }
        return node
      })
    }
    setFileTree((prev) => updateNode(prev))
  }, [])

  const removeNode = useCallback((nodeId: string) => {
    const filterNode = (nodes: TreeNodeData[]): TreeNodeData[] => {
      return nodes
        .filter((node) => node.id !== nodeId)
        .map((node) => {
          if (node.children) {
            return { ...node, children: filterNode(node.children) }
          }
          return node
        })
    }
    setFileTree((prev) => filterNode(prev))
  }, [])

  const renderTree = (nodes: TreeNodeData[], level = 0): React.ReactNode => {
    return nodes.map((node, index) => {
      const isLast = index === nodes.length - 1
      const hasChildren = node.type === "folder" && node.children && node.children.length > 0

      return (
        <TreeNodeWrapper key={node.id} nodeId={node.id}>
          <TreeNode nodeId={node.id} level={level} isLast={isLast}>
            <TreeNodeTrigger>
              <TreeExpander hasChildren={hasChildren} />
              <TreeIcon
                hasChildren={hasChildren}
                icon={
                  node.type === "folder" ? (
                    <IconFolder className="h-4 w-4 text-blue-400" />
                  ) : (
                    <IconFile className="h-4 w-4 text-neutral-400" />
                  )
                }
              />
              <TreeLabel>{node.name}</TreeLabel>
              <Button
                size="sm"
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation()
                  removeNode(node.id)
                }}
                className="h-6 w-6 p-0 text-neutral-400 hover:text-red-400"
              >
                <IconX className="h-3 w-3" />
              </Button>
            </TreeNodeTrigger>
            <div className="ml-8 mt-1 mb-2">
              <Input
                placeholder={`Description for ${node.name}...`}
                value={node.description}
                onChange={(e) => updateNodeDescription(node.id, e.target.value)}
                className="bg-neutral-950 border-neutral-800 text-white text-xs h-8"
                onClick={(e) => e.stopPropagation()}
              />
            </div>
            {hasChildren && (
              <TreeNodeContent hasChildren={hasChildren}>{renderTree(node.children!, level + 1)}</TreeNodeContent>
            )}
          </TreeNode>
        </TreeNodeWrapper>
      )
    })
  }

  const canProceed = () => {
    if (currentStep === "description") {
      return agentName.trim() !== "" && agentDescription.trim() !== "" && sop.trim() !== ""
    }
    if (currentStep === "knowledge-base") {
      return true // Optional step
    }
    if (currentStep === "mode") {
      return selectedMode !== null
    }
    return false
  }

  const handleNext = () => {
    if (currentStep === "description") {
      setCurrentStep("knowledge-base")
    } else if (currentStep === "knowledge-base") {
      setCurrentStep("mode")
    }
  }

  const handleBack = () => {
    if (currentStep === "knowledge-base") {
      setCurrentStep("description")
    } else if (currentStep === "mode") {
      setCurrentStep("knowledge-base")
    }
  }

  const collectAllFiles = (nodes: TreeNodeData[]): File[] => {
    const files: File[] = []
    const traverse = (nodeList: TreeNodeData[]) => {
      for (const node of nodeList) {
        if (node.type === "file" && node.file) {
          files.push(node.file)
        }
        if (node.children) {
          traverse(node.children)
        }
      }
    }
    traverse(nodes)
    return files
  }

  const collectFileDescriptions = (nodes: TreeNodeData[]): Record<string, string> => {
    const descriptions: Record<string, string> = {}
    const traverse = (nodeList: TreeNodeData[]) => {
      for (const node of nodeList) {
        if (node.type === "file") {
          descriptions[node.path] = node.description || ""
        }
        if (node.children) {
          traverse(node.children)
        }
      }
    }
    traverse(nodes)
    return descriptions
  }

  const handleCreate = async () => {
    if (!selectedMode) return

    setIsSubmitting(true)
    setError(null)

    try {
      const { createAgent } = await import("@/lib/api/agents")
      
      // Collect all files from tree
      const files = collectAllFiles(fileTree)
      const fileDescriptions = collectFileDescriptions(fileTree)

      // Build agent data
      const agentData = {
        agent_name: agentName,
        agent_type: (selectedMode === "voice" ? "voice" : "text") as "voice" | "text",
        sop: sop,
        knowledge_base_description: agentDescription,
        human_handoff_description: humanInLoopScenarios || "N/A",
        files: files,
        file_descriptions: fileDescriptions,
      }

      // Add voice personality if voice mode and provided
      if (selectedMode === "voice" && voicePersonality.trim()) {
        agentData.voice_personality = {
          additional_instructions: voicePersonality,
        }
      }

      // Create agent
      const createdAgent = await createAgent(agentData)
      
      // Redirect to agents list
      router.push("/dashboard/agents")
    } catch (err: any) {
      console.error("Error creating agent:", err)
      setError(err.message || "Failed to create agent. Please try again.")
      setIsSubmitting(false)
    }
  }

  return (
    <DashboardLayout>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="border-b border-neutral-800 bg-neutral-900/50 backdrop-blur-sm">
          <div className="p-6 md:p-8">
            <h1 className="text-3xl font-bold text-white">Create New Agent</h1>
            <p className="text-neutral-400 mt-1">Follow the steps to configure your AI agent.</p>
          </div>
        </div>

        {/* Timeline */}
        <div className="border-b border-neutral-800 bg-neutral-900/30 px-6 md:px-8 py-6">
          <div className="flex items-center justify-between max-w-3xl mx-auto">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={cn(
                      "h-10 w-10 rounded-full flex items-center justify-center border-2 transition-colors",
                      index < currentStepIndex
                        ? "bg-accent border-accent"
                        : index === currentStepIndex
                          ? "border-accent bg-accent/20"
                          : "border-neutral-700 bg-neutral-900",
                    )}
                  >
                    {index < currentStepIndex ? (
                      <IconCheck className="h-5 w-5 text-white" />
                    ) : (
                      <span
                        className={cn(
                          "text-sm font-semibold",
                          index === currentStepIndex ? "text-accent" : "text-neutral-500",
                        )}
                      >
                        {index + 1}
                      </span>
                    )}
                  </div>
                  <span
                    className={cn(
                      "text-xs mt-2 text-center",
                      index === currentStepIndex ? "text-white font-medium" : "text-neutral-500",
                    )}
                  >
                    {step.label}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={cn(
                      "h-0.5 flex-1 mx-2 transition-colors",
                      index < currentStepIndex ? "bg-accent" : "bg-neutral-800",
                    )}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6 md:p-8">
          <div className="max-w-3xl mx-auto">
            {currentStep === "description" && (
              <Card className="bg-neutral-900 border-neutral-800 p-6">
                <h2 className="text-xl font-semibold text-white mb-6">Agent Description</h2>
                <div className="space-y-6">
                  <div>
                    <Label htmlFor="agent-name" className="text-white mb-2">
                      Agent Name
                    </Label>
                    <Input
                      id="agent-name"
                      placeholder="e.g., Customer Support Agent"
                      value={agentName}
                      onChange={(e) => setAgentName(e.target.value)}
                      className="bg-neutral-950 border-neutral-800 text-white"
                    />
                  </div>
                  <div>
                    <Label htmlFor="agent-description" className="text-white mb-2">
                      Description
                    </Label>
                    <Textarea
                      id="agent-description"
                      placeholder="Describe what this agent does and its capabilities..."
                      value={agentDescription}
                      onChange={(e) => setAgentDescription(e.target.value)}
                      rows={4}
                      className="bg-neutral-950 border-neutral-800 text-white resize-none"
                    />
                  </div>
                  <div>
                    <Label htmlFor="sop" className="text-white mb-2">
                      SOP (Statement of Purpose)
                    </Label>
                    <Textarea
                      id="sop"
                      placeholder="Define the standard operating procedures and guidelines for this agent..."
                      value={sop}
                      onChange={(e) => setSop(e.target.value)}
                      rows={4}
                      className="bg-neutral-950 border-neutral-800 text-white resize-y"
                    />
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                      <Checkbox
                        id="human-in-loop"
                        checked={humanInLoop}
                        onCheckedChange={(checked) => setHumanInLoop(checked as boolean)}
                        className="border-neutral-700 data-[state=checked]:bg-accent data-[state=checked]:border-accent"
                      />
                      <Label htmlFor="human-in-loop" className="text-white cursor-pointer flex items-center gap-2">
                        Human in Loop <span className="text-xl">👤</span>
                      </Label>
                    </div>
                    {humanInLoop && (
                      <div className="ml-8 animate-in fade-in slide-in-from-top-2 duration-300">
                        <Textarea
                          placeholder="In what scenarios you want the agent to include Human in loop..."
                          value={humanInLoopScenarios}
                          onChange={(e) => setHumanInLoopScenarios(e.target.value)}
                          rows={3}
                          className="bg-neutral-950 border-neutral-800 text-white resize-y"
                        />
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            )}

            {currentStep === "knowledge-base" && (
              <Card className="bg-neutral-900 border-neutral-800 p-6">
                <h2 className="text-xl font-semibold text-white mb-2">Knowledge Base</h2>
                <p className="text-neutral-400 text-sm mb-6">
                  Upload folders to provide context for your agent. Add descriptions at each level.
                </p>

                <div className="mb-6">
                  <input
                    ref={folderInputRef}
                    type="file"
                    // @ts-ignore - webkitdirectory is not in the types but is supported
                    webkitdirectory=""
                    directory=""
                    multiple
                    onChange={handleFolderUpload}
                    className="hidden"
                  />
                  <Button
                    onClick={() => folderInputRef.current?.click()}
                    className="w-full bg-accent hover:bg-accent/90 text-white"
                  >
                    <IconFolder className="h-5 w-5 mr-2" />
                    Upload Folder
                  </Button>
                </div>

                {fileTree.length > 0 && (
                  <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-white mb-4">Uploaded Files & Folders</h3>
                    <TreeProvider defaultExpandedIds={fileTree.map((n) => n.id)}>
                      <TreeView className="text-sm">{renderTree(fileTree)}</TreeView>
                    </TreeProvider>
                  </div>
                )}
              </Card>
            )}

            {currentStep === "mode" && (
              <div className="space-y-6">
                <Card className="bg-neutral-900 border-neutral-800 p-6">
                  <h2 className="text-xl font-semibold text-white mb-2">Select Agent Mode</h2>
                  <p className="text-neutral-400 text-sm mb-6">Choose how your agent will interact with users.</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Voice Mode */}
                    <button
                      onClick={() => {
                        setSelectedMode("voice")
                        setShowVoicePersonality(true)
                      }}
                      className={cn(
                        "p-8 rounded-lg border-2 transition-all text-left",
                        selectedMode === "voice"
                          ? "border-accent bg-accent/10"
                          : "border-neutral-700 hover:border-neutral-600",
                      )}
                    >
                      <div className="flex items-center justify-center h-16 w-16 rounded-full bg-neutral-800 mb-4">
                        <IconMicrophone className="h-8 w-8 text-accent" />
                      </div>
                      <h3 className="text-lg font-semibold text-white mb-2">Voice Mode</h3>
                      <p className="text-neutral-400 text-sm">
                        Real-time voice conversations using AWS Nova Sonic for natural speech interactions.
                      </p>
                    </button>

                    {/* Conversational Mode */}
                    <button
                      onClick={() => {
                        setSelectedMode("conversational")
                        setShowVoicePersonality(false)
                      }}
                      className={cn(
                        "p-8 rounded-lg border-2 transition-all text-left",
                        selectedMode === "conversational"
                          ? "border-accent bg-accent/10"
                          : "border-neutral-700 hover:border-neutral-600",
                      )}
                    >
                      <div className="flex items-center justify-center h-16 w-16 rounded-full bg-neutral-800 mb-4">
                        <IconMessage className="h-8 w-8 text-accent" />
                      </div>
                      <h3 className="text-lg font-semibold text-white mb-2">Conversational Mode</h3>
                      <p className="text-neutral-400 text-sm">
                        Text-based conversations powered by Claude for intelligent chat interactions.
                      </p>
                    </button>
                  </div>
                </Card>

                {/* Voice Personality Section - Collapsible */}
                {selectedMode === "voice" && showVoicePersonality && (
                  <Card className="bg-neutral-900 border-neutral-800 p-6 animate-in fade-in slide-in-from-top-2 duration-300">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">Voice Personality (Optional)</h3>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowVoicePersonality(false)}
                        className="text-neutral-400 hover:text-white"
                      >
                        <IconX className="h-4 w-4" />
                      </Button>
                    </div>
                    <p className="text-neutral-400 text-sm mb-4">
                      Define how your voice agent should sound and behave during conversations.
                    </p>
                    
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="voice-personality" className="text-white mb-2">
                          Personality Instructions
                        </Label>
                        <Textarea
                          id="voice-personality"
                          placeholder="Describe the voice personality..."
                          value={voicePersonality}
                          onChange={(e) => setVoicePersonality(e.target.value)}
                          rows={6}
                          className="bg-neutral-950 border-neutral-800 text-white resize-y"
                        />
                      </div>
                      
                      {/* Example */}
                      <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-4">
                        <p className="text-xs font-semibold text-accent mb-2">Example:</p>
                        <p className="text-xs text-neutral-400 leading-relaxed">
                          "You are Sarah, a friendly and empathetic customer service representative. Speak in a warm, 
                          conversational tone with moderate pacing. Use occasional filler words like 'um' to sound natural. 
                          Be patient and understanding when customers are frustrated."
                        </p>
                      </div>
                    </div>
                  </Card>
                )}

                {!showVoicePersonality && selectedMode === "voice" && (
                  <Button
                    variant="outline"
                    onClick={() => setShowVoicePersonality(true)}
                    className="w-full border-neutral-700 text-white hover:bg-neutral-800 bg-transparent"
                  >
                    Add Voice Personality
                  </Button>
                )}
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 mt-6">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between mt-8">
              <Button
                variant="outline"
                onClick={handleBack}
                disabled={currentStep === "description" || isSubmitting}
                className="border-neutral-700 text-white hover:bg-neutral-800 bg-transparent"
              >
                Back
              </Button>
              {currentStep === "mode" ? (
                <Button
                  onClick={handleCreate}
                  disabled={!canProceed() || isSubmitting}
                  className="bg-accent hover:bg-accent/90 text-white"
                >
                  {isSubmitting ? "Creating..." : "Create Agent"}
                </Button>
              ) : (
                <Button
                  onClick={handleNext}
                  disabled={!canProceed()}
                  className="bg-accent hover:bg-accent/90 text-white"
                >
                  Next
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
