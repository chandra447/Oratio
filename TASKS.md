# Oratio Platform - Hackathon Development Tasks

**Last Updated**: January 2025  
**Timeline**: 6-day sprint to HACKATHON DEMO  
**Current Focus**: Infrastructure deployment + **VOICE INTEGRATION (WOW FACTOR)**  
**Goal**: Live voice demo with Nova Sonic + Chameleon

---

## 📊 Overall Progress

```
Phase 1: Core Infrastructure  ████████████████░░ 85% (IN PROGRESS)
Phase 2: Voice Integration    ░░░░░░░░░░░░░░░░░░  0% (HACKATHON WOW FACTOR!)
Phase 3: Testing & Validation ░░░░░░░░░░░░░░░░░░  0% (AS NEEDED)
Phase 4: Session Management   ░░░░░░░░░░░░░░░░░░  0% (SKIP FOR HACKATHON)
```

---

## 🏆 **HACKATHON STRATEGY**

### **What Makes This Project Win:**
1. ✅ **No-code agent creation** - Upload SOP, get production agent
2. ✅ **Meta-agent architecture** - AI that builds AI (inception!)
3. 🎯 **LIVE VOICE DEMO** - Talk to your custom agent via phone/browser
4. ✅ **Chameleon architecture** - One runtime, infinite agents
5. ✅ **Real memory** - Agent remembers conversation context

### **The "WOW" Demo Flow:**
```
1. Show dashboard → Upload SOP → Agent created in 30 seconds
2. Open phone/browser → Click "Call Agent" button
3. SPEAK to agent (Nova Sonic) → Agent responds in VOICE
4. Agent calls Chameleon for business logic
5. Agent remembers context across conversation
6. Show live transcript + tool calls in dashboard
```

**Judges will lose their minds!** 🤯

---

## 🎯 Current Sprint (Days 1-6)

### **Priority 1: Deploy Infrastructure** ⚡

#### ✅ **COMPLETED**
- [x] AgentCreator meta-agent (DSPy + LangGraph)
  - [x] DSPy signatures (SOP parser, plan drafter/reviewer, code generator/reviewer, prompt generator)
  - [x] LangGraph pipeline with review cycles
  - [x] MCP tools for documentation access
  - [x] Code validation with PythonInterpreter
  - [x] Chameleon-compatible code generation (hooks + state injection)
- [x] Chameleon generic loader
  - [x] Dynamic agent loading from S3
  - [x] Memory hooks injection (MemoryHookProvider)
  - [x] DynamoDB integration for memory_id retrieval
  - [x] actor_id + session_id handling
- [x] Backend API
  - [x] Authentication (Cognito + JWT)
  - [x] Agent CRUD operations
  - [x] Chat endpoint (text conversations)
  - [x] API key management
- [x] Frontend
  - [x] Landing page
  - [x] Login/Signup pages
  - [x] Dashboard layout
  - [x] Agent creation forms
  - [x] Knowledge base upload
  - [x] API key management
  - [x] Protected routes (client-side)
- [x] Infrastructure (CDK)
  - [x] DynamoDB tables (users, agents, API keys, knowledge bases)
  - [x] S3 buckets (knowledge base files, generated code)
  - [x] Cognito User Pool
  - [x] Lambda functions (KB provisioner, AgentCreator invoker)
  - [x] Step Functions workflow
  - [x] IAM roles (AgentCore execution roles)
  - [x] CloudFormation outputs (role ARNs)
- [x] GitHub Actions CI/CD
  - [x] Docker builds (AgentCreator, Chameleon, Backend)
  - [x] ECR push
  - [x] CDK deployment
  - [x] AgentCore runtime deployments
  - [x] SSM Parameter Store (runtime ARNs)

#### 🔄 **IN PROGRESS**
- [ ] **Deploy infrastructure to AWS**
  - [ ] Run GitHub Actions workflow
  - [ ] Verify CDK stack deployment
  - [ ] Verify AgentCore runtimes deployed
  - [ ] Capture outputs (Cognito User Pool ID, API Gateway URL, etc.)
  - [ ] Update frontend `.env.local` with backend URL

---

### **Priority 2: Nova Sonic Voice Integration** 🎙️ **[HACKATHON PRIORITY]**

#### **Backend Voice WebSocket** (Day 2-3)
- [x] **Create `backend/routers/voice.py`** ✅ DONE
  - WebSocket endpoint: `WS /api/v1/voice/{agent_id}/{actor_id}/{session_id}?api_key=xxx`
  - API key validation
  - Nova Sonic stream initialization  
  - Chameleon tool integration
  - Conversation history logging (based on AWS sample)
  - Bidirectional audio streaming

- [ ] **Nova Sonic Configuration**
  ```python
  from bedrock_voice import NovaSonic  # AWS SDK
  
  # Define Chameleon as a tool for Nova Sonic
  chameleon_tool = {
      "name": "business_agent",
      "description": "Invoke custom business logic agent",
      "input_schema": {
          "type": "object",
          "properties": {
              "query": {"type": "string"}
          }
      },
      "invoke": lambda query: invoke_chameleon(agent_id, user_id, actor_id, session_id, query)
  }
  
  voice_agent = NovaSonic(
      memory_id=agent_memory_id,  # From DynamoDB
      actor_id=actor_id,
      session_id=session_id,
      tools=[chameleon_tool],
      voice_config={
          "voice_id": "Joanna",  # AWS Polly voice
          "language": "en-US"
      }
  )
  ```

- [ ] **Chameleon Invocation Helper**
  ```python
  async def invoke_chameleon(agent_id, user_id, actor_id, session_id, prompt):
      """Helper to invoke Chameleon from Nova Sonic tool call"""
      result = invocation_service.invoke_agent(
          runtime_arn=chameleon_runtime_arn,
          agent_id=agent_id,
          user_id=user_id,
          actor_id=actor_id,
          session_id=session_id,
          prompt=prompt
      )
      return result["result"]
  ```

- [ ] **WebSocket Audio Streaming**
  - Accept audio chunks from client (base64 encoded)
  - Forward to Nova Sonic
  - Stream Nova Sonic audio response back to client
  - Handle transcript events for UI

#### **Frontend Voice UI** (Day 3-4)
- [ ] **Create `components/voice-agent.tsx`**
  - [ ] WebSocket connection to `/voice` endpoint
  - [ ] Microphone access (Web Audio API)
  - [ ] Audio recording/streaming
  - [ ] Audio playback from WebSocket
  - [ ] Visual feedback (waveform, speaking indicator)
  - [ ] Live transcript display
  - [ ] "Call Agent" button in dashboard

- [ ] **Audio Handling**
  ```typescript
  // Capture audio from mic
  navigator.mediaDevices.getUserMedia({ audio: true })
  
  // WebSocket for bidirectional streaming
  const ws = new WebSocket(`wss://api.../voice/${agentId}/${actorId}/${sessionId}?api_key=...`)
  
  // Send audio chunks
  ws.send(audioChunkBase64)
  
  // Receive and play audio
  ws.onmessage = (event) => {
      const audioBlob = base64ToBlob(event.data)
      playAudio(audioBlob)
  }
  ```

- [ ] **Real-Time Transcript**
  - Display user speech (from Nova Sonic transcription)
  - Display agent response (text + audio)
  - Show tool calls (when Chameleon is invoked)

#### **Quick Testing** (Day 4)
- [ ] **Test Voice Flow**
  - Open browser → navigate to agent detail page
  - Click "Call Agent"
  - Allow microphone access
  - Speak: "Hello, can you help me?"
  - Verify: Nova Sonic responds with voice
  - Verify: Chameleon tool called (check logs)
  - Verify: Conversation stored in memory

- [ ] **Test Multi-Turn Voice**
  - Speak turn 1: "What's your return policy?"
  - Speak turn 2: "How long does it take?" (should have context)
  - Verify: Agent remembers previous question

---

### **Priority 3: Quick Testing & Demo Prep** 🧪

#### **Authentication Flow** (Critical Path)
- [ ] **Test Cognito Registration**
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password": "Test1234!", "name": "Test User"}'
  ```
  - [ ] Check email for verification code
  - [ ] Verify user created in Cognito User Pool
  - [ ] Verify user record in DynamoDB `oratio-users` table

- [ ] **Test Email Confirmation**
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/confirm \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "confirmation_code": "123456"}'
  ```
  - [ ] Verify user status = `CONFIRMED` in Cognito

- [ ] **Test Login**
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password": "Test1234!"}'
  ```
  - [ ] Receive `access_token`, `id_token`, `refresh_token`
  - [ ] Verify JWT signature
  - [ ] Decode JWT and check claims (`sub`, `email`, `cognito:username`)

- [ ] **Test Protected Endpoint**
  ```bash
  curl -X GET http://localhost:8000/api/v1/auth/me \
    -H "Authorization: Bearer <access_token>"
  ```
  - [ ] Returns user profile
  - [ ] Test with invalid token (should return 401)
  - [ ] Test with expired token (should return 401)

#### **Agent Creation Flow** (Critical Path)
- [ ] **Test Agent Creation**
  ```bash
  curl -X POST http://localhost:8000/api/v1/agents \
    -H "Authorization: Bearer <access_token>" \
    -H "Content-Type: multipart/form-data" \
    -F "name=CustomerSupportAgent" \
    -F "description=Handles customer inquiries" \
    -F "sop=@sop.txt" \
    -F "knowledge_base_description=Product catalog and FAQs" \
    -F "human_handoff_description=Escalate complex issues"
  ```
  - [ ] Verify Step Functions execution started
  - [ ] Monitor Step Functions in AWS Console
  - [ ] Wait for `kb_provisioner` Lambda (creates Bedrock KB)
  - [ ] Wait for `agentcreator_invoker` Lambda (generates code + creates memory)
  - [ ] Verify agent status = `active` in DynamoDB
  - [ ] Verify agent code in S3 at `s3://<CODE_BUCKET>/<user_id>/<agent_id>/agent_file.py`
  - [ ] Verify `memory_id` field populated in DynamoDB
  - [ ] Verify `agentcore_runtime_arn` = Chameleon ARN

- [ ] **Test Agent Listing**
  ```bash
  curl -X GET http://localhost:8000/api/v1/agents \
    -H "Authorization: Bearer <access_token>"
  ```
  - [ ] Returns list of agents for user
  - [ ] Verify all fields present (id, name, status, created_at, etc.)

#### **Chat Flow** (Critical Path)
- [ ] **Test API Key Creation**
  ```bash
  curl -X POST http://localhost:8000/api/v1/agents/<agent_id>/api-keys \
    -H "Authorization: Bearer <access_token>" \
    -H "Content-Type: application/json" \
    -d '{"name": "Test Key", "permissions": ["CHAT"]}'
  ```
  - [ ] Receive API key (format: `oratio_...`)
  - [ ] Verify key stored in DynamoDB with hash

- [ ] **Test Chat Endpoint**
  ```bash
  curl -X POST http://localhost:8000/api/v1/chat/<agent_id>/<actor_id>/<session_id> \
    -H "X-API-Key: oratio_..." \
    -H "Content-Type: application/json" \
    -d '{"message": "Hello, can you help me?"}'
  ```
  - [ ] Verify Chameleon invoked (check CloudWatch logs)
  - [ ] Verify agent code loaded from S3
  - [ ] Verify memory hooks injected
  - [ ] Verify response returned
  - [ ] Verify conversation stored in Memory API

- [ ] **Test Multi-Turn Conversation**
  ```bash
  # Turn 1
  curl -X POST http://localhost:8000/api/v1/chat/<agent_id>/customer-john/session-123 \
    -H "X-API-Key: oratio_..." \
    -d '{"message": "What's your return policy?"}'
  
  # Turn 2 (same session)
  curl -X POST http://localhost:8000/api/v1/chat/<agent_id>/customer-john/session-123 \
    -H "X-API-Key: oratio_..." \
    -d '{"message": "How long does it take?"}'
  ```
  - [ ] Verify second message has context from first
  - [ ] Verify both turns stored in Memory API
  - [ ] Query Memory API directly to verify:
    ```python
    from bedrock_agentcore.memory import MemoryClient
    memory_client = MemoryClient()
    turns = memory_client.get_last_k_turns(
        memory_id="<agent_memory_id>",
        actor_id="customer-john",
        session_id="session-123",
        k=10
    )
    print(turns)
    ```

- [ ] **Test Multiple Actors (Isolation)**
  ```bash
  # Actor 1
  curl -X POST .../chat/<agent_id>/customer-john/session-a ...
  
  # Actor 2
  curl -X POST .../chat/<agent_id>/customer-jane/session-b ...
  ```
  - [ ] Verify conversations are isolated
  - [ ] Verify each actor has separate history

---

### **Priority 3: Frontend Integration** 🖥️

- [ ] **Update Frontend Environment**
  - [ ] Set `NEXT_PUBLIC_API_URL` to deployed backend URL
  - [ ] Set `NEXT_PUBLIC_COGNITO_USER_POOL_ID`
  - [ ] Set `NEXT_PUBLIC_COGNITO_CLIENT_ID`

- [ ] **Test Frontend Auth Flow**
  - [ ] Sign up → receive email → confirm → login
  - [ ] Verify JWT stored in localStorage
  - [ ] Verify protected routes redirect to login
  - [ ] Verify dashboard loads after login

- [ ] **Test Frontend Agent Creation**
  - [ ] Navigate to `/dashboard/agents/create`
  - [ ] Fill form + upload SOP file
  - [ ] Submit and verify agent appears in `/dashboard/agents`
  - [ ] Verify agent status progresses: `creating` → `active`

- [ ] **Test Frontend Chat (Future)**
  - [ ] Create chat UI component
  - [ ] Integrate with `/chat` endpoint
  - [ ] Display conversation history

---

## 📦 Post-MVP (Phase 3)

### **Session Management API**

#### **New Endpoints**
- [ ] `GET /api/v1/agents/{agent_id}/sessions`
  - List all sessions for an agent
  - Query Memory API for session list
  - Return: `[{actor_id, session_id, last_message_at, message_count}]`

- [ ] `GET /api/v1/agents/{agent_id}/sessions/{actor_id}/{session_id}`
  - Get full conversation history
  - Query Memory API for turns
  - Return: `[{role, content, timestamp}]`

- [ ] `GET /api/v1/agents/{agent_id}/analytics`
  - Basic stats: total sessions, total messages, active sessions
  - Aggregate from Memory API

#### **Frontend Dashboard**
- [ ] Sessions list view (table with filters)
- [ ] Session detail view (conversation transcript)
- [ ] Real-time updates (optional, using WebSocket + RxPy)

---

## 🎙️ Future (Phase 4)

### **Voice Integration**

#### **Backend**
- [ ] **Create `routers/voice.py`**
  - [ ] WebSocket endpoint: `WS /voice/{agent_id}/{actor_id}/{session_id}`
  - [ ] Validate API key via query param
  - [ ] Initialize Nova Sonic with Chameleon as tool
  - [ ] Bidirectional audio streaming

- [ ] **Nova Sonic Configuration**
  - [ ] Configure Chameleon as tool for Nova Sonic
  - [ ] Set up memory hooks (per-agent memory_id)
  - [ ] Handle transcription → agent logic → synthesis

#### **Frontend**
- [ ] WebSocket client for voice streaming
- [ ] Audio capture (Web Audio API)
- [ ] Audio playback
- [ ] Voice UI component (waveform, recording indicator)

---

## 🐛 Known Issues / Tech Debt

### **High Priority**
- [ ] **Error handling in Chameleon**
  - Add retry logic for S3 failures
  - Add better error messages for missing memory_id

- [ ] **AgentCreator timeout handling**
  - Current Lambda timeout: 15 minutes
  - If code generation takes >15min, invocation fails
  - Solution: Use Step Functions Activity or async invoke

- [ ] **API Key hashing**
  - Currently using SHA-256
  - Consider bcrypt for stronger security

### **Medium Priority**
- [ ] **Rate limiting**
  - No rate limiting on chat endpoint
  - Add Redis + rate limiter middleware

- [ ] **Logging improvements**
  - Structured logging (JSON)
  - Correlation IDs across services
  - Centralized log aggregation (CloudWatch Logs Insights)

- [ ] **Frontend error boundaries**
  - Add React error boundaries
  - Better error messages for users

### **Low Priority**
- [ ] **Token refresh in frontend**
  - Implement automatic token refresh
  - Currently requires re-login after expiry

- [ ] **Agent update/delete**
  - No update/delete endpoints yet
  - Implement PATCH /agents/{id} and DELETE /agents/{id}

---

## 📝 Task Management in Cursor

**Cursor doesn't have built-in task management**, but you can use:

### **Option 1: TODO Comments**
```python
# TODO: Add retry logic for S3 failures
# FIXME: Memory client initialization fails if region not set
# NOTE: This assumes actor_id is always provided
```

Then search with Cursor: `Cmd+Shift+F` → search for `TODO`, `FIXME`, etc.

### **Option 2: GitHub Issues**
- Create issues in GitHub repo
- Link commits to issues with `Closes #123`
- Track progress in Projects board

### **Option 3: This TASKS.md File**
- Keep this file updated with checkboxes
- Review daily and mark completed items
- Add new tasks as they arise

---

## 📅 **6-Day Hackathon Timeline**

### **Day 1 (Today): Deploy & Validate Core** ⚡
1. Deploy infrastructure (30 min)
2. Test Cognito auth (30 min)
3. Create test agent (1 hour)
4. Test text chat (30 min)
5. Verify Chameleon works (30 min)

### **Day 2: Nova Sonic Backend** 🎙️
1. Research Nova Sonic SDK (1 hour)
2. Create `voice.py` WebSocket (2 hours)
3. Configure Chameleon tool (2 hours)
4. Test with mock audio (1 hour)

### **Day 3: Nova Sonic Frontend** 🖥️
1. Create voice UI component (2 hours)
2. Web Audio API (mic) (2 hours)
3. WebSocket client (2 hours)
4. Visual feedback + transcript (2 hours)

### **Day 4: Integration** ✨
1. End-to-end voice testing (2 hours)
2. Bug fixes (3 hours)
3. UI polish (2 hours)

### **Day 5: Demo Prep** 🎬
1. Demo script + practice (3 hours)
2. Record video (2 hours)
3. Slides (2 hours)

### **Day 6: Submission** 🚀
1. Final testing (2 hours)
2. Deploy production (1 hour)
3. Submit + Q&A prep (3 hours)

---

## 🎯 **Demo Script (4 Minutes)**

**Opening**: "Watch us create a production voice agent in 30 seconds"

**Show**: Dashboard → Upload SOP → Agent ready

**WOW**: Click "Call Agent" → SPEAK → Agent responds in VOICE → Show tool calls

**Close**: "From SOP to voice agent in 30 seconds. That's Oratio."

---

## 🎯 **START NOW**

1. ✅ Deploy infrastructure (GitHub Actions)
2. ✅ Research Nova Sonic SDK
3. ✅ Create `voice.py` skeleton
4. ✅ Test text chat works
5. ✅ Plan voice UI

---

## 📞 Resources

- **Nova Sonic Docs**: https://docs.aws.amazon.com/bedrock/latest/userguide/nova-sonic.html
- **Strands Docs**: https://strandsagents.com/
- **Web Audio API**: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API

---

**LET'S WIN THIS HACKATHON! 🏆🚀**

