# Oratio Platform

AI-Architected Voice Agents for Modern Enterprises

## Overview

Oratio is a multi-tenant SaaS platform that enables enterprises to create, deploy, and manage voice and conversational AI agents without writing code. Users provide SOPs (Standard Operating Procedures) and knowledge base documents, and Oratio automatically generates, deploys, and manages custom AI agents with REST API and WebSocket endpoints.

## Architecture

Three-tier architecture:
- **Frontend**: Next.js 14 with TypeScript, Tailwind CSS
- **Backend**: FastAPI with Python
- **Infrastructure**: AWS services (DynamoDB, S3, Lambda, Step Functions, Bedrock, AgentCore)

## Project Structure

```
oratio/
├── frontend/              # Next.js application
├── backend/               # FastAPI application
├── infrastructure/        # AWS CDK code (Python)
├── lambdas/              # Lambda function code
├── voice_service/        # Voice WebSocket service (to be implemented)
├── text_service/         # Text REST service (to be implemented)
└── docs/                 # Documentation (to be implemented)
```

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.11+
- uv package manager
- AWS CDK CLI
- AWS credentials configured

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Backend Setup

```bash
cd backend
uv sync
uv run uvicorn main:app --reload
```

API available at [http://localhost:8000](http://localhost:8000)

### Infrastructure Setup

```bash
cd infrastructure
uv sync
cdk bootstrap  # First time only
cdk deploy --all
```

## Development

### Frontend

```bash
cd frontend
npm run dev          # Development server
npm run build        # Production build
npm run lint         # Linting
npm run type-check   # Type checking
npm run format       # Format code
```

### Backend

```bash
cd backend
uv run uvicorn main:app --reload  # Development server
uv run ruff check .                # Linting
uv run ruff format .               # Format code
uv run pytest                      # Run tests
```

### Infrastructure

```bash
cd infrastructure
cdk synth        # Synthesize CloudFormation
cdk diff         # Show changes
cdk deploy --all # Deploy all stacks
```

## Key Features

- **No-Code Agent Creation**: Upload SOP and documents, get a production-ready AI agent
- **Meta-Agent Architecture**: AgentCreator automatically designs and deploys custom agents
- **Dual Interaction Modes**: Voice (WebSocket + Nova Sonic) and text (REST API + Claude)
- **Live Monitoring**: Real-time dashboard for active conversations
- **Human Handoff**: Configurable escalation triggers with notifications
- **Multi-Tenant**: Secure isolation with API key management per agent

## Tech Stack

### Frontend
- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- shadcn/ui components
- React Hook Form + Zod

### Backend
- FastAPI
- Python 3.11+
- Pydantic
- boto3 (AWS SDK)

### Infrastructure
- AWS CDK (Python)
- DynamoDB
- S3
- Lambda
- Step Functions
- Cognito
- Bedrock (Nova Sonic, Claude)
- AgentCore

## Documentation

- [Frontend README](frontend/README.md)
- [Backend README](backend/README.md)
- [Infrastructure README](infrastructure/README.md)
- [Requirements](.kiro/specs/oratio-platform/requirements.md)
- [Design](.kiro/specs/oratio-platform/design.md)
- [Tasks](.kiro/specs/oratio-platform/tasks.md)

## License

Proprietary - All rights reserved
