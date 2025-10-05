# Oratio Frontend

Next.js 14 frontend application for Oratio platform.

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (to be added)
- **Icons**: Lucide React (to be added)

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run production server
npm start

# Type check
npm run type-check

# Lint
npm run lint

# Format code
npm run format
```

## Project Structure

```
src/
├── app/                    # App router pages
│   ├── (auth)/            # Authentication pages
│   ├── (dashboard)/       # Dashboard pages
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/            # React components
│   └── ui/               # shadcn/ui components
└── lib/                  # Utilities and helpers
    └── utils.ts          # Utility functions
```

## Development

Open [http://localhost:3000](http://localhost:3000) to view the application.
