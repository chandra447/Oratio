"use client"

import { Button } from "@/components/ui/button"
import { ArrowRight, Sparkles } from "lucide-react"
import { motion } from "framer-motion"
import { WavyBackground } from "@/components/ui/wavy-background"

export function HeroSection() {
  return (
    <WavyBackground
      className="mx-auto max-w-7xl"
      containerClassName="relative overflow-hidden border-b border-border/40"
      colors={["#3b82f6", "#2563eb", "#1d4ed8", "#1e40af", "#60a5fa"]}
      waveWidth={50}
      backgroundFill="black"
      blur={10}
      speed="fast"
      waveOpacity={0.5}
    >
      <div className="container relative mx-auto px-4 py-20 md:px-6 md:py-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mx-auto max-w-4xl text-center"
        >
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-4 py-1.5 text-sm">
            <Sparkles className="h-3.5 w-3.5 text-accent" />
            <span className="text-accent-foreground">Powered by AWS Bedrock & AgentCore</span>
          </div>

          <h1 className="mb-6 text-balance font-sans text-5xl font-bold leading-tight tracking-tight md:text-6xl lg:text-7xl">
            Build voice AI agents without writing code
          </h1>

          <p className="mb-10 text-pretty text-lg text-muted-foreground md:text-xl">
            Enterprise-grade platform for creating, deploying, and managing conversational AI agents. Leverage AWS Nova
            Sonic for voice and Claude for intelligence—all through an intuitive no-code interface.
          </p>

          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button size="lg" className="group w-full bg-accent text-accent-foreground hover:bg-accent/90 sm:w-auto">
              Start Building
              <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Button>
            <Button size="lg" variant="outline" className="w-full border-border bg-transparent sm:w-auto">
              View Demo
            </Button>
          </div>

      
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mx-auto mt-4 max-w-5xl"
        >
          <div className="relative rounded-xl border border-border bg-card/50 p-2 shadow-2xl backdrop-blur">
            <img src="dashboard.png" alt="Oratio Dashboard - Manage AI Agents" className="w-full rounded-lg" />
          </div>
        </motion.div>
      </div>
    </WavyBackground>
  )
}
