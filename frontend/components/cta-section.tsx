"use client"

import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"
import { AnimatedWaves } from "./animated-waves"

export function CTASection() {
  return (
    <section className="relative border-b border-border/40 bg-accent py-20 text-accent-foreground md:py-32">
      <AnimatedWaves />

      <div className="container relative mx-auto px-4 md:px-6">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="mb-6 text-balance text-3xl font-bold tracking-tight md:text-4xl lg:text-5xl">
            Ready to build your AI agents?
          </h2>
          <p className="mb-10 text-pretty text-lg text-accent-foreground/90">
            Join enterprise teams already using Oratio to deploy intelligent voice and conversational AI agents. Start
            your free trial today—no credit card required.
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button size="lg" variant="secondary" className="group w-full sm:w-auto">
              Get Started Free
              <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="w-full border-accent-foreground/20 bg-transparent text-accent-foreground hover:bg-accent-foreground/10 sm:w-auto"
            >
              Schedule a Demo
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}
