"use client";

/**
 * @author: @dorian_baffier
 * @description: Typewriter
 * @version: 1.0.0
 * @date: 2025-06-26
 * @license: MIT
 * @website: https://kokonutui.com
 * @github: https://github.com/kokonut-labs/kokonutui
 */

import { motion, useAnimate } from "motion/react";
import { useEffect } from "react";

interface TypewriterSequence {
  text: string;
  deleteAfter?: boolean;
  pauseAfter?: number;
}

interface TypewriterTitleProps {
  sequences?: TypewriterSequence[];
  typingSpeed?: number;
  startDelay?: number;
  autoLoop?: boolean;
  loopDelay?: number;
}

export default function TypewriterTitle({
  sequences = [
    { text: "Typewriter", deleteAfter: true },
    { text: "Multiple Words", deleteAfter: true },
    { text: "Auto Loop", deleteAfter: false },
  ],
  typingSpeed = 50,
  startDelay = 500,
  autoLoop = true,
  loopDelay = 2000,
}: TypewriterTitleProps) {
  const [scope, animate] = useAnimate();

  useEffect(() => {
    let isActive = true;

    const typeText = async () => {
      const titleElement = scope.current.querySelector("[data-typewriter]");
      if (!titleElement) return;

      while (isActive) {
        // Reset the text content
        await animate(scope.current, { opacity: 1 });
        titleElement.textContent = "";

        // Wait for initial delay on first run
        await new Promise((resolve) => setTimeout(resolve, startDelay));

        // Process each sequence
        for (const sequence of sequences) {
          if (!isActive) break;

          // Type out the sequence text
          for (let i = 0; i < sequence.text.length; i++) {
            if (!isActive) break;
            titleElement.textContent = sequence.text.slice(0, i + 1);
            await new Promise((resolve) => setTimeout(resolve, typingSpeed));
          }

          // Pause after typing if specified
          if (sequence.pauseAfter) {
            await new Promise((resolve) =>
              setTimeout(resolve, sequence.pauseAfter)
            );
          }

          // Delete the text if specified
          if (sequence.deleteAfter) {
            // Small pause before deleting
            await new Promise((resolve) => setTimeout(resolve, 500));

            for (let i = sequence.text.length; i > 0; i--) {
              if (!isActive) break;
              titleElement.textContent = sequence.text.slice(0, i);
              await new Promise((resolve) =>
                setTimeout(resolve, typingSpeed / 2)
              );
            }
          }
        }

        if (!(autoLoop && isActive)) break;

        // Wait before starting next loop
        await new Promise((resolve) => setTimeout(resolve, loopDelay));
      }
    };

    typeText();

    // Cleanup function to stop the animation when component unmounts
    return () => {
      isActive = false;
    };
  }, [sequences, typingSpeed, startDelay, autoLoop, loopDelay, animate, scope]);

  return (
    <div className="relative mx-auto w-full max-w-4xl py-24">
      <div
        className="relative z-10 flex flex-col items-center justify-center text-center"
        ref={scope}
      >
        <motion.div
          animate={{ opacity: 1 }}
          className="flex items-center gap-2 font-mono text-4xl text-black tracking-tight md:text-6xl dark:text-white"
          initial={{ opacity: 0 }}
        >
          <span
            className="inline-block animate-cursor border-black border-r-2 pr-1 dark:border-white"
            data-typewriter
          >
            {sequences[0].text}
          </span>
        </motion.div>
      </div>
    </div>
  );
}
