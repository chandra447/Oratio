# Memory Architecture - Conversation Continuity

## Overview

The Oratio platform uses **AgentCore Memory** with **hooks** for conversation continuity. Memory management is handled centrally by the **Chameleon generic loader**, not by individual generated agents.

**Reference**: [AWS AgentCore Memory Sample](https://github.com/awslabs/amazon-bedrock-agentcore-samples/blob/main/01-tutorials/04-AgentCore-memory/01-short-term-memory/01-single-agent/with-strands-agent/personal-agent.ipynb)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Chameleon Generic Loader                  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Memory Hook Provider (MemoryHookProvider)         │    │
│  │  - on_agent_initialized: Load conversation history │    │
│  │  - on_message_added: Save new messages             │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Hook & State Injection                             │    │
│  │  hooks = [MemoryHookProvider(client, memory_id)]   │    │
│  │  state = {actor_id, session_id}                     │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Dynamically Load Generated Agent from S3          │    │
│  │  agent_module.invoke(payload, context, hooks, state)│    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Generated Agent Code                       │
│                                                              │
│  def create_orchestrator(hooks=None, state=None):           │
│      return Agent(                                           │
│          system_prompt="...",                                │
│          tools=[...],                                        │
│          hooks=hooks or [],  ← Injected by Chameleon        │
│          state=state or {}   ← Injected by Chameleon        │
│      )                                                       │
│                                                              │
│  def invoke(payload, context, hooks=None, state=None):      │
│      agent = create_orchestrator(hooks=hooks, state=state)  │
│      response = agent({'message': user_message})            │
│      return {'output': str(response)}                       │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. MemoryHookProvider (in Chameleon)

Located in: `agent-creator/generic_loader.py`

```python
class MemoryHookProvider(HookProvider):
    """Memory hook provider for conversation continuity"""
    
    def __init__(self, memory_client: MemoryClient, memory_id: str):
        self.memory_client = memory_client
        self.memory_id = memory_id
    
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """Load recent conversation history when agent starts"""
        actor_id = event.agent.state.get("actor_id")
        session_id = event.agent.state.get("session_id")
        
        # Load last 10 conversation turns
        recent_turns = self.memory_client.get_last_k_turns(
            memory_id=self.memory_id,
            actor_id=actor_id,
            session_id=session_id,
            k=10
        )
        
        # Add to system prompt
        if recent_turns:
            context = format_conversation_history(recent_turns)
            event.agent.system_prompt += f"\n\nRecent conversation:\n{context}"
    
    def on_message_added(self, event: MessageAddedEvent):
        """Store messages in memory"""
        actor_id = event.agent.state.get("actor_id")
        session_id = event.agent.state.get("session_id")
        
        self.memory_client.create_event(
            memory_id=self.memory_id,
            actor_id=actor_id,
            session_id=session_id,
            messages=[...]
        )
```

### 2. Hook & State Injection (in Chameleon)

Located in: `agent-creator/generic_loader.py` (`invoke` function)

```python
# Prepare memory hooks and state for injection
hooks = []
state = {}

if memory_client and MEMORY_ID:
    # Extract session info from payload
    actor_id = payload.get('actor_id', user_id)
    session_id = payload.get('session_id', f"{user_id}_{agent_id}_default")
    
    # Create memory hook provider
    memory_hook = MemoryHookProvider(memory_client, MEMORY_ID)
    hooks.append(memory_hook)
    
    # Set state for agent
    state = {
        "actor_id": actor_id,
        "session_id": session_id
    }

# Call the agent's invoke function with hooks and state injection
result = agent_module.invoke(payload, context, hooks=hooks, state=state)
```

### 3. Generated Agent Pattern

Located in: `agent-creator/agentcreator/signatures/code_generator.py`

**Multi-Agent Example:**
```python
def create_orchestrator(hooks=None, state=None):
    """Create orchestrator agent with optional hooks and state injection."""
    return Agent(
        system_prompt="Route queries to specialists...",
        tools=[specialist1, specialist2, handoff_to_user],
        hooks=hooks or [],  # Memory hooks injected here
        state=state or {}   # Session state injected here
    )

def invoke(payload, context, hooks=None, state=None):
    """Entrypoint with hook injection support"""
    agent = create_orchestrator(hooks=hooks, state=state)
    response = agent({'message': payload.get('prompt')})
    return {'output': str(response)}
```

**Single-Agent Example:**
```python
def create_agent(hooks=None, state=None):
    """Create agent with optional hooks and state injection."""
    return Agent(
        system_prompt="You help customers...",
        tools=[retrieve, handoff_to_user],
        hooks=hooks or [],  # Memory hooks injected here
        state=state or {}   # Session state injected here
    )

def invoke(payload, context, hooks=None, state=None):
    """Entrypoint with hook injection support"""
    agent = create_agent(hooks=hooks, state=state)
    response = agent({'message': payload.get('prompt')})
    return {'output': str(response)}
```

## How It Works

### 1. User Sends Message

```python
POST /chat
{
  "agent_id": "agent-123",
  "user_id": "user-456",
  "actor_id": "user-456",  # Optional, defaults to user_id
  "session_id": "session-789",  # Optional, auto-generated
  "prompt": "What did I ask you last time?"
}
```

### 2. Chameleon Invocation

1. FastAPI calls `bedrock-agentcore.invoke_agent_runtime(chameleon_arn, payload)`
2. Chameleon receives: `agent_id`, `user_id`, `actor_id`, `session_id`, `prompt`
3. Chameleon fetches agent code from S3: `s3://oratio-generated-code/{user_id}/{agent_id}/agent_file.py`

### 3. Hook & State Setup

```python
# Chameleon creates memory hooks
memory_hook = MemoryHookProvider(memory_client, MEMORY_ID)
hooks = [memory_hook]

# Chameleon prepares state
state = {
    "actor_id": actor_id,  # From payload or defaults to user_id
    "session_id": session_id  # From payload or auto-generated
}
```

### 4. Agent Execution

```python
# Chameleon calls generated agent with injection
result = agent_module.invoke(payload, context, hooks=hooks, state=state)
```

### 5. Memory Hooks Fire

**On Agent Initialization (`AgentInitializedEvent`):**
```python
# Hook loads last 10 conversation turns
recent_turns = memory_client.get_last_k_turns(
    memory_id=MEMORY_ID,
    actor_id=state["actor_id"],
    session_id=state["session_id"],
    k=10
)

# Adds to system prompt:
# """
# Recent conversation:
# user: What's the weather in SF?
# assistant: The weather in San Francisco is 65°F and sunny.
# user: What did I ask you last time?
# """
```

**On Message Added (`MessageAddedEvent`):**
```python
# Hook saves each message to memory
memory_client.create_event(
    memory_id=MEMORY_ID,
    actor_id=state["actor_id"],
    session_id=state["session_id"],
    messages=[(message_text, role)]
)
```

### 6. Response

Agent processes the message with conversation context and returns response.

## Benefits

### ✅ Centralized Memory Management
- **One memory resource** for all generated agents
- Memory setup happens in Chameleon, not in generated code
- Easier to maintain and update

### ✅ Clean Generated Code
- Agents focus on business logic only
- No memory client setup or management
- Simpler, more readable code

### ✅ Flexible Session Management
- `actor_id`: Who is speaking (user, different personas, etc.)
- `session_id`: Conversation context (different topics, channels, etc.)
- Can have multiple sessions per user

### ✅ Conversation Continuity
- Last 10 turns loaded automatically
- User can return hours/days later
- Context persists across agent restarts

## Environment Variables

### Chameleon Generic Loader

| Variable | Purpose | Set By |
|----------|---------|--------|
| `MEMORY_ID` | AgentCore Memory resource ID | Infrastructure deployment |
| `CODE_BUCKET` | S3 bucket with generated code | Infrastructure deployment |
| `AWS_REGION` | AWS region for Memory Client | Infrastructure deployment |

### Infrastructure Setup

The `MEMORY_ID` is created during infrastructure deployment:

```python
# In CDK or deployment script
memory = memory_client.create_memory_and_wait(
    name="OratioAgentMemory",
    strategies=[],  # No strategies = short-term memory only
    description="Short-term memory for all Oratio agents",
    event_expiry_days=7  # Keep conversations for 7 days
)

# Store memory_id in environment variable for Chameleon
MEMORY_ID = memory['id']
```

## Memory Retention

- **Short-term memory**: Raw conversation turns
- **Retention**: 7 days (configurable via `event_expiry_days`)
- **Retrieval**: Last K turns (currently K=10)
- **No long-term strategies**: Only recent conversation context

## Session Identifiers

### actor_id
- **Purpose**: Identifies who is speaking
- **Examples**:
  - `user_123` - Regular user
  - `admin_456` - Admin user
  - `bot_789` - Another bot in multi-bot scenario
- **Default**: Falls back to `user_id` if not provided

### session_id
- **Purpose**: Identifies conversation context
- **Examples**:
  - `user_123_agent_456_channel_slack` - Slack conversation
  - `user_123_agent_456_channel_web` - Web conversation
  - `user_123_agent_456_topic_billing` - Billing topic
- **Default**: Auto-generated as `{user_id}_{agent_id}_default`

## Comparison: Old vs New

### ❌ Old Approach (Incorrect)

```python
# In generated agent code
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

def get_session_manager(payload, context):
    memory_config = {
        'memory_id': payload.get("memory_id"),
        'actor_id': "orchestrator",
        'session_id': context.get("session_id")
    }
    return AgentCoreMemorySessionManager(memory_config)

def invoke(payload, context):
    session_manager = get_session_manager(payload, context)
    agent = create_orchestrator(session_manager=session_manager)
    response = agent(...)
```

**Problems:**
- `AgentCoreMemorySessionManager` doesn't actually load conversation history
- Each generated agent needs to manage memory
- More complex generated code
- Harder to maintain

### ✅ New Approach (Correct)

```python
# In Chameleon (generic_loader.py)
memory_hook = MemoryHookProvider(memory_client, MEMORY_ID)
hooks = [memory_hook]
state = {"actor_id": actor_id, "session_id": session_id}

result = agent_module.invoke(payload, context, hooks=hooks, state=state)

# In generated agent code (simple!)
def create_orchestrator(hooks=None, state=None):
    return Agent(
        system_prompt="...",
        tools=[...],
        hooks=hooks or [],
        state=state or {}
    )

def invoke(payload, context, hooks=None, state=None):
    agent = create_orchestrator(hooks=hooks, state=state)
    response = agent(...)
```

**Benefits:**
- Hooks automatically load and save conversation history
- Centralized memory management in Chameleon
- Simpler generated code
- Based on official AWS samples

## Testing

### Test Conversation Continuity

```python
# First message
response1 = invoke_agent(
    agent_id="agent-123",
    user_id="user-456",
    session_id="session-789",
    prompt="My name is Alice and I love pizza"
)

# Second message (same session)
response2 = invoke_agent(
    agent_id="agent-123",
    user_id="user-456",
    session_id="session-789",
    prompt="What's my name?"
)
# Expected: "Your name is Alice"

# Third message (same session)
response3 = invoke_agent(
    agent_id="agent-123",
    user_id="user-456",
    session_id="session-789",
    prompt="What food do I like?"
)
# Expected: "You love pizza"
```

### Test Session Isolation

```python
# Session 1
response_a = invoke_agent(
    session_id="session-A",
    prompt="I prefer tea"
)

# Session 2 (different session)
response_b = invoke_agent(
    session_id="session-B",
    prompt="What do I prefer?"
)
# Expected: Agent doesn't know (no shared context between sessions)
```

## Summary

✅ **Memory hooks in Chameleon** (not in generated code)  
✅ **Hook injection pattern** for clean separation  
✅ **Based on AWS official samples**  
✅ **Centralized memory management**  
✅ **Simple, maintainable generated agents**  
✅ **Conversation continuity across sessions**  

**Key Insight**: Memory is infrastructure concern (Chameleon), not business logic concern (generated agents).

