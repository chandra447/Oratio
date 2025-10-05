# Frontend Design System

## Overview

Oratio's frontend uses **shadcn/ui** components built on **Radix UI** primitives with **Tailwind CSS** for styling. This provides a consistent, accessible, and elegant user experience that matches our brand identity as a premium AI platform.

## Technology Stack

### shadcn/ui
**Documentation**: https://ui.shadcn.com/

shadcn/ui is a collection of re-usable components built using Radix UI and Tailwind CSS. Components are copied into your project, giving you full control and customization.

**Installation**:
```bash
npx shadcn@latest init
```

**Adding Components**:
```bash
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add dialog
npx shadcn@latest add form
npx shadcn@latest add table
```

### Core Technologies
- **Next.js 14**: App Router with React Server Components
- **TypeScript**: Type-safe component development
- **Tailwind CSS**: Utility-first styling
- **Radix UI**: Accessible component primitives
- **React Hook Form**: Form state management
- **Zod**: Schema validation

## Design Principles

### Brand Identity
**Personality**: Confident, elegant, forward-thinking - a luxury audio product rather than a typical chatbot builder.

**Visual Language**:
- Clean, spacious layouts with generous whitespace
- Sophisticated color palette with subtle gradients
- Smooth animations and transitions
- Premium typography
- Conversational, empathetic tone

### Color Palette

```css
/* Primary Colors */
--primary: 222.2 47.4% 11.2%;        /* Deep charcoal */
--primary-foreground: 210 40% 98%;   /* Off-white */

/* Secondary Colors */
--secondary: 210 40% 96.1%;          /* Light gray */
--secondary-foreground: 222.2 47.4% 11.2%;

/* Accent Colors */
--accent: 210 40% 96.1%;
--accent-foreground: 222.2 47.4% 11.2%;

/* Semantic Colors */
--destructive: 0 84.2% 60.2%;        /* Red for errors */
--success: 142 76% 36%;              /* Green for success */
--warning: 38 92% 50%;               /* Amber for warnings */

/* Background */
--background: 0 0% 100%;             /* White */
--foreground: 222.2 84% 4.9%;        /* Near black */

/* Muted */
--muted: 210 40% 96.1%;
--muted-foreground: 215.4 16.3% 46.9%;

/* Border */
--border: 214.3 31.8% 91.4%;
--input: 214.3 31.8% 91.4%;
--ring: 222.2 84% 4.9%;
```

### Typography

```css
/* Font Family */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Font Sizes */
--text-xs: 0.75rem;      /* 12px */
--text-sm: 0.875rem;     /* 14px */
--text-base: 1rem;       /* 16px */
--text-lg: 1.125rem;     /* 18px */
--text-xl: 1.25rem;      /* 20px */
--text-2xl: 1.5rem;      /* 24px */
--text-3xl: 1.875rem;    /* 30px */
--text-4xl: 2.25rem;     /* 36px */
```

## Component Library

### Essential Components to Install

```bash
# Layout & Navigation
npx shadcn@latest add sidebar
npx shadcn@latest add navigation-menu
npx shadcn@latest add breadcrumb

# Forms & Inputs
npx shadcn@latest add form
npx shadcn@latest add input
npx shadcn@latest add textarea
npx shadcn@latest add select
npx shadcn@latest add checkbox
npx shadcn@latest add radio-group
npx shadcn@latest add switch
npx shadcn@latest add label

# Data Display
npx shadcn@latest add table
npx shadcn@latest add card
npx shadcn@latest add badge
npx shadcn@latest add avatar
npx shadcn@latest add separator

# Feedback
npx shadcn@latest add alert
npx shadcn@latest add toast
npx shadcn@latest add progress
npx shadcn@latest add skeleton

# Overlays
npx shadcn@latest add dialog
npx shadcn@latest add sheet
npx shadcn@latest add popover
npx shadcn@latest add dropdown-menu
npx shadcn@latest add tooltip

# Buttons & Actions
npx shadcn@latest add button
npx shadcn@latest add scroll-area

# File Upload
npx shadcn@latest add file-upload
```

## Page-Specific Component Usage

### Authentication Pages

**Login/Register Forms**:
```tsx
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"

<Card className="w-full max-w-md">
  <CardHeader>
    <CardTitle>Welcome to Oratio</CardTitle>
    <CardDescription>Sign in to manage your AI agents</CardDescription>
  </CardHeader>
  <CardContent>
    <form>
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" placeholder="you@company.com" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" />
        </div>
      </div>
    </form>
  </CardContent>
  <CardFooter>
    <Button className="w-full">Sign In</Button>
  </CardFooter>
</Card>
```

### Dashboard Layout

**Sidebar Navigation**:
```tsx
import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar"
import { Bot, MessageSquare, Bell, Key, BarChart } from "lucide-react"

<Sidebar>
  <SidebarContent>
    <SidebarGroup>
      <SidebarGroupLabel>Platform</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild>
              <a href="/agents">
                <Bot className="mr-2 h-4 w-4" />
                <span>Agents</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild>
              <a href="/sessions/live">
                <MessageSquare className="mr-2 h-4 w-4" />
                <span>Live Sessions</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  </SidebarContent>
</Sidebar>
```

### Agent Creation Wizard

**Multi-Step Form**:
```tsx
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { FileUpload } from "@/components/ui/file-upload"

<div className="space-y-6">
  <Progress value={33} className="w-full" />
  
  <Card>
    <CardHeader>
      <CardTitle>Create Your AI Agent</CardTitle>
      <CardDescription>Step 1: Basic Information</CardDescription>
    </CardHeader>
    <CardContent className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="agent-name">Agent Name</Label>
        <Input id="agent-name" placeholder="Customer Service Agent" />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="sop">Standard Operating Procedure</Label>
        <Textarea 
          id="sop" 
          placeholder="Describe how your agent should behave..."
          rows={8}
        />
      </div>
      
      <div className="space-y-2">
        <Label>Knowledge Base Documents</Label>
        <FileUpload 
          accept=".pdf,.md,.txt"
          multiple
          onUpload={handleFileUpload}
        />
      </div>
    </CardContent>
  </Card>
  
  <div className="flex justify-between">
    <Button variant="outline">Back</Button>
    <Button>Next Step</Button>
  </div>
</div>
```

### Agent List View

**Data Table**:
```tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { MoreHorizontal } from "lucide-react"

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>Type</TableHead>
      <TableHead>Status</TableHead>
      <TableHead>Created</TableHead>
      <TableHead className="text-right">Actions</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {agents.map((agent) => (
      <TableRow key={agent.id}>
        <TableCell className="font-medium">{agent.name}</TableCell>
        <TableCell>
          <Badge variant="outline">{agent.type}</Badge>
        </TableCell>
        <TableCell>
          <Badge variant={agent.status === 'active' ? 'success' : 'secondary'}>
            {agent.status}
          </Badge>
        </TableCell>
        <TableCell>{agent.createdAt}</TableCell>
        <TableCell className="text-right">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>View Details</DropdownMenuItem>
              <DropdownMenuItem>Edit Configuration</DropdownMenuItem>
              <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

### Live Sessions Dashboard

**Real-Time Session Cards**:
```tsx
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"

<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
  {sessions.map((session) => (
    <Card key={session.id} className="cursor-pointer hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{session.agentName}</CardTitle>
          <Badge variant={session.type === 'voice' ? 'default' : 'secondary'}>
            {session.type}
          </Badge>
        </div>
        <CardDescription>
          Duration: {session.duration} • {session.messageCount} messages
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Avatar className="h-8 w-8">
              <AvatarFallback>CU</AvatarFallback>
            </Avatar>
            <div className="text-sm">
              <p className="font-medium">Customer</p>
              <p className="text-muted-foreground">{session.customerInfo}</p>
            </div>
          </div>
          <Separator />
          <ScrollArea className="h-20">
            <p className="text-sm text-muted-foreground">
              {session.lastMessage}
            </p>
          </ScrollArea>
        </div>
      </CardContent>
    </Card>
  ))}
</div>
```

### Notification Center

**Alert System**:
```tsx
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Bell, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"

<div className="space-y-4">
  {notifications.map((notification) => (
    <Alert key={notification.id} variant={notification.priority === 'high' ? 'destructive' : 'default'}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Human Handoff Requested</AlertTitle>
      <AlertDescription className="flex items-center justify-between">
        <span>{notification.message}</span>
        <Button size="sm" variant="outline">View Session</Button>
      </AlertDescription>
    </Alert>
  ))}
</div>
```

### Toast Notifications

**Real-Time Feedback**:
```tsx
import { useToast } from "@/components/ui/use-toast"

const { toast } = useToast()

// Success notification
toast({
  title: "Agent Created Successfully",
  description: "Your agent is now active and ready to handle conversations.",
  variant: "success",
})

// Error notification
toast({
  title: "Agent Creation Failed",
  description: "There was an error creating your agent. Please try again.",
  variant: "destructive",
})

// Info notification
toast({
  title: "New Session Started",
  description: "A customer has connected to your agent.",
})
```

## Layout Patterns

### Dashboard Layout
```tsx
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"

export default function DashboardLayout({ children }) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          {/* Header content */}
        </header>
        <main className="flex flex-1 flex-col gap-4 p-4">
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
```

### Modal Dialogs
```tsx
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"

<Dialog>
  <DialogTrigger asChild>
    <Button>Delete Agent</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Are you sure?</DialogTitle>
      <DialogDescription>
        This action cannot be undone. This will permanently delete your agent
        and all associated data.
      </DialogDescription>
    </DialogHeader>
    <DialogFooter>
      <Button variant="outline">Cancel</Button>
      <Button variant="destructive">Delete</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

## Animation & Transitions

Use Tailwind's transition utilities for smooth interactions:

```tsx
// Hover effects
<Card className="transition-shadow hover:shadow-lg">

// Loading states
<Skeleton className="h-12 w-full" />

// Fade in animations
<div className="animate-in fade-in-50 duration-500">

// Slide in animations
<div className="animate-in slide-in-from-bottom-4 duration-300">
```

## Accessibility Guidelines

- Always use semantic HTML elements
- Include proper ARIA labels and descriptions
- Ensure keyboard navigation works for all interactive elements
- Maintain sufficient color contrast (WCAG AA minimum)
- Use focus indicators for keyboard users
- Provide alternative text for images and icons
- Test with screen readers

## Development Guidelines

1. **Component Organization**: Keep components in `components/ui/` for shadcn components and `components/` for custom components
2. **Styling**: Use Tailwind utility classes, avoid custom CSS when possible
3. **Consistency**: Reuse shadcn components across the application
4. **Responsiveness**: Design mobile-first, use Tailwind's responsive modifiers
5. **Dark Mode**: Consider dark mode support using Tailwind's dark: modifier
6. **Performance**: Use React Server Components where possible, lazy load heavy components

## Resources

- **shadcn/ui Documentation**: https://ui.shadcn.com/
- **Radix UI Primitives**: https://www.radix-ui.com/
- **Tailwind CSS**: https://tailwindcss.com/
- **Lucide Icons**: https://lucide.dev/ (recommended icon library)
- **Next.js App Router**: https://nextjs.org/docs/app
