# Oratio Platform

**AI-Powered Agent Platform-as-a-Service for Enterprises**

Build, deploy, and manage conversational and voice AI agents in minutes—not months.

---

## 🎯 Overview

Oratio is a multi-tenant SaaS platform that enables enterprises to create, deploy, and manage AI agents without writing code. Simply provide your SOPs (Standard Operating Procedures) and knowledge base documents, and Oratio automatically generates, deploys, and manages production-ready AI agents.

### **Dual Interaction Modes**
- **💬 Text Chat** (Available Now): REST API for web apps, mobile apps, chatbots, Slack/Discord integrations
- **🎙️ Voice Agents** (Coming Soon): WebSocket-based voice interactions with AWS Nova Sonic

---

## 🏗️ Architecture

### **Three-Tier System**
```
Frontend (Next.js) → Backend (FastAPI) → AWS Infrastructure (CDK)
       ↓                    ↓                      ↓
  Dashboard UI      REST/WebSocket APIs    AgentCore Runtime
```

### **Unique "Chameleon" Architecture**
Instead of deploying one AgentCore runtime per agent (slow, expensive), Oratio uses a **generic loader called "Chameleon"** that dynamically loads agent code from S3 at invocation time:

```
Enterprise User → Creates Agent → AgentCreator Meta-Agent
                                        ↓
                              Agent Code Stored in S3
                                        ↓
End Customer → Text/Voice Request → Chameleon (Generic Loader)
                                        ↓
                              Dynamically Loads Agent from S3
                                        ↓
                              Executes + Memory Hooks
                                        ↓
                              Returns Response
```

**Benefits:**
- ✅ One AgentCore deployment for unlimited agents
- ✅ Sub-second agent creation (no deployment wait)
- ✅ Cost-effective scaling
- ✅ Per-agent memory isolation

---

## 📁 Project Structure

```
oratio/
├── frontend/                 # Next.js 15 app (TypeScript, Tailwind, shadcn/ui)
│   ├── app/                 # Pages (landing, auth, dashboard)
│   ├── components/          # React components
│   ├── lib/                 # API clients, auth context
│   └── middleware.ts        # Security headers
│
├── backend/                 # FastAPI application
│   ├── routers/            # API endpoints (auth, agents, chat)
│   ├── services/           # Business logic (auth, agent CRUD, invocation)
│   ├── models/             # Pydantic models
│   ├── aws/                # AWS SDK clients (Cognito, DynamoDB, S3, Bedrock)
│   └── utils/              # JWT validation, helpers
│
├── agent-creator/          # AgentCreator Meta-Agent (DSPy + LangGraph)
│   ├── agentcreator/       # DSPy modules & pipeline
│   │   ├── signatures/     # DSPy signatures (plan, code, review)
│   │   ├── modules.py      # DSPy modules (ChainOfThought, ReAct)
│   │   ├── pipeline.py     # LangGraph orchestration
│   │   └── mcp_tools.py    # MCP documentation tools
│   ├── generic_loader.py   # Chameleon (dynamic agent loader)
│   ├── agent_runtime.py    # AgentCreator FastAPI runtime
│   └── Dockerfile          # AgentCreator container
│
├── infrastructure/         # AWS CDK (Python)
│   ├── stacks/            # CDK stacks (main Oratio stack)
│   ├── cdk_constructs/    # Reusable constructs (auth, compute, storage, IAM)
│   └── scripts/           # Deployment scripts (deploy_agentcore.py)
│
├── lambdas/               # Lambda functions
│   ├── kb_provisioner/    # Creates Bedrock Knowledge Bases
│   └── agentcreator_invoker/  # Invokes AgentCreator + creates memory
│
├── .github/
│   └── workflows/         # CI/CD (deploy-infrastructure.yml)
│
└── docs/                  # Architecture & design docs
```

---

## 🚀 Getting Started

### **Prerequisites**
- **Node.js** 20+
- **Python** 3.11+
- **uv** package manager (`pip install uv`)
- **AWS CDK CLI** (`npm install -g aws-cdk`)
- **AWS credentials** configured
- **Docker** (for local testing)

---

### **1. Frontend Setup**

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

**Features:**
- ✅ Landing page
- ✅ Login/Signup (Cognito integration)
- ✅ Dashboard (agents, knowledge bases, API keys)
- ✅ Protected routes (client-side with JWT)

---

### **2. Backend Setup**

```bash
cd backend
uv sync
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs at [http://localhost:8000/docs](http://localhost:8000/docs)

**Endpoints:**
- ✅ `POST /api/v1/auth/register` - User registration
- ✅ `POST /api/v1/auth/login` - Login with Cognito
- ✅ `POST /api/v1/agents` - Create agent
- ✅ `GET /api/v1/agents` - List agents
- ✅ `POST /api/v1/chat/{agent_id}/{actor_id}/{session_id}` - Chat with agent
- 🔮 `WS /api/v1/voice/{agent_id}/{actor_id}/{session_id}` - Voice agent (future)

---

### **3. Infrastructure Deployment**

```bash
cd infrastructure
uv sync
cdk bootstrap  # First time only
cdk deploy --all
```

**What Gets Deployed:**
- ✅ DynamoDB tables (users, agents, API keys, knowledge bases)
- ✅ S3 buckets (knowledge base files, generated agent code)
- ✅ Cognito User Pool (authentication)
- ✅ Lambda functions (KB provisioner, AgentCreator invoker)
- ✅ Step Functions (agent creation workflow)
- ✅ IAM roles (AgentCore execution roles for Chameleon + AgentCreator)

**GitHub Actions CI/CD:**
1. Builds Docker images (AgentCreator, Chameleon, Backend)
2. Pushes to ECR
3. Deploys CDK infrastructure
4. Deploys AgentCore runtimes (AgentCreator, Chameleon)
5. Stores ARNs in SSM Parameter Store

---

## 🔑 Key Features

### **1. No-Code Agent Creation**
- Upload SOP document + knowledge base files
- AgentCreator meta-agent designs optimal architecture
- Generates production-ready Strands agent code
- Creates dedicated memory resource
- Deploys in seconds (not minutes)

### **2. Meta-Agent Architecture (AgentCreator)**
**DSPy + LangGraph Pipeline:**
```
SOP → Parse → Draft Plan → Review Plan → Generate Code → Review Code → Generate Prompt
```

- Uses MCP tools to access Strands + AgentCore documentation
- Supports single-agent and multi-agent (agents-as-tools) patterns
- Validates code syntax with code interpreter
- Iterative refinement (up to 3 cycles per stage)

### **3. Chameleon Generic Loader**
- Dynamically loads agent code from S3
- Injects memory hooks for conversation continuity
- Fetches `memory_id` from DynamoDB (per agent)
- Supports `actor_id` (end customer) + `session_id` (conversation)

### **4. Multi-Tenant with API Keys**
- Scoped API keys per agent
- Permissions: `CHAT`, `VOICE`, `ADMIN`
- Rate limiting (future)

### **5. Conversation Memory**
- Per-agent memory resource (AWS Bedrock AgentCore Memory API)
- Per-actor sessions (end customers)
- Automatic context loading (last 10 turns)
- 30-day retention

---

## 🧪 Testing Checklist

### **Backend Tests (Before Deployment)**
```bash
cd backend
uv run pytest
```

### **Critical Tests:**
- [ ] Cognito registration (check email for verification code)
- [ ] Cognito login (JWT tokens returned)
- [ ] JWT validation in protected endpoints
- [ ] Agent creation (triggers Step Functions)
- [ ] Chat endpoint with valid API key
- [ ] Chat endpoint with invalid API key (403)
- [ ] Agent invocation (Chameleon loads code from S3)

---

## 🧑‍💻 Development Workflow

### **Frontend**
```bash
cd frontend
npm run dev          # Dev server with hot reload
npm run build        # Production build
npm run lint         # ESLint
```

### **Backend**
```bash
cd backend
uv run uvicorn main:app --reload  # Dev server
uv run ruff check .                # Linting
uv run ruff format .               # Formatting
```

### **Infrastructure**
```bash
cd infrastructure
cdk synth           # Generate CloudFormation
cdk diff            # Show changes
cdk deploy --all    # Deploy
cdk destroy --all   # Cleanup
```

---

## 🗂️ Tech Stack

### **Frontend**
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4
- **UI**: shadcn/ui (Radix UI primitives)
- **Forms**: React Hook Form + Zod
- **State**: React Context (auth)
- **HTTP**: Fetch API (custom client)

### **Backend**
- **Framework**: FastAPI
- **Language**: Python 3.11
- **Validation**: Pydantic
- **AWS SDK**: boto3
- **JWT**: jose (Python JOSE)
- **CORS**: FastAPI CORS middleware

### **Agent Creation (Meta-Agent)**
- **Framework**: DSPy (LLM prompting framework)
- **Orchestration**: LangGraph (state machine)
- **LLM**: Bedrock Nova Pro (fast + cost-effective)
- **Tools**: MCP (Model Context Protocol) for docs
- **Code Validation**: DSPy PythonInterpreter

### **Generated Agents**
- **Framework**: Strands Agents SDK
- **Tools**: strands-tools (community package)
- **Memory**: Bedrock AgentCore Memory API (via hooks)
- **Runtime**: Chameleon (generic loader)

### **Infrastructure**
- **IaC**: AWS CDK (Python)
- **Auth**: AWS Cognito
- **Database**: DynamoDB
- **Storage**: S3
- **Compute**: Lambda, AgentCore Runtime
- **Orchestration**: Step Functions
- **LLM**: Bedrock (Nova, Claude)
- **CI/CD**: GitHub Actions

---

## 📝 Next Steps (See TASKS.md)

1. **Deploy Infrastructure** (6-day goal)
   - Test Cognito auth flow
   - Test agent creation workflow
   - Test text chat API

2. **Session Management API** (Post-MVP)
   - List sessions for agent
   - Get conversation history
   - Basic analytics

3. **Voice Integration** (Future)
   - Nova Sonic WebSocket endpoint
   - Chameleon as tool for voice agent
   - RxPy streaming for real-time UI

---

## 📚 Documentation

- [Agent Creator Architecture](agent-creator/ARCHITECTURE.md)
- [Infrastructure Deployment](infrastructure/README.md)
- [Backend API](backend/README.md)
- [Authentication Flow](docs/AUTHENTICATION_IMPLEMENTATION.md)
- [Dependency Injection](docs/DEPENDENCY_INJECTION.md)

---

## 🔒 Security Notes

- **Frontend**: Client-side route protection (tokens in localStorage)
- **Backend**: JWT validation on all protected endpoints
- **API Keys**: Scoped per agent with permissions
- **Secrets**: Stored in AWS Secrets Manager (Cognito client secret)
- **CORS**: Configured for production origins
- **Headers**: Security headers via Next.js middleware

---

## 📄 License

Proprietary - All Rights Reserved

---

## 🙋 Support

For questions or issues, refer to `TASKS.md` for current development status.
