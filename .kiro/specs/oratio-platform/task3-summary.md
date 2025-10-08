# Task 3: Agent Creation Service - Implementation Summary

## Overview
This task implements the complete agent creation workflow, from user submission to deployed AgentCore agent.

## Architecture Flow

```
User Submits Form
    ↓
FastAPI Backend (/api/agents POST)
    ↓
1. Upload files to S3 (with userId, agentId tags)
2. Create KB entry in DynamoDB (status="notready")
3. Create Agent entry in DynamoDB (status="creating")
4. Trigger Step Functions
    ↓
Step Functions Workflow:
    ↓
Lambda 1: KB Provisioner
    - Create Bedrock Knowledge Base (with userId tag)
    - Configure S3 data source
    - Start ingestion job
    - Update KB status to "ready"
    ↓
Lambda 2: AgentCreator Invoker
    - Invoke AgentCreator meta-agent
    - Pass SOP, KB ID, descriptions, folderFileDescriptions (nested)
    - AgentCreator generates:
      * agent_file.py (Strands agent for business logic)
      * prompt.md (system prompt for Nova Sonic)
    - Store both files to S3 (with userId, agentId tags)
    - Update agent with agentCodeS3Path and generatedPromptS3Path
    ↓
Lambda 3: Code Checker (in loop)
    - Check if code exists in S3
    - Return codeReady status
    ↓
Lambda 4: AgentCore Deployer
    - Deploy agent to AgentCore (with userId, agentId tags)
    - Update agent status to "active"
    - Generate endpoints
```

## New Database Tables

### oratio-knowledgebases
- **PK**: knowledgeBaseId (UUID)
- **Attributes**: userId, s3Path, bedrockKnowledgeBaseId, status, folderFileDescriptions, createdAt, updatedAt
- **GSI**: userId-index (for querying user's KBs)

### oratio-agents (updated schema)
- **PK**: userId
- **SK**: agentId
- **New Attributes**: 
  - knowledgeBaseId (reference)
  - sop (user-provided)
  - knowledgeBaseDescription (when to use KB)
  - humanHandoffDescription (when to escalate)
  - generatedPromptS3Path (path to prompt.md for voice agents)
  - agentCodeS3Path (path to agent_file.py - Strands agent)

## S3 Bucket Structure

```
oratio-knowledge-bases/
  {userId}/
    {agentId}/
      document1.pdf
      document2.md
      folder/
        file.txt

oratio-generated-code/
  {userId}/
    {agentId}/
      agent_file.py  # Strands agent code for business logic
      prompt.md      # System prompt for Nova Sonic voice agent
```

## Resource Tagging

All created resources include tags:
- **S3 Objects**: userId, agentId, resourceType
- **Bedrock KB**: userId, platform, environment
- **AgentCore Agent**: userId, agentId, platform, environment

## API Endpoints

### POST /api/agents
**Request** (multipart/form-data):
```json
{
  "agentName": "Customer Service Agent",
  "agentType": "voice",
  "sop": "Handle customer inquiries...",
  "knowledgeBaseDescription": "Use KB for product info",
  "humanHandoffDescription": "Escalate for refunds",
  "folderFileDescriptions": "{\"products\": {\"catalog.pdf\": \"Product catalog\", \"specs.md\": \"Technical specs\"}, \"faq.txt\": \"Common questions\"}",
  "files": [File, File, ...]
}
```

**Note**: 
- `folderFileDescriptions` is a JSON string with nested structure
- No `voiceConfig` or `textConfig` - AgentCreator generates the prompt
- Files are uploaded and matched with descriptions by path

**Response**:
```json
{
  "agentId": "uuid",
  "status": "creating",
  "message": "Agent creation started"
}
```

### GET /api/agents
**Response**:
```json
{
  "agents": [
    {
      "agentId": "uuid",
      "agentName": "Customer Service Agent",
      "status": "active",
      "agentType": "voice",
      "createdAt": 1234567890,
      "websocketUrl": "wss://...",
      "apiEndpoint": "https://..."
    }
  ]
}
```

### GET /api/agents/{agentId}
**Response**:
```json
{
  "agentId": "uuid",
  "agentName": "Customer Service Agent",
  "status": "active",
  "agentType": "voice",
  "sop": "Handle customer inquiries...",
  "knowledgeBaseDescription": "Use KB for product info",
  "humanHandoffDescription": "Escalate for refunds",
  "generatedPromptS3Path": "s3://oratio-generated-code/{userId}/{agentId}/prompt.md",
  "agentCodeS3Path": "s3://oratio-generated-code/{userId}/{agentId}/agent_file.py",
  "knowledgeBase": {
    "knowledgeBaseId": "uuid",
    "status": "ready",
    "bedrockKnowledgeBaseId": "bedrock-kb-id"
  },
  "createdAt": 1234567890,
  "updatedAt": 1234567890,
  "websocketUrl": "wss://...",
  "apiEndpoint": "https://..."
}
```

## Implementation Tasks

### 3.1 - Update DynamoDB Schema ✓
- Add oratio-knowledgebases table
- Document updated agents table schema

### 3.2 - Create Backend Models ✓
- KnowledgeBase model
- Updated Agent model

### 3.3 - Create AWS Client Wrappers ✓
- S3 client (with tagging)
- DynamoDB client
- Bedrock client (with tagging)
- Step Functions client

### 3.4 - Create Backend Services ✓
- KnowledgeBaseService
- AgentService
- S3Service

### 3.5 - Create API Endpoint ✓
- POST /api/agents (with file upload)

### 3.6 - Create Listing Endpoints ✓
- GET /api/agents
- GET /api/agents/{agentId}

### 3.7 - Implement KB Provisioner Lambda ✓
- Create Bedrock KB with tagging
- Configure S3 data source
- Start ingestion

### 3.8 - Implement AgentCreator Invoker Lambda ✓
- Invoke AgentCreator meta-agent
- Store generated code and prompt

### 3.9 - Implement Code Checker Lambda ✓
- Check S3 for generated code

### 3.10 - Implement AgentCore Deployer Lambda ✓
- Deploy to AgentCore with tagging
- Update agent status

### 3.11 - Create Step Functions Workflow ✓
- Orchestrate all lambdas
- Error handling and retries

### 3.12 - Update CDK Infrastructure ✓
- Define Lambda functions
- Configure IAM permissions
- Deploy via CDK

### 3.13 - Write Unit Tests (Optional) ✓
- Test services and workflows

## Key Considerations

1. **Tenant Isolation**: All operations validate userId from JWT
2. **Resource Tagging**: All AWS resources tagged for cost tracking
3. **Error Handling**: Comprehensive error handling at each step
4. **Status Tracking**: Agent status updated throughout workflow
5. **Idempotency**: Operations should be idempotent where possible
6. **Security**: No sensitive data in logs, proper IAM permissions

## Voice Agent Architecture (Future Task 5)

Based on `sonic_example.py`, the voice service will:

```python
# Voice WebSocket Handler
async def handle_voice_websocket(websocket, agent_id, api_key):
    # 1. Authenticate API key
    agent = validate_api_key_and_get_agent(api_key, agent_id)
    
    # 2. Load generated prompt from S3
    prompt = s3.get_object(agent.generatedPromptS3Path)
    
    # 3. Initialize BedrockStreamManager (from sonic_example.py)
    stream_manager = BedrockStreamManager(model_id='amazon.nova-sonic-v1:0')
    await stream_manager.initialize_stream()
    
    # 4. Send system prompt to Nova Sonic
    await stream_manager.send_text_content(prompt)
    
    # 5. Bidirectional audio streaming
    async def receive_audio():
        async for audio_chunk in websocket:
            stream_manager.add_audio_chunk(audio_chunk)
    
    async def send_audio():
        while True:
            audio_output = await stream_manager.audio_output_queue.get()
            await websocket.send(audio_output)
    
    # 6. When Nova Sonic needs business logic (tool use):
    #    - Invoke agent_file.py via AgentCore
    #    - Return result to Nova Sonic
    
    await asyncio.gather(receive_audio(), send_audio())
```

**Key Components**:
- `BedrockStreamManager`: Handles Nova Sonic bidirectional streaming
- `AudioStreamer`: Manages PyAudio input/output (adapted for WebSocket)
- `RxPy Subjects`: Event-driven audio processing
- API Key authentication per WebSocket connection
- Multi-tenant support with userId/agentId isolation

## Next Steps After Task 3

1. **Frontend Integration** (Task 3.6 in original plan)
   - Create agent creation wizard UI
   - Implement file upload component with folder structure
   - Add real-time status updates
   - Build folderFileDescriptions editor (nested structure)

2. **Voice Agent Integration** (Task 5)
   - Implement WebSocket voice service based on sonic_example.py
   - Load prompt.md from S3 and pass to Nova Sonic
   - Integrate agent_file.py invocation for business logic
   - Add API key authentication middleware
   - Handle multiple concurrent voice sessions

3. **Testing and Validation**
   - End-to-end testing of agent creation
   - Load testing for concurrent creations
   - Error scenario testing
   - Voice agent WebSocket testing
