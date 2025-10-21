# Oratio Platform

**AI-Powered Voice & Text Agent Platform for Enterprises**

Build, deploy, and manage conversational AI agents in minutes—not months. Simply provide your SOPs and knowledge base, and Oratio automatically generates production-ready agents.

![Oratio Architecture](docs/Oratio.drawio.png)

---

## 📖 Quick Navigation

| Topic | Description |
|-------|-------------|
| [🤖 AgentCreator Pipeline](docs/AGENT_CREATOR.md) | How the meta-agent generates custom agents |
| [🎙️ Voice Agents](docs/VOICE_AGENTS.md) | How voice agents work with AWS Nova Sonic |
| [🚀 Deployment](docs/DEPLOYMENT.md) | Infrastructure setup and CI/CD pipeline |
| [🏗️ Architecture](docs/ORATIO_ARCHITECTURE.md) | Detailed system design |

---

## 🎯 What is Oratio?

Oratio is a **multi-tenant SaaS platform** that enables enterprises to create AI agents without writing code. The platform consists of three main components:

1. **Frontend Dashboard** - Next.js application for agent management
2. **Backend API** - FastAPI service handling authentication and orchestration
3. **Agent Infrastructure** - AWS-based agent creation and runtime system

### **The Problem We Solve**

Traditional AI agent deployment requires:
- Manual coding for each agent
- Separate infrastructure per agent
- Complex deployment pipelines
- Weeks of development time

### **Our Solution**

Oratio automates the entire process:
- Upload SOP + knowledge base documents
- AgentCreator meta-agent generates custom code
- Chameleon runtime loads agents dynamically
- Deploy unlimited agents with one infrastructure

---

## 🏗️ System Architecture

### **High-Level Flow**

```mermaid
graph TB
    subgraph "User Interface"
        A[Enterprise Dashboard]
    end
    
    subgraph "Backend Services"
        B[FastAPI Backend]
        C[AWS Cognito Auth]
    end
    
    subgraph "Agent Creation Pipeline"
        D[Step Functions Workflow]
        E[AgentCreator Meta-Agent]
        F[Knowledge Base Provisioner]
    end
    
    subgraph "Storage Layer"
        G[DynamoDB Tables]
        H[S3 Buckets]
        I[Bedrock Knowledge Bases]
    end
    
    subgraph "Runtime Layer"
        J[Chameleon Generic Loader]
        K[AgentCore Memory]
    end
    
    subgraph "End Users"
        L[Text Chat Customers]
        M[Voice Call Customers]
    end
    
    A -->|Create Agent| B
    B -->|Authenticate| C
    B -->|Trigger| D
    D -->|Invoke| E
    D -->|Provision KB| F
    E -->|Store Code| H
    E -->|Store Metadata| G
    F -->|Create KB| I
    
    L -->|Chat Request| J
    M -->|Voice Request| J
    J -->|Load Code| H
    J -->|Load Memory| K
    J -->|Query KB| I
```

### **Key Innovation: Chameleon Architecture**

Traditional approach: **One AgentCore deployment per agent** (slow, expensive)

Oratio approach: **One generic loader for unlimited agents**

```mermaid
graph LR
    subgraph "Traditional Approach"
        A1[Agent 1 Code] --> B1[AgentCore Runtime 1]
        A2[Agent 2 Code] --> B2[AgentCore Runtime 2]
        A3[Agent 3 Code] --> B3[AgentCore Runtime 3]
    end
    
    subgraph "Oratio Chameleon Approach"
        C1[Agent 1 Code]
        C2[Agent 2 Code]
        C3[Agent 3 Code]
        C1 --> D[S3 Storage]
        C2 --> D
        C3 --> D
        D --> E[Chameleon Loader]
        E -->|Loads Dynamically| F[Single AgentCore Runtime]
    end
```

**Benefits:**
- ✅ Sub-second agent creation (no deployment wait)
- ✅ Cost-effective scaling (one runtime for all agents)
- ✅ Per-agent memory isolation
- ✅ Instant updates (just update S3 code)

---

## 🔄 Agent Creation Workflow

```mermaid
sequenceDiagram
    participant User as Enterprise User
    participant UI as Dashboard
    participant API as Backend API
    participant SF as Step Functions
    participant AC as AgentCreator
    participant KB as KB Provisioner
    participant S3 as S3 Storage
    participant DB as DynamoDB

    User->>UI: Upload SOP + Documents
    UI->>API: POST /agents
    API->>DB: Store Agent Metadata
    API->>S3: Upload Documents
    API->>SF: Start Workflow
    
    SF->>KB: Provision Knowledge Base
    KB->>S3: Index Documents
    KB-->>SF: KB ARN
    
    SF->>AC: Generate Agent Code
    AC->>AC: Parse SOP
    AC->>AC: Design Architecture
    AC->>AC: Generate Strands Code
    AC->>AC: Review & Validate
    AC->>S3: Store agent_file.py
    AC-->>SF: Success
    
    SF->>DB: Update Agent Status
    SF-->>API: Workflow Complete
    API-->>UI: Agent Ready
```

### **AgentCreator Pipeline (DSPy + LangGraph)**

The meta-agent that generates custom agents:

```mermaid
graph LR
    A[SOP Input] --> B[Parse Requirements]
    B --> C[Draft Architecture Plan]
    C --> D[Review Plan]
    D -->|Needs Revision| C
    D -->|Approved| E[Generate Code]
    E --> F[Review Code]
    F -->|Needs Revision| E
    F -->|Approved| G[Generate Prompts]
    G --> H[Deploy to S3]
```

**Pipeline Stages:**
1. **SOP Parser** - Extracts business rules and requirements
2. **Plan Drafter** - Designs single or multi-agent architecture
3. **Plan Reviewer** - Validates architecture (up to 3 iterations)
4. **Code Generator** - Writes production-ready Strands agent code
5. **Code Reviewer** - Validates syntax and best practices
6. **Prompt Generator** - Creates optimized system prompts

---

## 💬 Runtime Execution Flow

### **Text Chat**

```mermaid
sequenceDiagram
    participant Customer as End Customer
    participant API as Backend API
    participant Cham as Chameleon
    participant S3 as S3 Storage
    participant Agent as Strands Agent
    participant KB as Knowledge Base
    participant Mem as Memory

    Customer->>API: POST /chat/{agent_id}
    API->>Cham: Invoke Agent
    Cham->>S3: Load agent_file.py
    Cham->>Mem: Load Conversation History
    Cham->>Agent: Execute with Context
    Agent->>KB: Retrieve Information
    KB-->>Agent: Relevant Documents
    Agent->>Agent: Process with Tools
    Agent->>Mem: Save Turn
    Agent-->>Cham: Response
    Cham-->>API: Result
    API-->>Customer: Agent Response
```

### **Voice Calls**

```mermaid
sequenceDiagram
    participant Customer as End Customer
    participant Voice as Voice Service
    participant Nova as Nova Sonic
    participant Cham as Chameleon
    participant Agent as Strands Agent

    Customer->>Voice: WebSocket Connect
    Voice->>Nova: Start Session
    
    loop Conversation
        Customer->>Voice: Audio Stream
        Voice->>Nova: Audio Input
        Nova->>Nova: Transcribe Speech
        
        alt Needs Business Logic
            Nova->>Cham: Invoke Agent Tool
            Cham->>Agent: Execute
            Agent-->>Cham: Response
            Cham-->>Nova: Result
        end
        
        Nova->>Nova: Generate Speech
        Nova->>Voice: Audio Output
        Voice->>Customer: Audio Stream
    end
```

---

## ✨ Key Features

### **1. No-Code Agent Creation**
- Upload SOP and knowledge base documents
- AgentCreator automatically designs optimal architecture
- Generates production-ready code in seconds
- No manual coding or deployment required

### **2. Intelligent Meta-Agent (AgentCreator)**
- **DSPy Framework** - Optimized LLM prompting
- **LangGraph Orchestration** - Multi-stage pipeline with quality gates
- **MCP Tools** - Accesses Strands and AgentCore documentation
- **Iterative Refinement** - Reviews and improves generated code
- **Multi-Agent Support** - Generates single or multi-agent architectures

### **3. Dynamic Runtime (Chameleon)**
- **Generic Loader** - One deployment for unlimited agents
- **S3-Based Loading** - Loads agent code on-demand
- **Memory Injection** - Automatic conversation history
- **Session Isolation** - Per-agent, per-customer separation

### **4. Dual Interaction Modes**
- **Text Chat** - REST API for web/mobile applications
- **Voice Calls** - WebSocket + AWS Nova Sonic for phone calls
- **Unified Backend** - Same agent code for both modes

### **5. Enterprise-Grade Memory**
- **AgentCore Memory API** - Persistent conversation history
- **Automatic Context Loading** - Last 10 turns loaded on init
- **Multi-Session Support** - Multiple conversations per customer
- **30-Day Retention** - Configurable retention policies

### **6. Multi-Tenant Architecture**
- **User Isolation** - Strict tenant separation in DynamoDB
- **API Key Management** - Scoped keys per agent
- **Cognito Authentication** - Secure user management
- **Role-Based Access** - CHAT, VOICE, ADMIN permissions

---

## 🛠️ Technology Stack

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Next.js 15]
        B[TypeScript]
        C[Tailwind CSS]
        D[shadcn/ui]
    end
    
    subgraph "Backend Layer"
        E[FastAPI]
        F[Python 3.11]
        G[Pydantic]
        H[boto3]
    end
    
    subgraph "Agent Creation"
        I[DSPy]
        J[LangGraph]
        K[Bedrock Nova Pro]
        L[MCP Tools]
    end
    
    subgraph "Generated Agents"
        M[Strands SDK]
        N[strands-tools]
        O[AgentCore Memory]
    end
    
    subgraph "AWS Infrastructure"
        P[CDK Python]
        Q[Cognito]
        R[DynamoDB]
        S[S3]
        T[Lambda]
        U[Step Functions]
        V[Bedrock]
    end
```

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| **Backend** | FastAPI, Python 3.11, Pydantic, boto3 |
| **Agent Creation** | DSPy, LangGraph, Bedrock Nova Pro, MCP Tools |
| **Generated Agents** | Strands SDK, strands-tools, AgentCore Memory |
| **Infrastructure** | AWS CDK, Cognito, DynamoDB, S3, Lambda, Step Functions |
| **LLM Models** | Nova Pro (text), Nova Sonic (voice), Claude (fallback) |
| **CI/CD** | GitHub Actions, Docker, ECR |

---

## 📊 Project Components

### **Frontend Dashboard**
- User authentication and registration
- Agent creation wizard
- Knowledge base management
- API key generation
- Session monitoring (future)

### **Backend API**
- RESTful endpoints for agent management
- Cognito integration for authentication
- JWT token validation
- WebSocket support for voice (future)
- Chat endpoint with API key validation

### **Agent Creator (Meta-Agent)**
- DSPy-powered code generation
- LangGraph workflow orchestration
- MCP documentation tools
- Syntax validation
- Multi-agent pattern support

### **Chameleon (Generic Loader)**
- Dynamic agent code loading from S3
- Memory hook injection
- Session state management
- Tool execution environment

### **Infrastructure (AWS CDK)**
- DynamoDB tables (users, agents, knowledge bases, API keys)
- S3 buckets (documents, generated code)
- Lambda functions (KB provisioner, AgentCreator invoker)
- Step Functions (agent creation workflow)
- Cognito User Pool (authentication)
- IAM roles and policies

---

## 🚀 Deployment Architecture

```mermaid
graph TB
    subgraph "GitHub"
        A[Code Repository]
    end
    
    subgraph "CI/CD Pipeline"
        B[GitHub Actions]
        C[Docker Build]
        D[ECR Push]
    end
    
    subgraph "AWS Infrastructure"
        E[CDK Deployment]
        F[CloudFormation]
    end
    
    subgraph "Deployed Services"
        G[Frontend Vercel]
        H[Backend ECS/Lambda]
        I[AgentCore Runtimes]
    end
    
    A -->|Push to main| B
    B --> C
    C --> D
    B --> E
    E --> F
    F --> G
    F --> H
    F --> I
```

**Deployment Process:**
1. Code pushed to GitHub main branch
2. GitHub Actions triggers CI/CD pipeline
3. Docker images built for backend and agent services
4. Images pushed to AWS ECR
5. CDK deploys infrastructure (DynamoDB, S3, Lambda, etc.)
6. AgentCore runtimes deployed (Chameleon, AgentCreator)
7. Frontend deployed to Vercel/Amplify

---

## 🔒 Security & Compliance

- **Authentication** - AWS Cognito with JWT tokens
- **Authorization** - API keys with scoped permissions
- **Data Isolation** - Multi-tenant DynamoDB design
- **Encryption** - S3 encryption at rest, TLS in transit
- **Secrets Management** - AWS Secrets Manager
- **Audit Logging** - CloudWatch Logs and X-Ray tracing
- **CORS** - Configured for production origins only

---

## 📈 Scalability

- **Horizontal Scaling** - Chameleon handles concurrent requests
- **Cost Optimization** - Pay-per-invocation model
- **Memory Efficiency** - Shared runtime for all agents
- **Storage** - S3 for unlimited agent code storage
- **Database** - DynamoDB on-demand scaling

---

## 📊 Current Status

**Phase:** MVP Development 

**Completed:**
- ✅ Frontend dashboard with authentication
- ✅ Backend API with Cognito integration
- ✅ AgentCreator meta-agent pipeline
- ✅ Chameleon generic loader
- ✅ AWS infrastructure (CDK)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ Text chat functionality
- ✅ Conversation memory system
- ✅ Voice agent integration (Nova Sonic)

**In Progress:**
- 🚧 Realtime call client transcriptions
- 🚧 Analytics dashboard

---

## 📚 Additional Documentation

- **[AgentCreator Pipeline](docs/AGENT_CREATOR.md)** - Meta-agent workflow and LangGraph orchestration
- **[Voice Agents](docs/VOICE_AGENTS.md)** - Detailed voice agent architecture

---



