"use client"
import type React from "react"
import { IconRobot, IconDatabase, IconKey, IconLogout } from "@tabler/icons-react"
import { cn } from "@/lib/utils"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { MicSparklesIcon } from "@/components/ui/mic-sparkles-icon"
import { useAuth } from "@/lib/auth/auth-context"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const { logout } = useAuth()
  
  const links = [
    {
      label: "Agents",
      href: "/dashboard/agents",
      icon: IconRobot,
    },
    {
      label: "Knowledge Base",
      href: "/dashboard/knowledge-base",
      icon: IconDatabase,
    },
    {
      label: "API Keys",
      href: "/dashboard/api-keys",
      icon: IconKey,
    },
    {
      label: "Logout",
      href: "#",
      icon: IconLogout,
      action: logout,
    },
  ]

  const isActive = (href: string) => {
    if (href === "/dashboard/agents") {
      return pathname.startsWith("/dashboard/agents")
    }
    return pathname === href
  }

  return (
    <div className="flex w-full h-screen overflow-hidden bg-neutral-950">
      {/* Compact Sidebar */}
      <aside className="w-16 bg-neutral-900/50 border-r border-neutral-800/50 flex flex-col items-center py-6 gap-6 shrink-0 relative z-10">
        {/* Logo */}
        <Link href="/dashboard/agents" className="group">
          <div className="h-10 w-10 shrink-0 rounded-xl bg-accent flex items-center justify-center relative transition-transform hover:scale-105">
            <MicSparklesIcon size={40} className="text-white" />
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="flex flex-col gap-3 flex-1">
          {links.map((link, idx) => {
            const Icon = link.icon
            const active = isActive(link.href)
            
            if (link.action) {
              // For logout button
              return (
                <button
                  key={idx}
                  onClick={link.action}
                  className={cn(
                    "h-10 w-10 rounded-xl flex items-center justify-center transition-all group relative",
                    "text-neutral-400 hover:text-white hover:bg-neutral-800/50"
                  )}
                  title={link.label}
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  {/* Tooltip */}
                  <span className="absolute left-14 px-2 py-1 bg-neutral-800 text-white text-xs rounded-md whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
                    {link.label}
                  </span>
                </button>
              )
            }
            
            return (
              <Link
                key={idx}
                href={link.href}
                className={cn(
                  "h-10 w-10 rounded-xl flex items-center justify-center transition-all group relative",
                  active
                    ? "bg-accent text-white"
                    : "text-neutral-400 hover:text-white hover:bg-neutral-800/50"
                )}
                title={link.label}
              >
                <Icon className="h-5 w-5 shrink-0" />
                {/* Tooltip */}
                <span className="absolute left-14 px-2 py-1 bg-neutral-800 text-white text-xs rounded-md whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
                  {link.label}
                </span>
              </Link>
            )
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex flex-1 overflow-auto relative z-0">
        <div className="flex h-full w-full flex-1 flex-col bg-neutral-950">{children}</div>
      </main>
    </div>
  )
}

