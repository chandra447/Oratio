"use client"

import { useRef } from "react"
import { motion, useScroll, useTransform } from "framer-motion"

export function AnimatedWaves() {
  const containerRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  })

  const y1 = useTransform(scrollYProgress, [0, 1], [0, -100])
  const y2 = useTransform(scrollYProgress, [0, 1], [0, -150])
  const y3 = useTransform(scrollYProgress, [0, 1], [0, -200])

  return (
    <div ref={containerRef} className="pointer-events-none absolute inset-0 overflow-hidden">
      <motion.div style={{ y: y1 }} className="absolute left-0 top-1/4 h-px w-full">
        <svg className="h-24 w-full" viewBox="0 0 1200 100" preserveAspectRatio="none">
          <path d="M0,50 Q300,20 600,50 T1200,50" fill="none" stroke="rgba(59, 130, 246, 0.2)" strokeWidth="2" />
        </svg>
      </motion.div>

      <motion.div style={{ y: y2 }} className="absolute left-0 top-1/2 h-px w-full">
        <svg className="h-32 w-full" viewBox="0 0 1200 100" preserveAspectRatio="none">
          <path d="M0,50 Q300,80 600,50 T1200,50" fill="none" stroke="rgba(59, 130, 246, 0.15)" strokeWidth="2" />
        </svg>
      </motion.div>

      <motion.div style={{ y: y3 }} className="absolute left-0 top-3/4 h-px w-full">
        <svg className="h-28 w-full" viewBox="0 0 1200 100" preserveAspectRatio="none">
          <path d="M0,50 Q300,30 600,50 T1200,50" fill="none" stroke="rgba(59, 130, 246, 0.1)" strokeWidth="2" />
        </svg>
      </motion.div>
    </div>
  )
}
