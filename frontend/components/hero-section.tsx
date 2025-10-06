"use client"

import { Button } from "@/components/ui/button"
import { ArrowRight, Sparkles } from "lucide-react"
import { motion } from "framer-motion"
import { useEffect, useRef } from "react"

export function HeroSection() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = canvas.offsetWidth * window.devicePixelRatio
      canvas.height = canvas.offsetHeight * window.devicePixelRatio
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
    }
    resizeCanvas()
    window.addEventListener("resize", resizeCanvas)

    // Wave animation
    let animationFrameId: number
    let time = 0

    const drawWave = (offset: number, amplitude: number, frequency: number, opacity: number) => {
      ctx.beginPath()
      const width = canvas.offsetWidth
      const height = canvas.offsetHeight
      const centerY = height / 2

      for (let x = 0; x < width; x++) {
        const y = centerY + Math.sin((x * frequency + time + offset) * 0.01) * amplitude
        if (x === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      }

      ctx.strokeStyle = `rgba(59, 130, 246, ${opacity})`
      ctx.lineWidth = 2
      ctx.stroke()
    }

    const animate = () => {
      ctx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight)

      // Draw multiple waves with different properties
      drawWave(0, 20, 0.5, 0.3)
      drawWave(100, 30, 0.7, 0.2)
      drawWave(200, 25, 0.6, 0.25)

      time += 2
      animationFrameId = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      window.removeEventListener("resize", resizeCanvas)
      cancelAnimationFrame(animationFrameId)
    }
  }, [])

  return (
    <section className="relative overflow-hidden border-b border-border/40 bg-background py-20 md:py-32">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>

      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full opacity-40" />

      <div className="container relative mx-auto px-4 md:px-6">
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

          <p className="mt-6 text-sm text-muted-foreground">
            No credit card required • Deploy in minutes • Enterprise support available
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mx-auto mt-16 max-w-5xl"
        >
          <div className="relative rounded-xl border border-border bg-card/50 p-2 shadow-2xl backdrop-blur">
            <img src="dashboard.png" alt="Oratio Dashboard - Manage AI Agents" className="w-full rounded-lg" />
          </div>
        </motion.div>
      </div>
    </section>
  )
}
