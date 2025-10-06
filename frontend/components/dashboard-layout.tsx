"use client"
import type React from "react"
import { useState } from "react"
import { Sidebar, SidebarBody, SidebarLink } from "@/components/ui/sidebar"
import { IconRobot, IconDatabase, IconKey, IconLogout, IconMicrophone } from "@tabler/icons-react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import Link from "next/link"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const links = [
    {
      label: "Agents",
      href: "/dashboard/agents",
      icon: <IconRobot className="h-5 w-5 shrink-0 text-neutral-200" />,
    },
    {
      label: "Knowledge Base",
      href: "/dashboard/knowledge-base",
      icon: <IconDatabase className="h-5 w-5 shrink-0 text-neutral-200" />,
    },
    {
      label: "API Keys",
      href: "/dashboard/api-keys",
      icon: <IconKey className="h-5 w-5 shrink-0 text-neutral-200" />,
    },
    {
      label: "Logout",
      href: "/",
      icon: <IconLogout className="h-5 w-5 shrink-0 text-neutral-200" />,
    },
  ]
  const [open, setOpen] = useState(false)

  return (
    <div className={cn("flex w-full h-screen overflow-hidden bg-black")}>
      <Sidebar open={open} setOpen={setOpen}>
        <SidebarBody className="justify-between gap-10">
          <div className="flex flex-1 flex-col overflow-x-hidden overflow-y-auto">
            {open ? <Logo /> : <LogoIcon />}
            <div className="mt-8 flex flex-col gap-2">
              {links.map((link, idx) => (
                <SidebarLink key={idx} link={link} />
              ))}
            </div>
          </div>
        </SidebarBody>
      </Sidebar>
      <div className="flex flex-1 overflow-auto">
        <div className="flex h-full w-full flex-1 flex-col bg-black">{children}</div>
      </div>
    </div>
  )
}

export const Logo = () => {
  return (
    <Link href="/dashboard/agents" className="relative z-20 flex items-center space-x-2 py-1 text-sm font-normal">
      <div className="h-8 w-8 shrink-0 rounded-full bg-accent flex items-center justify-center">
        <IconMicrophone className="h-5 w-5 text-white" />
      </div>
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="font-semibold text-xl whitespace-pre text-white"
      >
        Oratio
      </motion.span>
    </Link>
  )
}

export const LogoIcon = () => {
  return (
    <Link href="/dashboard/agents" className="relative z-20 flex items-center space-x-2 py-1">
      <div className="h-8 w-8 shrink-0 rounded-full bg-accent flex items-center justify-center">
        <IconMicrophone className="h-5 w-5 text-white" />
      </div>
    </Link>
  )
}
