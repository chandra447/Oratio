# shadcn/ui Setup Guide

The frontend is now configured with shadcn/ui components.

## Configuration

- **Style**: New York
- **Base Color**: Neutral
- **CSS Variables**: Enabled
- **Icon Library**: Lucide React
- **TypeScript**: Enabled
- **React Server Components**: Enabled

## Adding Components

Use the shadcn CLI to add components:

```bash
# Add a single component
npx shadcn@latest add button

# Add multiple components
npx shadcn@latest add button card form input

# Add all components (not recommended)
npx shadcn@latest add --all
```

## Recommended Components for Oratio

Based on the design system, here are the components you'll likely need:

### Layout & Navigation
```bash
npx shadcn@latest add sidebar
npx shadcn@latest add navigation-menu
npx shadcn@latest add breadcrumb
```

### Forms & Inputs
```bash
npx shadcn@latest add form
npx shadcn@latest add input
npx shadcn@latest add textarea
npx shadcn@latest add select
npx shadcn@latest add checkbox
npx shadcn@latest add radio-group
npx shadcn@latest add switch
npx shadcn@latest add label
```

### Data Display
```bash
npx shadcn@latest add table
npx shadcn@latest add card
npx shadcn@latest add badge
npx shadcn@latest add avatar
npx shadcn@latest add separator
```

### Feedback
```bash
npx shadcn@latest add alert
npx shadcn@latest add toast
npx shadcn@latest add progress
npx shadcn@latest add skeleton
```

### Overlays
```bash
npx shadcn@latest add dialog
npx shadcn@latest add sheet
npx shadcn@latest add popover
npx shadcn@latest add dropdown-menu
npx shadcn@latest add tooltip
```

### Buttons & Actions
```bash
npx shadcn@latest add button
npx shadcn@latest add scroll-area
```

## Usage Example

```tsx
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function Example() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Welcome to Oratio</CardTitle>
        <CardDescription>AI-Architected Voice Agents</CardDescription>
      </CardHeader>
      <CardContent>
        <Button>Get Started</Button>
      </CardContent>
    </Card>
  )
}
```

## Customization

### Colors

Edit `frontend/src/app/globals.css` to customize the color palette:

```css
:root {
  --primary: hsl(222.2 47.4% 11.2%);
  --primary-foreground: hsl(210 40% 98%);
  /* ... other colors */
}
```

### Tailwind Config

Edit `frontend/tailwind.config.ts` to extend the theme:

```typescript
theme: {
  extend: {
    // Add custom styles here
  }
}
```

## Component Structure

All shadcn/ui components will be added to:
```
frontend/src/components/ui/
```

Custom components should go in:
```
frontend/src/components/
```

## Resources

- [shadcn/ui Documentation](https://ui.shadcn.com/)
- [Lucide Icons](https://lucide.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Radix UI](https://www.radix-ui.com/)

## Next Steps

1. Add the components you need for your first page
2. Create custom components that compose shadcn/ui components
3. Build out the authentication pages
4. Create the dashboard layout
5. Implement the agent creation wizard
