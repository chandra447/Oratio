import dspy
from typing import List


class CodeGeneratorSignature(dspy.Signature):
    """Generate production-ready Strands agent code deployable to AWS Bedrock AgentCore.
    
    IMPORTANT: When calling tools, use plain tool names without markdown formatting (no backticks).
    Example: search_docs NOT `search_docs`
    
    GOAL: Create a complete, working Python agent that:
    - Deploys successfully to AgentCore Runtime
    - Implements the business logic from the requirements
    - Uses only verified imports from Strands and AgentCore documentation
    - Handles memory persistence if enabled
    - Integrates with Bedrock Knowledge Base for RAG
    - Includes proper error handling and logging
    
    CONSTRAINTS:
    - All imports must be verified against Strands Agents or AgentCore documentation
    - Code must follow the AgentCore deployment pattern (BedrockAgentCoreApp with @app.entrypoint)
    - Memory hooks must use the HookProvider pattern from strands.hooks
    - Knowledge Base retrieval must use boto3 bedrock-agent-runtime client
    - No hallucinated imports or non-existent APIs
    
    DOCUMENTATION SOURCES AVAILABLE:
    Use fetch_doc(url) to get complete documentation from these URLs:
    
    1. AgentCore Deployment Pattern (CRITICAL - READ FIRST):
       URL: https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/#option-a-sdk-integration
       Contains: BedrockAgentCoreApp usage, @app.entrypoint pattern, invoke(payload, context) signature,
                 app.run() pattern, complete working examples, memory hook integration
    
    2. Community Tools Package (for pre-built tools):
       URL: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/community-tools-package/
       Contains: retrieve() for Knowledge Base, calculator(), current_time(), and other ready-to-use tools
                 from strands_agents_tools package - NO need to implement manually!
    
    3. Bedrock Model Configuration:
       URL: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/amazon-bedrock/
       Contains: BedrockModel configuration, model_id format, temperature/top_p settings
    
    4. Agent Loop & Tool Execution (READ THIS - explains why NO manual tool selection):
       URL: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/agent-loop/
       Contains: How Agent AUTOMATICALLY processes messages, selects tools, and manages conversation
                 The agent loop handles tool selection - you just provide system_prompt and tools list!
    
    5. Multi-Agent Pattern (if SOP has multiple distinct responsibilities):
       URL: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/agents-as-tools/
       Contains: How to create specialized agents as tools for complex SOPs with multiple domains
                 Use @tool decorator to wrap specialized agents, orchestrator agent coordinates them
    
    Also available:
    - search_docs(query): Search all Strands documentation
    - search_agentcore_docs(query): Search AgentCore documentation
    
    COMMON PITFALLS TO AVOID:
    - ❌ from strands.bedrock import BedrockAgentCoreApp (doesn't exist)
    - ❌ from strands.agents import StrandsAgent (doesn't exist)
    - ❌ from strands.tools import memory, retrieve (doesn't exist)
    - ❌ from strands_agents_tools import memory (doesn't exist - there's no memory tool!)
    - ❌ ShortTermMemoryHookProvider (doesn't exist)
    
    MEMORY PATTERN (if enable_memory_hooks=True):
    - ✅ bedrock_agentcore.memory.MemoryClient - For creating/managing memory resources
    - ✅ AgentCoreMemorySessionManager - For Strands integration (use session_manager parameter)
    - ✅ AgentCoreMemoryConfig - Configuration with memory_id, actor_id, session_id
    - ❌ strands_agents_tools.memory - Does NOT exist!
    - ❌ Memory hooks with HookProvider - WRONG approach!
    
    CORRECT: Memory via session_manager parameter in Agent(), NOT as a tool or hook!
    
    Get memory_id, actor_id, session_id from:
    - context.session_id (if available)
    - payload.get("memory_id"), payload.get("actor_id")
    - Environment variables: os.getenv("MEMORY_ID")
    - Defaults: "default-actor", "default-session"
    
    KEY REQUIREMENTS:
    - ✅ @app.entrypoint MUST decorate a MODULE-LEVEL FUNCTION (not a class method)
    - ✅ Function signature: def invoke(payload, context) - NOT def invoke(self, event)
    - ✅ Use strands_agents_tools for pre-built tools (retrieve, calculator, etc.)
    - ✅ Agent instance created at module level, NOT as a class
    - ✅ Tools passed to Agent() constructor, NOT implemented manually
    - ✅ Memory hooks use HookProvider pattern from strands.hooks
    - ✅ Use system_prompt parameter in Agent() - NOT manual keyword checking in invoke()
    - ✅ Let the Agent decide tool usage - NO manual if/else logic for tool selection
    
    CRITICAL ANTI-PATTERNS TO AVOID:
    ❌ Manual keyword checking: if "product" in message.lower() or "order" in message.lower()
    ❌ Manual tool selection: if condition: use_tool_a() else: use_tool_b()
    ❌ Missing system_prompt: Agent should have clear instructions in system_prompt parameter
    
    The Agent's event loop automatically handles tool selection based on the system_prompt.
    Your job is to write a good system_prompt that guides the agent's behavior.
    
    SUCCESS CRITERIA:
    - Code passes Python syntax validation
    - All imports exist in documentation
    - Follows AgentCore deployment contract (@app.entrypoint, app.run())
    - Implements all requirements from the plan
    - Includes comprehensive error handling
    """
    
    # Core Inputs
    plan: str = dspy.InputField(
        desc="Approved agent architecture plan detailing tools, memory, and deployment structure"
    )
    requirements: str = dspy.InputField(
        desc="Original SOP and voice personality requirements defining agent behavior"
    )
    bedrock_knowledge_base_id: str = dspy.InputField(
        desc="Bedrock Knowledge Base ID for RAG retrieval"
    )
    
    # Configuration Inputs
    model_id: str = dspy.InputField(
        desc="Bedrock foundation model identifier (e.g., amazon.nova-pro-v1:0)"
    )
    enable_memory_hooks: bool = dspy.InputField(
        desc="Whether to implement memory persistence using HookProvider pattern"
    )
    code_review_feedback: str = dspy.InputField(
        desc="Feedback from previous code review iteration (empty on first generation)",
        default=""
    )
    

    # Outputs
    agent_code: str = dspy.OutputField(
        desc="Complete, production-ready Python code with verified imports and proper error handling"
    )
    validation_status: str = dspy.OutputField(
        desc="'valid' if all imports verified against docs, 'invalid' if hallucinated imports detected"
    )
    documentation_references: List[str] = dspy.OutputField(
        desc="URLs of documentation pages consulted to verify imports and patterns"
    )
    implementation_notes: str = dspy.OutputField(
        desc="Summary of key architectural decisions and how requirements were implemented"
    )
