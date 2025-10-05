# Requirements Document

## Introduction

Oratio is a multi-tenant SaaS platform that enables enterprises to create, deploy, and manage voice and conversational AI agents without writing code. The platform leverages AWS AgentCore for agent deployment, AWS Bedrock (Nova Sonic for voice, Claude for text), and provides a comprehensive dashboard for monitoring live interactions. Users provide SOPs (Standard Operating Procedures) and knowledge bases, and the platform automatically generates, deploys, and manages custom AI agents with REST API and WebSocket endpoints.

## Requirements

### Requirement 1: User Authentication and Multi-Tenancy

**User Story:** As an enterprise user, I want to register and log into the Oratio platform securely, so that I can manage my organization's AI agents in isolation from other tenants.

#### Acceptance Criteria

1. WHEN a new user registers THEN the system SHALL create a user account in AWS Cognito User Pool with email verification
2. WHEN a user logs in with valid credentials THEN Cognito SHALL issue JWT tokens (ID token, access token, refresh token)
3. WHEN a user makes API requests THEN the system SHALL validate the Cognito JWT token and extract userId from token claims
4. WHEN a user is created in Cognito THEN the system SHALL create a corresponding user profile in DynamoDB with organizationName and metadata
5. IF a user provides invalid credentials THEN Cognito SHALL reject the login attempt with appropriate error messaging
6. WHEN a user's access token expires THEN the system SHALL accept the refresh token to issue new tokens without re-authentication
7. WHEN a user makes API requests THEN the system SHALL enforce tenant isolation using the userId from Cognito token claims

### Requirement 2: Agent Creation with SOP and Knowledge Base

**User Story:** As an enterprise user, I want to create a new AI agent by providing an SOP and uploading knowledge base documents, so that the agent can handle conversations according to my business requirements.

#### Acceptance Criteria

1. WHEN a user submits an agent creation form with SOP and documents THEN the system SHALL validate inputs and initiate the agent creation workflow
2. WHEN documents are uploaded THEN the system SHALL store them in S3 under the user's isolated namespace
3. WHEN the agent creation workflow starts THEN the system SHALL create a Bedrock Knowledge Base and ingest the uploaded documents
4. WHEN the Knowledge Base is ready THEN the system SHALL invoke the AgentCreator meta-agent to generate custom agent code
5. WHEN agent code is generated THEN the system SHALL deploy the agent to AWS AgentCore
6. WHEN deployment completes THEN the system SHALL update the agent status to "active" and provide API credentials
7. IF any step fails THEN the system SHALL update the agent status to "failed" and log detailed error information
8. WHEN agent creation is in progress THEN the system SHALL provide real-time status updates to the user interface

### Requirement 3: Voice Agent with WebSocket Communication

**User Story:** As an enterprise user, I want my deployed agent to support voice interactions via WebSocket, so that my customers can have real-time voice conversations with the AI agent.

#### Acceptance Criteria

1. WHEN a voice agent is created THEN the system SHALL provision a unique WebSocket endpoint for that agent
2. WHEN a customer connects to the WebSocket endpoint with valid API key THEN the system SHALL establish a bidirectional audio streaming connection
3. WHEN audio data is received from the customer THEN the system SHALL process it using Nova Sonic model
4. WHEN Nova Sonic generates a response THEN the system SHALL invoke the deployed AgentCore agent for decision-making
5. WHEN the AgentCore agent returns a response THEN the system SHALL stream the audio back to the customer
6. WHEN a voice session is active THEN the system SHALL create and update a session record in DynamoDB
7. WHEN a voice session ends THEN the system SHALL save the transcript and audio recording to S3
8. IF the WebSocket connection drops THEN the system SHALL handle reconnection gracefully and maintain session continuity

### Requirement 4: Text Agent with REST API

**User Story:** As an enterprise user, I want my deployed agent to support text conversations via REST API, so that my applications can integrate conversational AI capabilities.

#### Acceptance Criteria

1. WHEN a text agent is created THEN the system SHALL provision a unique REST API endpoint for that agent
2. WHEN a customer sends a message with valid API key THEN the system SHALL authenticate and process the request
3. WHEN a text message is received THEN the system SHALL invoke the deployed AgentCore agent with conversation context
4. WHEN the AgentCore agent returns a response THEN the system SHALL return it with relevant knowledge base sources
5. WHEN a conversation session exists THEN the system SHALL maintain conversation history across multiple requests
6. IF no session ID is provided THEN the system SHALL create a new session automatically
7. WHEN a text session is updated THEN the system SHALL persist the conversation state in DynamoDB

### Requirement 5: API Key Management

**User Story:** As an enterprise user, I want to generate and manage API keys for my agents, so that I can control access to my deployed agents securely.

#### Acceptance Criteria

1. WHEN a user requests a new API key THEN the system SHALL generate a unique key and store its hash in DynamoDB
2. WHEN an API key is created THEN the system SHALL display it once to the user and never show it again
3. WHEN a customer uses an API key THEN the system SHALL validate it against the hashed value in the database
4. WHEN a user views their API keys THEN the system SHALL display key metadata without revealing the actual key value
5. WHEN a user revokes an API key THEN the system SHALL mark it as inactive and reject future requests using that key
6. WHEN an API key is used THEN the system SHALL update the last used timestamp and usage count
7. IF an invalid API key is provided THEN the system SHALL reject the request with a 401 Unauthorized response

### Requirement 6: Live Session Monitoring Dashboard

**User Story:** As an enterprise user, I want to view live voice calls and text conversations in real-time, so that I can monitor how my agents are performing and intervene when necessary.

#### Acceptance Criteria

1. WHEN a user opens the live sessions dashboard THEN the system SHALL display all active sessions for their agents
2. WHEN a new session starts THEN the system SHALL push an update to the dashboard via WebSocket
3. WHEN a session is active THEN the system SHALL display real-time transcript updates as messages are exchanged
4. WHEN a user selects a session THEN the system SHALL display detailed information including customer metadata and conversation history
5. WHEN a session ends THEN the system SHALL update the dashboard to reflect the completed status
6. WHEN the dashboard loads THEN the system SHALL query DynamoDB for active sessions and establish WebSocket connection for updates
7. IF the WebSocket connection is lost THEN the system SHALL attempt to reconnect automatically

### Requirement 7: Human Handoff Notifications

**User Story:** As an enterprise user, I want to receive notifications when an agent needs to escalate to a human, so that I can provide timely assistance to customers.

#### Acceptance Criteria

1. WHEN a user configures an agent THEN the system SHALL allow specification of handoff conditions
2. WHEN a handoff condition is detected during a conversation THEN the system SHALL create a notification record in DynamoDB
3. WHEN a handoff is triggered THEN the system SHALL update the session status to "handoff_requested"
4. WHEN a handoff notification is created THEN the system SHALL send an email via SES to the user
5. WHEN a handoff notification is created THEN the system SHALL push a real-time alert to connected dashboard users via WebSocket
6. WHEN a user views notifications THEN the system SHALL display unread notifications prominently
7. WHEN a user acknowledges a notification THEN the system SHALL mark it as read and update the status

### Requirement 8: Agent Configuration Management

**User Story:** As an enterprise user, I want to view and update my agent configurations, so that I can modify behavior and settings without recreating the agent.

#### Acceptance Criteria

1. WHEN a user views an agent THEN the system SHALL display all configuration details including SOP, voice settings, and handoff conditions
2. WHEN a user updates agent configuration THEN the system SHALL validate changes and persist them to DynamoDB
3. WHEN voice configuration is updated THEN the system SHALL apply changes to the voice service without requiring redeployment
4. WHEN handoff conditions are modified THEN the system SHALL update the detection logic for future sessions
5. WHEN a user pauses an agent THEN the system SHALL reject new session requests with appropriate messaging
6. WHEN a user deletes an agent THEN the system SHALL archive the agent data and revoke all associated API keys
7. IF configuration changes require agent redeployment THEN the system SHALL notify the user and provide an option to redeploy

### Requirement 9: Session History and Analytics

**User Story:** As an enterprise user, I want to view historical sessions and analytics, so that I can understand usage patterns and improve my agents.

#### Acceptance Criteria

1. WHEN a user views session history THEN the system SHALL display completed sessions with filtering and sorting options
2. WHEN a user selects a historical session THEN the system SHALL display the complete transcript and metadata
3. WHEN a voice session is selected THEN the system SHALL provide a link to download the audio recording from S3
4. WHEN viewing session history THEN the system SHALL display metrics including duration, message count, and handoff status
5. WHEN filtering sessions THEN the system SHALL support filtering by agent, date range, session type, and status
6. WHEN querying session history THEN the system SHALL use DynamoDB GSI for efficient queries by agent and timestamp
7. IF a session has associated handoff events THEN the system SHALL display the handoff reason and outcome

### Requirement 10: AgentCreator Meta-Agent Pipeline

**User Story:** As the platform, I want to automatically generate custom agent code from user-provided SOPs, so that agents are architecturally sound and follow best practices.

#### Acceptance Criteria

1. WHEN the AgentCreator is invoked THEN the system SHALL parse the SOP and extract key requirements
2. WHEN SOP parsing completes THEN the system SHALL generate an initial agent implementation plan
3. WHEN a plan is drafted THEN the system SHALL review it through multiple cycles to ensure quality
4. WHEN the plan is approved THEN the system SHALL generate Python code for the AgentCore agent
5. WHEN code is generated THEN the system SHALL review it for correctness and best practices
6. WHEN code review passes THEN the system SHALL write the agent code to S3
7. IF any step fails THEN the system SHALL retry with adjustments and log detailed error information
8. WHEN the pipeline completes THEN the system SHALL notify the deployment Lambda to proceed

### Requirement 11: Step Functions Orchestration

**User Story:** As the platform, I want to orchestrate the agent creation workflow reliably, so that all steps execute in the correct order with proper error handling.

#### Acceptance Criteria

1. WHEN agent creation is triggered THEN the system SHALL start a Step Functions execution
2. WHEN the workflow starts THEN the system SHALL invoke the KB Provisioner Lambda
3. WHEN KB provisioning completes THEN the system SHALL invoke the AgentCreator Invoker Lambda
4. WHEN AgentCreator completes THEN the system SHALL wait and check for generated code in S3
5. WHEN code is available THEN the system SHALL invoke the AgentCore Deployer Lambda
6. WHEN deployment succeeds THEN the system SHALL update the agent status and send notifications
7. IF any step fails THEN the system SHALL execute error handling logic and update the agent status to "failed"
8. WHEN the workflow completes THEN the system SHALL log execution details to CloudWatch

### Requirement 12: Security and Tenant Isolation

**User Story:** As the platform, I want to enforce strict security and tenant isolation, so that user data and agents remain private and secure.

#### Acceptance Criteria

1. WHEN storing data in S3 THEN the system SHALL use user-specific prefixes to isolate tenant data
2. WHEN querying DynamoDB THEN the system SHALL always include userId in the query to enforce tenant boundaries
3. WHEN validating API keys THEN the system SHALL verify the key belongs to the correct agent and user
4. WHEN handling errors THEN the system SHALL not expose sensitive information in error messages
5. WHEN logging operations THEN the system SHALL include userId and agentId for audit trails
6. WHEN a user accesses resources THEN the system SHALL verify ownership before allowing operations
7. IF a user attempts to access another tenant's resources THEN the system SHALL reject the request with a 403 Forbidden response
