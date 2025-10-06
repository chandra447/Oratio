"use client"

import { Bot, Zap, Activity, Code2, Database, Shield } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { AnimatedWaves } from "./animated-waves"

const features = [
  {
    icon: Bot,
    title: "No-Code Agent Builder",
    description:
      "Create sophisticated voice and conversational AI agents without writing a single line of code. Upload your SOPs and knowledge bases, and let Oratio handle the rest.",
  },
  {
    icon: Zap,
    title: "Instant Deployment",
    description:
      "Deploy your AI agents to production in minutes with AWS AgentCore. Get REST API and WebSocket endpoints automatically configured for seamless integration.",
  },
  {
    icon: Activity,
    title: "Real-Time Monitoring",
    description:
      "Monitor live conversations with comprehensive dashboards. Track performance metrics, conversation quality, and user interactions in real-time.",
  },
  {
    icon: Code2,
    title: "Multi-Modal AI",
    description:
      "Leverage AWS Bedrock's Nova Sonic for natural voice interactions and Claude for intelligent text processing. Switch seamlessly between voice and text modes.",
  },
  {
    icon: Database,
    title: "Knowledge Management",
    description:
      "Upload and manage your organization's knowledge bases and SOPs. Oratio automatically indexes and retrieves relevant information for your agents.",
  },
  {
    icon: Shield,
    title: "Enterprise Security",
    description:
      "Multi-tenant architecture with enterprise-grade security. Infrastructure built on AWS with data isolation and encryption at rest and in transit.",
  },
]

export function FeaturesSection() {
  return (
    <section id="features" className="relative border-b border-border/40 bg-background py-20 md:py-32">
      <AnimatedWaves />

      <div className="container relative mx-auto px-4 md:px-6">
        <div className="mx-auto mb-16 max-w-3xl text-center">
          <h2 className="mb-4 text-balance text-3xl font-bold tracking-tight md:text-4xl lg:text-5xl">
            Everything you need to build AI agents
          </h2>
          <p className="text-pretty text-lg text-muted-foreground">
            Enterprise-grade features designed for teams building the future of conversational AI.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <Card
              key={index}
              className="border-border/50 bg-card transition-all hover:border-accent/50 hover:shadow-lg hover:shadow-accent/5"
            >
              <CardContent className="p-6">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-accent/10">
                  <feature.icon className="h-6 w-6 text-accent" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">{feature.title}</h3>
                <p className="text-pretty leading-relaxed text-muted-foreground">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
