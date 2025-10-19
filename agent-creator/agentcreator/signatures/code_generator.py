import dspy
from typing import List
from .types import CodeGenerationOutput, AgentPlan, Requirements

class CodeGeneratorSignature(dspy.Signature):
    """Generate production-ready Python code for a Strands agent system (single or multi-agent) that will be dynamically loaded by Chameleon.

CHAMELEON ARCHITECTURE:
Chameleon is a generic AgentCore Runtime loader that dynamically loads agent code from S3 at invocation time.
It handles all AgentCore integration (runtime, memory hooks, session management) so generated agents are pure Strands code.

⚠️ CRITICAL: MEMORY IS HANDLED BY CHAMELEON (NOT BY GENERATED CODE) ⚠️

MEMORY ARCHITECTURE:
- **Chameleon** (generic loader) handles ALL memory operations via MemoryHookProvider
- Generated agent code receives `hooks` and `state` as parameters (injected by Chameleon)
- DO NOT create AgentCoreMemorySessionManager, MemoryClient, or any memory code in generated agents
- DO NOT import bedrock_agentcore.memory modules
- Memory hooks are injected at runtime by Chameleon

⚠️ CRITICAL: YOU MUST USE DOCUMENTATION TOOLS BEFORE WRITING ANY CODE ⚠️

MANDATORY WORKFLOW (DO NOT SKIP ANY STEP):

STEP 1 - FETCH DOCUMENTATION (REQUIRED):
You MUST use the available MCP documentation tools BEFORE writing any code:
- Use 'search_docs' tool to find relevant Strands documentation
- Use 'fetch_doc' tool to get full documentation content
- Use 'search_agentcore_docs' to find AgentCore documentation
- Use 'fetch_agentcore_doc' to get AgentCore documentation

Key documentation to retrieve:
1. Community tools imports: search for "community-tools-package"
2. Multi-agent patterns: search for "agents-as-tools" if plan.architecture_type == 'multi_agent'
3. AgentCore deployment: search for "deploy_to_bedrock_agentcore"

STEP 2 - VERIFY IMPORTS:
After fetching docs, verify the EXACT import statements:
- Tools: from strands_tools import retrieve, handoff_to_user (NOT from strands.tools or strands_agents.tools)
- Agent: from strands import Agent, tool (NOT from strands_agents)
- NO bedrock_agentcore imports needed (Chameleon handles all AgentCore integration)
- NO Agent.handle() method exists - use @tool decorator and agent() callable
- NO memory imports - Chameleon injects hooks

STEP 3 - WRITE CODE WITH CORRECT PATTERNS:

For MULTI-AGENT (plan.architecture_type == 'multi_agent'):
```python
import os
import logging
from strands import Agent, tool
from strands_tools import retrieve, handoff_to_user

# Environment variables
os.environ["KNOWLEDGE_BASE_ID"] = "kb-test-123"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define specialist agents as @tool decorated functions
@tool
def product_inquiry_agent(query: str) -> str:
    \"\"\"Handle product inquiries.\"\"\"
    agent = Agent(
        model="bedrock/amazon.nova-pro-v1:0",  # Use Nova Pro
        system_prompt="You are a product expert. Use retrieve tool to answer questions.",
        tools=[retrieve]
    )
    return agent(query)  # Agent is callable, use agent(query) not agent.invoke(query)

@tool
def order_tracking_agent(query: str) -> str:
    \"\"\"Handle order tracking.\"\"\"
    agent = Agent(
        model="bedrock/amazon.nova-pro-v1:0",  # Use Nova Pro
        system_prompt="You track orders. Use retrieve tool for order info.",
        tools=[retrieve]
    )
    return agent(query)

@tool
def returns_processing_agent(query: str) -> str:
    \"\"\"Handle returns processing.\"\"\"
    agent = Agent(
        model="bedrock/amazon.nova-pro-v1:0",  # Use Nova Pro
        system_prompt="You process returns. Use retrieve tool for returns info.",
        tools=[retrieve]
    )
    return agent(query)

def create_orchestrator(hooks=None, state=None):
    \"\"\"Create orchestrator agent with optional hooks and state injection.
    
    Args:
        hooks: List of HookProvider instances (injected by Chameleon for memory)
        state: Dict with actor_id and session_id (injected by Chameleon)
    \"\"\"
    return Agent(
        model="bedrock/amazon.nova-pro-v1:0",  # Use Nova Pro instead of default Claude
        system_prompt="Route queries to specialists. Use product_inquiry_agent for products, order_tracking_agent for orders, returns_processing_agent for returns.",
        tools=[product_inquiry_agent, order_tracking_agent, returns_processing_agent, handoff_to_user],
        hooks=hooks or [],
        state=state or {}
    )

def invoke(payload, context, hooks=None, state=None):
    \"\"\"Entrypoint - orchestrator handles routing.
    
    Args:
        payload: Request payload with user message
        context: Request context from AgentCore  
        hooks: Optional hooks injected by Chameleon (for memory)
        state: Optional state injected by Chameleon (actor_id, session_id)
    \"\"\"
    try:
        logger.info(f"Received payload: {payload}")
        
        # Create agent with injected hooks and state
        agent = create_orchestrator(hooks=hooks, state=state)
        
        # Extract user message from payload
        user_message = payload.get('prompt', payload.get('input', ''))
        
        # Invoke agent with string prompt (Strands expects str, not dict)
        response = agent(user_message)
        return {'output': str(response)}
    except Exception as e:
        logger.error(f'Error occurred: {e}')
        return {'error': str(e)}
```

For SINGLE-AGENT (plan.architecture_type == 'single_agent'):
```python
import os
import logging
from strands import Agent
from strands_tools import retrieve, handoff_to_user

os.environ["KNOWLEDGE_BASE_ID"] = "kb-test-123"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_agent(hooks=None, state=None):
    \"\"\"Create agent with optional hooks and state injection.
    
    Args:
        hooks: List of HookProvider instances (injected by Chameleon for memory)
        state: Dict with actor_id and session_id (injected by Chameleon)
    \"\"\"
    return Agent(
        model="bedrock/amazon.nova-pro-v1:0",  # Use Nova Pro instead of default Claude
        system_prompt="You help customers with inquiries using retrieve and handoff_to_user tools.",
        tools=[retrieve, handoff_to_user],
        hooks=hooks or [],
        state=state or {}
    )

def invoke(payload, context, hooks=None, state=None):
    \"\"\"Entrypoint for single agent.
    
    Args:
        payload: Request payload with user message
        context: Request context from AgentCore
        hooks: Optional hooks injected by Chameleon (for memory)
        state: Optional state injected by Chameleon (actor_id, session_id)
    \"\"\"
    try:
        logger.info(f"Received payload: {payload}")
        
        # Create agent with injected hooks and state
        agent = create_agent(hooks=hooks, state=state)
        
        # Extract user message from payload
        user_message = payload.get('prompt', payload.get('input', ''))
        
        # Invoke agent with string prompt (Strands expects str, not dict)
        response = agent(user_message)
        return {'output': str(response)}
    except Exception as e:
        logger.error(f'Error occurred: {e}')
        return {'error': str(e)}
```

STEP 4 - VALIDATE CODE:
Use validate_python_syntax tool to check syntax before finishing.

CRITICAL RULES (BASED ON VERIFIED DOCUMENTATION):
❌ NEVER use Agent.handle() or Agent.invoke() - they don't exist
❌ NEVER do manual routing in invoke() with if/else - let orchestrator handle it
❌ NEVER import from bedrock_agentcore - Chameleon handles all AgentCore integration
❌ NEVER create AgentCoreMemorySessionManager or MemoryClient - Chameleon provides memory via hooks
❌ NEVER import bedrock_agentcore.memory modules - memory is injected by Chameleon
❌ NEVER skip documentation lookup - it's mandatory
✅ ALWAYS use @tool decorator for specialist agents in multi-agent
✅ ALWAYS call agent directly: agent(query) or agent({'message': query}) - Agent is callable
✅ ALWAYS import: from strands import Agent, tool
✅ ALWAYS import tools: from strands_tools import retrieve, handoff_to_user
✅ ALWAYS accept hooks and state parameters in create_agent/create_orchestrator functions
✅ ALWAYS accept hooks and state parameters in invoke() function
✅ ALWAYS pass hooks and state to Agent() constructor: Agent(..., hooks=hooks or [], state=state or {})
✅ ALWAYS verify imports against fetched documentation
✅ ALWAYS include logging and error handling
✅ ALWAYS handle both 'prompt' and 'input' keys in payload
✅ GENERATED CODE SHOULD BE A PURE PYTHON MODULE (no BedrockAgentCoreApp, no app.run())

"""
    plan: AgentPlan = dspy.InputField(
        desc="Approved agent architecture plan detailing tools, roles, memory, and structure."
    )
    requirements: Requirements = dspy.InputField(
        desc="Original requirements and voice/personality configuration."
    )
    bedrock_knowledge_base_id: str = dspy.InputField(
        desc="Knowledge Base ID for 'retrieve' tool setup."
    )
    model_id: str = dspy.InputField(
        desc="Bedrock model identifier (e.g., 'amazon.nova-pro-v1:0')."
    )
    enable_memory_hooks: bool = dspy.InputField(
        desc="True to use hooks provided by Chameleon for memory integration."
    )
    code_review_feedback: str = dspy.InputField(
        desc="Code review feedback, if any, for revision context.", default=""
    )

    output: CodeGenerationOutput = dspy.OutputField(
        desc="Agent code, validation status, doc references, and implementation notes."
    )
