# Implementation Plan

- [x] 1. Set up project structure and core infrastructure
  - Create directory structure for frontend (Next.js) and backend (FastAPI)
  - Set up development environment with Docker containers
  - Configure AWS CDK for infrastructure as code
  - _Requirements: 12.1, 12.2_

- [x] 1.1 Initialize Next.js frontend with TypeScript
  - Create Next.js 14 project with app router
  - Configure TypeScript, ESLint, and Tailwind CSS
  - Set up project structure with components, pages, and utilities
  - _Requirements: 1.1, 1.2_

- [x] 1.2 Initialize FastAPI backend with Python
  - Create FastAPI project with proper directory structure
  - Set up virtual environment and dependencies
  - Configure development server and hot reload
  - _Requirements: 1.3, 1.4_

- [x] 1.3 Set up AWS infrastructure with Python CDK
  - Install AWS CDK CLI and Python CDK libraries (aws-cdk-lib, constructs)
  - Create CDK app structure with Python stacks for DynamoDB, S3, Lambda, Step Functions
  - Configure IAM roles and policies for service access
  - Set up Step Functions state machine definition
  - _Requirements: 11.1, 12.1, 12.2_

- [x] 1.4 Configure Oratio design system in shadcn/ui and Tailwind
  - Update frontend/tailwind.config.ts with Oratio color palette (primary: #1A244B, secondary: #FFB76B, accent: #8A3FFC, background-light: #F7F7F9, background-dark: #101010, surface-light: #FFFFFF, surface-dark: #1C1C1E, text-light: #1A244B, text-dark: #FFFFFF, subtle-light: #646B87, subtle-dark: #A0AEC0)
  - Configure custom border radius values for Oratio arch motif (DEFAULT: 1rem, lg: 1.5rem, xl: 2rem, full: 9999px)
  - Add custom box-shadow for glowing effects (glow: '0 0 20px 5px rgba(255, 183, 107, 0.3), 0 0 10px 2px rgba(138, 63, 252, 0.2)')
  - Set up Inter font family as primary display font in Tailwind config with display variant
  - Update frontend/src/app/globals.css with CSS custom properties for Oratio design tokens
  - Create custom CSS utilities for signature elements (.oratio-corner with border-bottom-right-radius: 2rem, .oratio-corner-top-left with border-top-left-radius: 2rem)
  - Add CSS animations for blob effects (@keyframes blob with translate and scale transformations)
  - Reference design tokens and styles from frontend/public/design/dashboard.html and landing.html
  - _Requirements: 1.1, 1.2_

- [x] 1.4.1 Install and configure required shadcn/ui components
  - Install shadcn/ui components: button, card, badge, avatar, input, label, separator, scroll-area, skeleton
  - Install Lucide React for consistent iconography (npm install lucide-react)
  - Configure components to use Oratio design tokens by default
  - Update component variants to support Oratio-specific styles (pill buttons, glowing effects)
  - Ensure all components support dark mode with Oratio dark color palette
  - _Requirements: 1.1, 1.2_

- [x] 1.5 Create landing page with Oratio design system
  - Build landing page at frontend/src/app/page.tsx
  - Implement hero section with animated blob backgrounds using CSS animations and gradient text effects
  - Create "How Oratio Works" section with three-column grid, icon-based workflow steps, and connecting line
  - Add "See Oratio in Action" video section with aspect-video container, play button overlay, and hover effects
  - Build "Built for Your Industry" grid (2x4 on mobile, 4 columns on desktop) with image cards and gradient overlays
  - Implement CTA section with rounded pill buttons, glowing effects, and gradient backgrounds
  - Create footer with multi-column layout (Product, Company, Resources, Legal) and brand consistency using appropriate logo variant
  - Use shadcn/ui components (Button, Card) styled with Oratio design tokens
  - Ensure responsive design with mobile-first approach
  - _Requirements: 1.1, 1.2_

- [x] 2. Implement authentication and user management
  - Create user registration and login functionality
  - Implement JWT token validation and refresh
  - Set up multi-tenant data isolation
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [x] 2.1 Create user authentication models and services
  - Implement User model with validation
  - Create AuthService for registration, login, and token management
  - Set up password hashing with bcrypt
  - _Requirements: 1.1, 1.2, 1.4_

- [x] 2.2 Implement Cognito integration
  - Set up AWS Cognito User Pool configuration
  - Create Cognito client for user operations
  - Implement email verification workflow
  - _Requirements: 1.1, 1.5_

- [x] 2.3 Create authentication API endpoints
  - Implement POST /api/auth/register endpoint
  - Implement POST /api/auth/login endpoint
  - Implement POST /api/auth/refresh endpoint
  - Implement GET /api/auth/me endpoint
  - _Requirements: 1.2, 1.3, 1.6_

- [x] 2.4 Build frontend authentication components
  - Create login and registration forms with validation following design system from frontend/public/design/landing.html
  - Use Oratio logo from frontend/public/oratio_light.png (light mode) and frontend/public/oratio_dark.png (dark mode) in auth pages
  - Implement JWT token storage and management
  - Create protected route guards
  - Set up automatic token refresh
  - Use Oratio design system: rounded pill buttons, primary blue (#1A244B), accent orange (#FFB76B)
  - _Requirements: 1.2, 1.6_

- [ ]* 2.5 Write authentication unit tests
  - Create unit tests for AuthService methods
  - Test JWT token validation and refresh logic
  - Test password hashing and verification
  - _Requirements: 1.1, 1.2, 1.6_

- [ ] 3. Implement agent creation and management
  - Create agent data models and validation
  - Build agent creation workflow with Step Functions
  - Implement agent CRUD operations
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

- [x] 3.1 Update DynamoDB schema for agents and knowledge bases
  - Add oratio-knowledgebases table to infrastructure/cdk_constructs/database.py with fields: knowledgeBaseId (PK), userId (for GSI), s3Path, bedrockKnowledgeBaseId, status, folderFileDescriptions, createdAt, updatedAt
  - Add GSI on userId for querying user's knowledge bases
  - Update agents table schema documentation to include: knowledgeBaseId, sop, knowledgeBaseDescription, humanHandoffDescription, generatedPrompt, agentCodeS3Path, status
  - Deploy CDK changes to create new table
  - _Requirements: 2.1, 2.2, 12.1_

- [x] 3.2 Create backend data models
  - Create backend/models/knowledge_base.py with KnowledgeBase model (knowledgeBaseId, userId, s3Path, bedrockKnowledgeBaseId, status, folderFileDescriptions as nested dict, createdAt, updatedAt)
  - Create backend/models/agent.py with Agent model including all fields: agentId, userId, agentName, agentType, sop, knowledgeBaseId, knowledgeBaseDescription, humanHandoffDescription, bedrockKnowledgeBaseArn, agentcoreAgentId, agentcoreAgentArn, generatedPromptS3Path (path to prompt.md), agentCodeS3Path (path to agent_file.py), status, createdAt, updatedAt, websocketUrl, apiEndpoint
  - Add Pydantic validation for all fields with proper types
  - Create enums for status fields (AgentStatus: creating|active|failed|paused, KnowledgeBaseStatus: notready|ready|error)
  - Note: voiceConfig and textConfig removed - voice agents use generated prompt.md, text agents use agent_file.py directly
  - _Requirements: 2.1, 8.1_

- [ ] 3.3 Create AWS client wrappers with tagging support
  - Create backend/aws/s3_client.py with methods: upload_file (with userId and agentId tags), upload_folder, get_file, list_files
  - Create backend/aws/dynamodb_client.py with methods for agents and knowledge bases tables: put_item, get_item, query_by_user, update_item
  - Create backend/aws/bedrock_client.py with create_knowledge_base method (with userId tag), create_data_source, start_ingestion_job
  - Create backend/aws/stepfunctions_client.py with start_execution method
  - Ensure all AWS resource creation includes proper tags (userId, agentId where applicable)
  - _Requirements: 2.2, 2.3, 12.1, 12.2_

- [x] 3.4 Create backend services for agent and knowledge base operations
  - Create backend/services/knowledge_base_service.py with methods: create_knowledge_base (creates DynamoDB entry with status="notready"), update_status, get_knowledge_base, list_user_knowledge_bases
  - Create backend/services/agent_service.py with methods: create_agent (creates DynamoDB entry with status="creating"), get_agent, list_user_agents, update_agent_status, update_agent_code_path, update_generated_prompt
  - Create backend/services/s3_service.py with methods: upload_knowledge_base_files (uploads to s3://oratio-knowledge-bases/{userId}/{agentId}/ with tags), generate_folder_structure
  - Implement proper error handling and logging in all services
  - _Requirements: 2.1, 2.2, 8.1, 8.2_

- [x] 3.5 Implement agent creation API endpoint
  - Create POST /api/agents endpoint in backend/routers/agents.py
  - Accept multipart/form-data with fields: agentName, agentType, sop, knowledgeBaseDescription, humanHandoffDescription, files (multiple), folderFileDescriptions (JSON string with nested structure)
  - Extract userId from JWT token for tenant isolation
  - Generate unique agentId and knowledgeBaseId (UUID)
  - Parse folderFileDescriptions JSON into nested dict structure: {"folder1": {"file1.pdf": "desc"}, "file2.txt": "desc"}
  - Upload files to S3 with proper tagging (userId, agentId, resourceType=knowledge-base)
  - Create knowledge base entry in DynamoDB with status="notready" and nested folderFileDescriptions
  - Create agent entry in DynamoDB with status="creating" and all provided fields
  - Trigger Step Functions workflow with payload: {userId, agentId, knowledgeBaseId, sop, knowledgeBaseDescription, humanHandoffDescription}
  - Return agent details with status="creating"
  - _Requirements: 2.1, 2.2, 2.8, 11.1_

- [x] 3.6 Implement agent listing and retrieval endpoints
  - Create GET /api/agents endpoint to list all user's agents with filtering by status
  - Create GET /api/agents/{agentId} endpoint to get single agent details
  - Ensure tenant isolation by validating userId from JWT matches agent's userId
  - Return 404 if agent not found or doesn't belong to user
  - Include knowledge base details in agent response
  - _Requirements: 2.1, 8.1, 12.6_

- [x] 3.7 Implement KB Provisioner Lambda function
  - Update lambdas/kb_provisioner/handler.py to create Bedrock Knowledge Base
  - Retrieve knowledge base details from DynamoDB using knowledgeBaseId
  - Create Bedrock Knowledge Base with OpenSearch Serverless backend and userId tag
  - Create S3 data source pointing to s3://oratio-knowledge-bases/{userId}/{agentId}/
  - Configure chunking strategy (FIXED_SIZE, 500 tokens, 20% overlap)
  - Start ingestion job and wait for completion (with timeout and retry logic)
  - Update knowledge base in DynamoDB with bedrockKnowledgeBaseId and status="ready" on success
  - Update status="error" on failure with error details
  - Return {knowledgeBaseId, bedrockKnowledgeBaseId, status} for next step
  - _Requirements: 2.3, 10.1, 11.2_

- [x] 3.8 Implement AgentCreator Invoker Lambda function
  - Update lambdas/agentcreator_invoker/handler.py to invoke AgentCreator meta-agent
  - Retrieve agent details from DynamoDB using agentId
  - Retrieve knowledge base details including nested folderFileDescriptions structure
  - Prepare payload for AgentCreator: {sop, knowledgeBaseId, bedrockKnowledgeBaseId, knowledgeBaseDescription, humanHandoffDescription, folderFileDescriptions}
  - Invoke AgentCreator meta-agent via bedrock-agent-runtime with proper session management
  - AgentCreator should output: agent_file.py (Strands agent code) and prompt.md (system prompt for Nova Sonic)
  - Store agent_file.py to s3://oratio-generated-code/{userId}/{agentId}/agent_file.py with tags (userId, agentId, resourceType=generated-code)
  - Store prompt.md to s3://oratio-generated-code/{userId}/{agentId}/prompt.md with same tags
  - Update agent in DynamoDB with agentCodeS3Path and generatedPromptS3Path
  - Return {agentId, codeS3Path, promptS3Path} for next step
  - _Requirements: 2.4, 10.2, 10.3, 10.4, 10.5, 10.6, 11.3_

- [x] 3.9 Implement Code Checker Lambda function
  - Create lambdas/code_checker/handler.py to check if generated code exists in S3
  - Accept action="check_code" in event payload
  - Check if s3://oratio-generated-code/{userId}/{agentId}/agent_file.py exists
  - Return {codeReady: true/false, agentId, codeS3Path} for Step Functions decision
  - _Requirements: 11.4_

- [x] 3.10 Implement AgentCore Deployer Lambda function
  - Update lambdas/agentcore_deployer/handler.py to deploy agent to AgentCore
  - Retrieve generated agent code from S3 using agentCodeS3Path
  - Deploy agent to AWS AgentCore using bedrock-agent APIs with tags (userId, agentId)
  - Create agent alias for production deployment
  - Store agentcoreAgentId and agentcoreAgentArn in DynamoDB
  - Generate websocketUrl and apiEndpoint based on agent type
  - Update agent status to "active" in DynamoDB
  - Send notification to user (future: via SNS/SES)
  - Return {agentId, status: "active", agentcoreAgentId, websocketUrl, apiEndpoint}
  - _Requirements: 2.5, 2.6, 11.5_

- [x] 3.11 Create Step Functions workflow for agent creation
  - Update infrastructure/cdk_constructs/stepfunctions.py (or create if not exists) with agent creation state machine
  - Define workflow: Start → KB Provisioner → AgentCreator Invoker → Wait (30s) → Code Checker → Choice (codeReady?) → [Yes: AgentCore Deployer, No: Wait (max 20 min total)] → End
  - Configure error handling with Catch blocks for each Lambda
  - Set retry policies for transient failures (3 retries with exponential backoff)
  - Set overall workflow timeout to 20 minutes
  - On error, update agent status to "failed" in DynamoDB with error details
  - On timeout, update agent status to "failed" with timeout error message
  - Configure CloudWatch logging for workflow execution
  - Deploy Step Functions state machine via CDK
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8_

- [x] 3.12 Update CDK infrastructure for Lambda functions
  - Update infrastructure/stacks/lambda_stack.py (or create if not exists) to define all Lambda functions
  - Configure KB Provisioner Lambda with environment variables: AGENTS_TABLE, KB_TABLE, KB_BUCKET
  - Configure AgentCreator Invoker Lambda with environment variables: AGENTS_TABLE, CODE_BUCKET, AGENTCREATOR_AGENT_ID
  - Configure Code Checker Lambda with environment variables: CODE_BUCKET
  - Configure AgentCore Deployer Lambda with environment variables: AGENTS_TABLE, CODE_BUCKET
  - Grant IAM permissions: DynamoDB read/write, S3 read/write, Bedrock KB creation, AgentCore deployment, Step Functions execution
  - Set appropriate timeout (5 min for KB Provisioner, 15 min for AgentCreator Invoker, 10 min for Deployer)
  - Deploy Lambda functions via CDK
  - _Requirements: 11.2, 11.3, 11.5_

- [ ]* 3.13 Write unit tests for agent service
  - Test agent creation workflow logic in backend/tests/test_agent_service.py
  - Test document upload and S3 tagging in backend/tests/test_s3_service.py
  - Test knowledge base service operations in backend/tests/test_knowledge_base_service.py
  - Mock AWS clients (S3, DynamoDB, Step Functions) for isolated testing
  - Test error handling and validation
  - _Requirements: 2.1, 2.7, 11.7_

- [ ] 4. Implement AgentCreator meta-agent pipeline with DSPy + LangGraph
  - Set up DSPy and LangGraph frameworks
  - Create SOP parsing and analysis with DSPy modules
  - Implement LangGraph workflow for agent generation
  - Generate Strands agents for AgentCore deployment
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

- [ ] 4.1 Set up DSPy and LangGraph environment
  - Install DSPy and LangGraph dependencies (pip install dspy-ai langgraph)
  - Configure DSPy with Bedrock Claude model as LLM backend
  - Set up LangGraph state management and workflow structure
  - Create base pipeline directory structure
  - _Requirements: 10.1_

- [ ] 4.2 Create SOP parser with DSPy
  - Implement DSPy Signature for SOP parsing task
  - Create ChainOfThought module for requirement extraction
  - Extract key requirements, business rules, and constraints from SOP text
  - Output structured data representation (JSON schema)
  - _Requirements: 10.1, 10.2_

- [ ] 4.3 Build LangGraph workflow for agent planning
  - Create LangGraph StateGraph for pipeline orchestration
  - Implement Plan Drafter node using DSPy module
  - Create Plan Reviewer node with cyclic refinement (2+ cycles)
  - Set up conditional edges for quality gates and iteration control
  - _Requirements: 10.2, 10.3_

- [ ] 4.4 Implement Strands agent code generator with DSPy
  - Create DSPy module for Strands agent code generation
  - Generate Python code following Strands framework patterns (tools, memory, reasoning)
  - Include proper imports and Strands agent structure
  - Ensure AgentCore deployment compatibility
  - Reference: https://strandsagents.com/latest/documentation/docs/
  - _Requirements: 10.4, 10.5_

- [ ] 4.5 Create code review and validation node
  - Implement LangGraph node for code quality review
  - Use DSPy for automated code analysis and validation
  - Validate Strands agent structure and best practices
  - Implement retry mechanism with feedback loop to code generator
  - _Requirements: 10.5, 10.6, 10.7_

- [ ] 4.6 Set up S3 integration for generated Strands agents
  - Implement secure code storage in S3 (oratio-generated-code bucket)
  - Create code retrieval for AgentCore deployment
  - Set up proper access controls and versioning
  - Store agent metadata and configuration alongside code
  - _Requirements: 10.6, 10.8_

- [ ]* 4.7 Write meta-agent pipeline unit tests
  - Test DSPy module outputs for SOP parsing accuracy
  - Test LangGraph workflow state transitions and cycles
  - Test Strands agent code generation quality and structure
  - Test error handling and retry logic
  - _Requirements: 10.7, 10.8_

- [ ] 5. Implement voice interaction service
  - Create WebSocket server for voice streaming
  - Integrate Nova Sonic for voice processing
  - Implement session management for voice calls
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [ ] 5.1 Create voice service WebSocket server
  - Implement FastAPI WebSocket endpoints
  - Set up bidirectional audio streaming
  - Create connection management and authentication
  - _Requirements: 3.1, 3.2_

- [ ] 5.2 Integrate Nova Sonic voice processing
  - Implement Nova Sonic client integration
  - Set up audio format conversion and streaming
  - Create voice-to-text and text-to-voice pipeline
  - _Requirements: 3.3, 3.5_

- [ ] 5.3 Implement voice session management
  - Create voice session data models
  - Implement session creation and tracking
  - Set up transcript and audio recording storage
  - _Requirements: 3.6, 3.7_

- [ ] 5.4 Create AgentCore integration for voice
  - Implement AgentCore client for voice responses
  - Set up context passing between voice and agent
  - Create response streaming back to client
  - _Requirements: 3.4, 3.5_

- [ ] 5.5 Implement WebSocket reconnection handling
  - Create graceful connection drop handling
  - Implement session continuity across reconnections
  - Set up automatic reconnection logic
  - _Requirements: 3.8_

- [ ]* 5.6 Write voice service unit tests
  - Test WebSocket connection handling
  - Test Nova Sonic integration
  - Test session management logic
  - _Requirements: 3.6, 3.7, 3.8_

- [ ] 6. Implement text conversation service
  - Create REST API for text interactions
  - Implement conversation session management
  - Set up AgentCore integration for text responses
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [ ] 6.1 Create text conversation API endpoints
  - Implement POST /chat/{agent_id} endpoint
  - Set up request validation and authentication
  - Create response formatting with sources
  - _Requirements: 4.1, 4.2, 4.4_

- [ ] 6.2 Implement text session management
  - Create text session data models
  - Implement session creation and retrieval
  - Set up conversation history persistence
  - _Requirements: 4.5, 4.6, 4.7_

- [ ] 6.3 Create AgentCore integration for text
  - Implement AgentCore client for text conversations
  - Set up context and history passing
  - Create knowledge base source attribution
  - _Requirements: 4.3, 4.4_

- [ ]* 6.4 Write text service unit tests
  - Test REST API endpoint functionality
  - Test session management logic
  - Test AgentCore integration
  - _Requirements: 4.3, 4.5, 4.7_

- [ ] 7. Implement API key management system
  - Create API key generation and validation
  - Implement secure key storage and hashing
  - Build key management interface
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [ ] 7.1 Create API key data models and services
  - Implement ApiKey model with validation
  - Create ApiKeyService for key operations
  - Set up secure key hashing with bcrypt
  - _Requirements: 5.1, 5.3_

- [ ] 7.2 Implement API key generation and storage
  - Create secure key generation logic
  - Implement one-time key display functionality
  - Set up DynamoDB operations for key metadata
  - _Requirements: 5.1, 5.2_

- [ ] 7.3 Create API key validation middleware
  - Implement key validation for voice and text services
  - Set up usage tracking and rate limiting
  - Create key expiration and revocation logic
  - _Requirements: 5.3, 5.5, 5.6, 5.7_

- [ ] 7.4 Build API key management endpoints
  - Create POST /api/api-keys endpoint
  - Create GET /api/api-keys endpoint
  - Create DELETE /api/api-keys/{key_id} endpoint
  - _Requirements: 5.1, 5.4, 5.5_

- [ ] 7.5 Create API key management frontend
  - Build key generation interface
  - Create key listing with metadata display
  - Implement key revocation functionality
  - _Requirements: 5.2, 5.4, 5.5_

- [ ]* 7.6 Write API key management unit tests
  - Test key generation and validation
  - Test usage tracking and rate limiting
  - Test key revocation logic
  - _Requirements: 5.3, 5.6, 5.7_

- [ ] 8. Implement live session monitoring dashboard
  - Create real-time session tracking
  - Build WebSocket-powered dashboard updates
  - Implement session detail views
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

- [ ] 8.1 Create session data models and services
  - Implement Session model with comprehensive fields
  - Create SessionService for session operations
  - Set up DynamoDB GSI for efficient queries
  - _Requirements: 6.1, 6.6_

- [ ] 8.2 Implement WebSocket server for live updates
  - Create WebSocket endpoint for dashboard updates
  - Set up real-time session event broadcasting
  - Implement user authentication for WebSocket connections
  - _Requirements: 6.2, 6.3, 6.7_

- [ ] 8.3 Build live sessions API endpoints
  - Create GET /api/sessions/live endpoint
  - Create GET /api/sessions endpoint with filtering
  - Create GET /api/sessions/{session_id} endpoint
  - _Requirements: 6.1, 6.4_

- [ ] 8.3.5 Create dashboard layout with Oratio design system
  - Build dashboard layout component following frontend/public/design/dashboard.html structure
  - Implement fixed sidebar navigation with Oratio logo from frontend/public/oratio_light.png (light mode) and frontend/public/oratio_dark.png (dark mode)
  - Create sidebar with rounded corners, backdrop blur, and shadow effects
  - Add navigation items: Agents (users icon), Sessions (layout icon), Analytics (pie-chart icon), Settings (settings icon)
  - Style active navigation item with primary/20 background and glowing shadow effect
  - Implement hover states with smooth transitions and scale effects
  - Create main content area with proper spacing (ml-32 for sidebar offset)
  - Use Lucide React icons for consistent iconography
  - Apply Oratio corner motif (oratio-corner class) to key UI elements
  - _Requirements: 6.1, 6.3_

- [ ] 8.4 Create live sessions dashboard frontend
  - Build real-time sessions list with WebSocket updates following frontend/public/design/dashboard.html layout
  - Create session detail modal with transcript view using Oratio arch motif and rounded corners
  - Implement filtering and search functionality with pill-shaped inputs and oratio-corner-top-left styling
  - Display agent cards in grid layout (1 col mobile, 2 cols tablet, 3 cols desktop) with hover lift effects
  - Add agent avatar with animated border on hover and status badges (Active/Paused)
  - Create "Create New Agent" card with dashed border, hover effects, and centered icon
  - Apply voice waveform animations and glowing hover states for active sessions
  - Use shadcn/ui Card, Badge, and Button components with Oratio styling
  - _Requirements: 6.1, 6.3, 6.4, 6.5_

- [ ]* 8.5 Write session monitoring unit tests
  - Test WebSocket connection and broadcasting
  - Test session query and filtering logic
  - Test real-time update functionality
  - _Requirements: 6.2, 6.6, 6.7_

- [ ] 9. Implement human handoff notification system
  - Create handoff condition detection
  - Implement notification creation and delivery
  - Build notification management interface
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [ ] 9.1 Create notification data models and services
  - Implement Notification model with metadata
  - Create NotificationService for notification operations
  - Set up handoff condition configuration
  - _Requirements: 7.1, 7.2_

- [ ] 9.2 Implement handoff detection logic
  - Create handoff condition evaluation engine
  - Set up trigger detection in voice and text services
  - Implement session status updates for handoffs
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 9.3 Create notification delivery system
  - Implement SES integration for email notifications
  - Set up WebSocket broadcasting for real-time alerts
  - Create notification persistence in DynamoDB
  - _Requirements: 7.4, 7.5_

- [ ] 9.4 Build notification management endpoints
  - Create GET /api/notifications endpoint
  - Create PATCH /api/notifications/{id}/read endpoint
  - Create PATCH /api/notifications/{id}/acknowledge endpoint
  - _Requirements: 7.6, 7.7_

- [ ] 9.5 Create notification center frontend
  - Build notification list with unread indicators
  - Create notification detail view with actions
  - Implement real-time notification updates
  - _Requirements: 7.5, 7.6, 7.7_

- [ ]* 9.6 Write notification system unit tests
  - Test handoff condition detection
  - Test notification delivery mechanisms
  - Test notification management operations
  - _Requirements: 7.2, 7.4, 7.7_

- [ ] 10. Implement session history and analytics
  - Create session history querying and filtering
  - Build analytics dashboard with metrics
  - Implement audio recording playback
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ] 10.1 Create session history API endpoints
  - Implement GET /api/sessions with advanced filtering
  - Create GET /api/sessions/{id}/transcript endpoint
  - Set up efficient DynamoDB queries with GSI
  - _Requirements: 9.1, 9.5, 9.6_

- [ ] 10.2 Implement audio recording management
  - Set up S3 integration for audio file storage
  - Create secure audio file access with signed URLs
  - Implement audio recording download functionality
  - _Requirements: 9.3_

- [ ] 10.3 Build session analytics logic
  - Create metrics calculation for duration and message count
  - Implement handoff status tracking and reporting
  - Set up usage pattern analysis
  - _Requirements: 9.4, 9.7_

- [ ] 10.4 Create session history frontend
  - Build session history table with sorting and filtering
  - Create session detail view with full transcript
  - Implement audio playback component
  - Add analytics dashboard with charts
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ]* 10.5 Write session history unit tests
  - Test session querying and filtering logic
  - Test audio recording access and security
  - Test analytics calculation accuracy
  - _Requirements: 9.5, 9.6, 9.7_

- [ ] 11. Implement agent configuration management
  - Create agent configuration update interface
  - Implement configuration validation and persistence
  - Set up agent pause/resume functionality
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [ ] 11.1 Create agent configuration API endpoints
  - Implement PATCH /api/agents/{id}/config endpoint
  - Create PUT /api/agents/{id}/pause endpoint
  - Create PUT /api/agents/{id}/resume endpoint
  - Set up configuration validation logic
  - _Requirements: 8.2, 8.5_

- [ ] 11.2 Implement configuration update logic
  - Create voice configuration update handling
  - Implement handoff condition modification
  - Set up agent redeployment detection and notification
  - _Requirements: 8.3, 8.4, 8.7_

- [ ] 11.3 Build agent configuration frontend
  - Create agent settings page with form validation
  - Implement voice configuration interface
  - Add handoff condition management
  - Create agent pause/resume controls
  - _Requirements: 8.1, 8.2, 8.5_

- [ ] 11.4 Implement agent deletion and archival
  - Create agent deletion logic with data archival
  - Implement API key revocation on deletion
  - Set up proper cleanup of associated resources
  - _Requirements: 8.6_

- [ ]* 11.5 Write configuration management unit tests
  - Test configuration validation and updates
  - Test agent pause/resume functionality
  - Test deletion and cleanup logic
  - _Requirements: 8.2, 8.5, 8.6_

- [ ] 12. Implement security and tenant isolation
  - Set up comprehensive security middleware
  - Implement tenant isolation validation
  - Create audit logging and monitoring
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7_

- [ ] 12.1 Create security middleware and validation
  - Implement tenant isolation middleware for all endpoints
  - Set up input sanitization and validation
  - Create resource ownership verification
  - _Requirements: 12.2, 12.6, 12.7_

- [ ] 12.2 Implement secure data access patterns
  - Set up S3 bucket policies with user-specific prefixes
  - Create DynamoDB access patterns with userId filtering
  - Implement API key validation with agent ownership
  - _Requirements: 12.1, 12.2, 12.3_

- [ ] 12.3 Create audit logging system
  - Implement comprehensive operation logging
  - Set up CloudWatch integration for monitoring
  - Create security event detection and alerting
  - _Requirements: 12.5_

- [ ] 12.4 Implement error handling with security focus
  - Create secure error responses without information leakage
  - Set up proper HTTP status codes and messages
  - Implement rate limiting and abuse prevention
  - _Requirements: 12.4, 12.7_

- [ ]* 12.5 Write security unit tests
  - Test tenant isolation enforcement
  - Test input validation and sanitization
  - Test resource ownership verification
  - _Requirements: 12.2, 12.6, 12.7_

- [ ] 13. Set up CI/CD pipeline with GitHub Actions
  - Create GitHub Actions workflows for linting, testing, and deployment
  - Implement Python linting with Ruff for backend and CDK
  - Set up TypeScript/ESLint for frontend validation
  - Configure automated CDK deployment pipeline
  - _Requirements: All requirements for production readiness_

- [ ] 13.1 Create GitHub Actions workflow for backend linting
  - Set up Ruff linting for Python backend code
  - Configure Ruff rules for code quality and formatting
  - Add workflow trigger on pull requests and pushes to main
  - Include type checking with mypy
  - _Requirements: Code quality standards_

- [ ] 13.2 Create GitHub Actions workflow for frontend linting
  - Set up ESLint and TypeScript checking for Next.js frontend
  - Configure Prettier for code formatting
  - Add workflow trigger on pull requests and pushes to main
  - Include build validation step
  - _Requirements: Code quality standards_

- [ ] 13.3 Create GitHub Actions workflow for CDK validation
  - Set up Ruff linting for Python CDK infrastructure code
  - Add CDK synth validation step
  - Include CDK diff check for infrastructure changes
  - Configure workflow to run on infrastructure file changes
  - _Requirements: Infrastructure validation_

- [ ] 13.4 Create GitHub Actions workflow for CDK deployment
  - Set up automated CDK deployment to staging environment
  - Configure AWS credentials using OIDC or secrets
  - Add approval gate for production deployments
  - Include rollback mechanism on deployment failures
  - _Requirements: Automated deployment_

- [ ] 13.5 Create GitHub Actions workflow for testing
  - Set up pytest execution for backend unit tests
  - Configure frontend test execution with Jest/Vitest
  - Add test coverage reporting
  - Fail workflow if coverage drops below threshold
  - _Requirements: Automated testing_

- [ ] 14. Set up monitoring and observability
  - Configure production monitoring and alerting
  - Implement health checks and observability
  - Set up logging and tracing infrastructure
  - _Requirements: All requirements for production readiness_

- [ ] 14.1 Create production deployment configuration
  - Set up AWS CDK production stacks with proper tagging
  - Configure environment-specific settings (dev/staging/prod)
  - Implement infrastructure versioning and change tracking
  - _Requirements: Production deployment_

- [ ] 14.2 Implement monitoring and observability
  - Set up CloudWatch dashboards and alarms
  - Create custom metrics for business logic
  - Implement distributed tracing with X-Ray
  - Configure log aggregation and retention policies
  - _Requirements: Production monitoring_

- [ ] 14.3 Create health check endpoints
  - Implement service health endpoints for backend API
  - Set up database connectivity checks
  - Create dependency health monitoring (AWS services)
  - Add readiness and liveness probes
  - _Requirements: Production reliability_

- [ ]* 14.4 Write integration tests for production readiness
  - Create end-to-end workflow tests
  - Test deployment pipeline functionality
  - Validate monitoring and alerting systems
  - _Requirements: Production quality assurance_