# Oratio Frontend Development Guidelines

## Project Context

Building Oratio voice agent platform frontend using Next.js 15, React 19, shadcn/ui, and Tailwind CSS. The frontend communicates with a FastAPI backend for all data operations.

## Code Style and Structure

### General Principles

- Write clear, concise TypeScript code with functional and declarative patterns
- Follow DRY (Don't Repeat Yourself) principle
- Use early returns to enhance readability
- Organize components: exports → subcomponents → helpers → types
- Prefer named exports for components

### Naming Conventions

- Use descriptive names with auxiliary verbs: `isLoading`, `hasError`, `canSubmit`
- Prefix event handlers with "handle": `handleClick`, `handleSubmit`, `handleVoiceInput`
- Use lowercase with hyphens for directories: `components/voice-agent`, `lib/oratio-config`
- Use PascalCase for component files: `VoiceAgentCard.tsx`, `AudioWaveform.tsx`

### TypeScript Best Practices

- Use TypeScript for all code - no JavaScript files
- Prefer `interface` over `type` for object shapes
- Avoid enums - use const objects with `as const` instead
- Ensure proper type safety and inference
- Use `satisfies` operator for type validation
- Define prop types inline or in separate interface

```typescript
// Good
interface VoiceAgentProps {
  agentId: string;
  isActive: boolean;
  onStatusChange: (status: AgentStatus) => void;
}

// Avoid enums
const AgentStatus = {
  IDLE: 'idle',
  LISTENING: 'listening',
  PROCESSING: 'processing',
  SPEAKING: 'speaking',
} as const;

type AgentStatus = typeof AgentStatus[keyof typeof AgentStatus];
```

## Next.js 15 & React 19 Best Practices

### Component Architecture

- **Prefer React Server Components (RSC)** by default - faster, smaller bundles
- Only use `'use client'` when absolutely necessary:
  - User interactions (onClick, onChange)
  - React hooks (useState, useEffect, useContext)
  - Browser APIs (localStorage, window)
  - Third-party libraries requiring client-side
- Implement proper error boundaries with `error.tsx`
- Use `loading.tsx` for loading states instead of manual spinners
- Optimize for Core Web Vitals (LCP, INP, CLS)

```typescript
// Server Component (default)
async function VoiceAgentList() {
  const agents = await fetchAgents(); // Direct API call
  return <div>{agents.map(agent => <AgentCard key={agent.id} agent={agent} />)}</div>;
}

// Client Component (only when needed)
'use client';
import { useState } from 'react';

function VoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  // Browser audio APIs require client-side
}
```

### Async Request APIs (Next.js 15)

Always await async props and request APIs:

```typescript
// Layout/Page components
export default async function Page(props: PageProps) {
  const params = await props.params;
  const searchParams = await props.searchParams;
  
  const cookieStore = await cookies();
  const headersList = await headers();
  const { isEnabled } = await draftMode();
}
```

### Data Fetching Strategies

- **Fetch requests are NOT cached by default in Next.js 15**
- Use explicit caching when needed:

```typescript
// Cached fetch
const data = await fetch('http://localhost:8000/api/agents', {
  cache: 'force-cache', // or 'no-store'
  next: { revalidate: 3600 } // Revalidate every hour
});

// Layout/page-level caching
export const fetchCache = 'default-cache';
export const dynamic = 'force-static'; // for static generation
```

### FastAPI Backend Integration

All data operations go through the FastAPI backend:

```typescript
// lib/api/client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchAgents(userId: string) {
  const response = await fetch(`${API_BASE_URL}/api/agents?userId=${userId}`, {
    headers: {
      'Authorization': `Bearer ${getToken()}`,
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch agents');
  }
  
  return response.json();
}

export async function createAgent(data: CreateAgentData) {
  const response = await fetch(`${API_BASE_URL}/api/agents`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getToken()}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    throw new Error('Failed to create agent');
  }
  
  return response.json();
}
```

### State Management

- Use `useActionState` (replaces deprecated `useFormState`)
- Implement URL state management using `nuqs` library
- Minimize client-side state - prefer server state
- Use `useOptimistic` for optimistic updates

```typescript
'use client';
import { useActionState } from 'react';
import { createVoiceAgent } from '@/lib/api/agents';

function AgentForm() {
  const [state, formAction, isPending] = useActionState(createVoiceAgent, null);
  
  return (
    <form action={formAction}>
      <input name="name" disabled={isPending} />
      {state?.error && <p className="text-destructive">{state.error}</p>}
    </form>
  );
}
```

## shadcn/ui Component Guidelines

### Component Customization Philosophy

- shadcn/ui components are **copied into your codebase** - you own the code
- Modify components directly in `components/ui/` when needed
- Don't wrap components unnecessarily - edit the source
- Keep custom variants in the component file using `cva`

### Installing Components

```bash
npx shadcn@latest add button card dialog
```

### Customizing Components

```typescript
// components/ui/button.tsx
import { cva, type VariantProps } from "class-variance-authority";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        // Add Oratio-specific variants
        oratio: "bg-gradient-to-r from-primary to-accent text-white hover:opacity-90 oratio-corner",
        voice: "bg-accent text-accent-foreground hover:bg-accent/80",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

// Use in components
<Button variant="oratio" size="lg">Start Voice Agent</Button>
```

### Component Organization

```
components/
├── ui/              # shadcn components (owned by you)
│   ├── button.tsx
│   ├── card.tsx
│   ├── dialog.tsx
│   └── ...
├── voice/           # Oratio-specific components
│   ├── VoiceAgentCard.tsx
│   ├── AudioWaveform.tsx
│   └── CallControls.tsx
└── layout/
    ├── Header.tsx
    └── Sidebar.tsx
```

### Using Composition Patterns

```typescript
// Prefer composition over creating wrapper components
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

function VoiceAgentCard({ agent }: { agent: VoiceAgent }) {
  return (
    <Card className="oratio-corner">
      <CardHeader>
        <CardTitle>{agent.name}</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Content */}
      </CardContent>
    </Card>
  );
}
```

## Styling with Tailwind CSS

### Oratio Design System

Use the custom Oratio classes defined in `globals.css`:

```tsx
// Oratio signature corners
<div className="oratio-corner bg-primary" />
<div className="oratio-corner-top-left bg-accent" />

// Oratio brand colors (from tailwind.config.ts)
<Button className="bg-primary text-primary-foreground" />
<Card className="bg-surface-light dark:bg-surface-dark" />

// Glow effects
<div className="shadow-glow" />

// Blob animations
<div className="animate-blob" />
<div className="animate-blob animation-delay-2000" />
```

### CSS Variables Best Practice

**IMPORTANT:** When working with CSS variables in `@layer base`, always use direct CSS properties instead of `@apply`:

```css
/* ❌ WRONG - Tailwind utilities aren't generated yet in base layer */
@layer base {
  body {
    @apply bg-background text-foreground;
  }
}

/* ✅ CORRECT - Use direct CSS properties */
@layer base {
  body {
    background-color: hsl(var(--background));
    color: hsl(var(--foreground));
  }
}
```

**Why:** Tailwind generates utility classes AFTER processing the base layer. Using `@apply` with utilities that reference CSS variables will fail because those utilities don't exist yet.

### Responsive Design

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Mobile: 1 col, Tablet: 2 cols, Desktop: 3 cols */}
</div>
```

### Dark Mode

```tsx
// Use CSS variables for automatic dark mode support
<div className="bg-background text-foreground" />
<Card className="bg-card text-card-foreground" />

// Or use dark: prefix
<div className="bg-white dark:bg-gray-900" />
```

## File Structure Best Practices

```
src/
├── app/                        # Next.js App Router
│   ├── (auth)/                 # Route groups
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/
│   │   ├── agents/
│   │   │   ├── page.tsx       # /agents
│   │   │   ├── [id]/
│   │   │   │   └── page.tsx   # /agents/:id
│   │   │   ├── loading.tsx
│   │   │   └── error.tsx
│   │   └── layout.tsx
│   ├── api/                    # API routes (use sparingly)
│   │   └── webhook/
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── components/
│   ├── ui/                     # shadcn components
│   ├── voice/                  # Domain components
│   └── layout/
├── lib/
│   ├── utils.ts               # cn() helper, utilities
│   ├── validations.ts         # Zod schemas
│   └── api/                   # FastAPI client wrappers
│       ├── client.ts
│       ├── agents.ts
│       └── sessions.ts
├── hooks/
│   ├── use-voice-recorder.ts
│   └── use-agent-status.ts
└── types/
    ├── voice-agent.ts
    └── api.ts
```

## Performance Optimization

### Image Optimization

```tsx
import Image from 'next/image';

<Image
  src="/oratio-logo.png"
  alt="Oratio Logo"
  width={200}
  height={60}
  priority // For above-the-fold images
  loading="lazy" // For below-the-fold
/>
```

### Dynamic Imports (Code Splitting)

```typescript
import dynamic from 'next/dynamic';

// Load heavy components only when needed
const AudioWaveform = dynamic(() => import('@/components/voice/AudioWaveform'), {
  loading: () => <div>Loading waveform...</div>,
  ssr: false, // Disable SSR if using browser APIs
});
```

### Avoid Premature Optimization

- Monitor first with Core Web Vitals
- Only use `useMemo` and `useCallback` when you have measured performance issues
- Profile before optimizing

## Error Handling

### Error Boundaries

```typescript
// app/dashboard/error.tsx
'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h2 className="text-2xl font-bold mb-4">Something went wrong!</h2>
      <p className="text-muted-foreground mb-4">{error.message}</p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
```

### API Error Handling

```typescript
// lib/api/client.ts
export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'API request failed');
    }

    return response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

## Security Best Practices

- Never expose API keys or secrets in client components
- Use environment variables: `process.env.NEXT_PUBLIC_API_URL`
- Validate all user inputs with Zod schemas
- Sanitize data before sending to backend
- Use HTTPS only in production
- Implement rate limiting on the backend
- Store JWT tokens securely (httpOnly cookies preferred)

```typescript
// lib/validations.ts
import { z } from 'zod';

export const createAgentSchema = z.object({
  name: z.string().min(3).max(50),
  phoneNumber: z.string().regex(/^\+?[1-9]\d{1,14}$/),
  voiceModel: z.enum(['nova-sonic', 'polly']),
});
```

## Testing (Future)

```typescript
// __tests__/components/VoiceAgentCard.test.tsx
import { render, screen } from '@testing-library/react';
import VoiceAgentCard from '@/components/voice/VoiceAgentCard';

describe('VoiceAgentCard', () => {
  it('renders agent name', () => {
    const agent = { id: '1', name: 'Test Agent', status: 'active' };
    render(<VoiceAgentCard agent={agent} />);
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
  });
});
```

## Common Anti-Patterns to Avoid

### ❌ Don't create wrapper components for shadcn/ui

```typescript
// Bad
function MyButton({ children }) {
  return <Button>{children}</Button>;
}
```

### ✅ Do modify shadcn components directly or use composition

```typescript
// Good
import { Button } from '@/components/ui/button';
<Button variant="oratio">{children}</Button>
```

### ❌ Don't use client components everywhere

```typescript
// Bad
'use client';
function AgentList() {
  const agents = useAgents(); // Could be server-fetched
}
```

### ✅ Do use server components for data fetching

```typescript
// Good
async function AgentList() {
  const agents = await fetchAgents();
  return <div>{agents.map(...)}</div>;
}
```

### ❌ Don't use @apply with CSS variables in @layer base

```css
/* Bad */
@layer base {
  body {
    @apply bg-background text-foreground;
  }
}
```

### ✅ Do use direct CSS properties

```css
/* Good */
@layer base {
  body {
    background-color: hsl(var(--background));
    color: hsl(var(--foreground));
  }
}
```

## Checklist for Every Component

- [ ] Is this a Server Component by default? (no 'use client')
- [ ] Are prop types defined with TypeScript?
- [ ] Are error states handled gracefully?
- [ ] Are loading states shown to users?
- [ ] Is the component accessible (ARIA labels, keyboard nav)?
- [ ] Are Tailwind classes using Oratio design tokens?
- [ ] Are images optimized with Next.js Image?
- [ ] Is sensitive data kept server-side only?
- [ ] Is the component responsive (mobile, tablet, desktop)?
- [ ] Are API calls properly error-handled?

## Last Updated

January 2025

**Framework Versions:** Next.js 15, React 19, shadcn/ui latest
