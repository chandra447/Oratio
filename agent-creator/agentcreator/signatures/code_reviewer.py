"""CodeReviewer Signature - Reviews generated agent code for quality"""

import dspy


class CodeReviewerSignature(dspy.Signature):
    """Review generated Strands agent code for correctness and production-readiness.
    
    IMPORTANT: When calling tools, use plain tool names without markdown formatting (no backticks).
    Example: search_docs NOT `search_docs`
    
    GOAL: Verify that the generated code:
    - Uses only valid imports from Strands and AgentCore documentation
    - Follows the correct AgentCore deployment pattern
    - Implements all requirements from the plan
    - Has no syntax errors or hallucinated APIs
    - Includes proper error handling and logging
    
    VALIDATION APPROACH:
    - Verify each import against Strands or AgentCore documentation
    - Check that BedrockAgentCoreApp pattern is correctly implemented
    - Validate memory hooks follow HookProvider pattern (if used)
    - Ensure Knowledge Base retrieval uses boto3 correctly
    - Check for common hallucination patterns
    
    DOCUMENTATION SOURCES AVAILABLE:
    Use fetch_doc(url) to verify patterns against these URLs:
    
    1. Agent Loop (explains why NO manual tool selection):
       URL: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/agent-loop/
       Verify: Agent automatically handles tool selection via event loop
    
    2. AgentCore Deployment:
       URL: https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/#option-a-sdk-integration
       Verify: Correct @app.entrypoint pattern and invoke() signature
    
    3. Community Tools:
       URL: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/community-tools-package/
       Verify: Using strands_agents_tools imports, not manual implementations
    
    4. Multi-Agent Pattern:
       URL: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/agents-as-tools/
       Verify: If multiple responsibilities, check if @tool pattern should be used
    
    Also available:
    - search_docs(query): Search all Strands documentation
    - search_agentcore_docs(query): Search AgentCore documentation
    
    CRITICAL CHECKS:
    1. Import Validation:
       - ❌ from strands.bedrock import BedrockAgentCoreApp (doesn't exist)
       - ✅ from bedrock_agentcore.runtime import BedrockAgentCoreApp
       - ❌ from strands.agents import StrandsAgent (doesn't exist)
       - ✅ from strands import Agent
       - ❌ from strands.tools import memory, retrieve (doesn't exist)
       - ✅ from strands_agents_tools import retrieve, calculator, etc.
    
    2. AgentCore Pattern:
       - Must have: app = BedrockAgentCoreApp()
       - Must have: @app.entrypoint decorator on MODULE-LEVEL function
       - Must have: def invoke(payload, context): signature (NOT def invoke(self, event))
       - Must have: app.run() in if __name__ == "__main__"
    
    3. Agent Configuration (CRITICAL):
       - Must have: system_prompt parameter in Agent() constructor
       - Must NOT have: Manual keyword checking (if "product" in message.lower())
       - Must NOT have: Manual tool selection logic (if condition: use_tool_a())
       - The Agent's event loop handles tool selection automatically!
    
    4. Memory Hooks (if enabled):
       - Must use: HookProvider, HookRegistry, MessageAddedEvent, AgentInitializedEvent
       - Must NOT use: ShortTermMemoryHookProvider (doesn't exist)
    
    5. Multi-Agent Pattern (if SOP has multiple distinct responsibilities):
       - Consider: Using @tool decorator to wrap specialized agents
       - Consider: Orchestrator agent that coordinates specialized agents
    
    CORRECT CODE PATTERN EXAMPLE:
    ```python
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
    from strands import Agent
    from strands_agents_tools import retrieve, handoff_to_user
    
    app = BedrockAgentCoreApp()
    
    # Agent with system_prompt - tools are passed as list
    agent = Agent(
        model="amazon.nova-pro-v1:0",
        system_prompt="You are a customer service agent. Use retrieve tool for product/order questions. Use handoff_to_user for complaints or refunds over $100.",
        tools=[
            retrieve(knowledge_base_id="kb-test-123"),
            handoff_to_user()
        ]
    )
    
    @app.entrypoint
    def invoke(payload, context):
        user_message = payload.get("prompt", "Hello")
        response = agent(user_message)  # Agent automatically selects tools!
        return response.message['content'][0]['text']
    
    if __name__ == "__main__":
        app.run()
    ```
    
    WRONG PATTERNS TO FLAG:
    - agent = retrieve(...) then agent.configure(...) - retrieve() returns a tool, not an agent!
    - if "complaints" in error_message: handoff_to_user() - manual checking in error handler
    - from strands.bedrock import BedrockAgentCoreApp - wrong import (should be bedrock_agentcore.runtime)
    - from strands_agents_tools import memory - CRITICAL: memory tool doesn't exist!
    - agent.configure(...) - Agent doesn't have a configure() method
    
    MEMORY CLARIFICATION (CRITICAL):
    - ✅ bedrock_agentcore.memory.MemoryClient - For creating/managing memory resources
    - ✅ bedrock_agentcore.memory.integrations.strands.session_manager.AgentCoreMemorySessionManager - For Strands integration
    - ✅ bedrock_agentcore.memory.integrations.strands.config.AgentCoreMemoryConfig - Configuration
    - ❌ strands_agents_tools.memory - Does NOT exist! This is a hallucination!
    - ❌ Memory hooks with HookProvider - WRONG approach!
    
    CORRECT MEMORY PATTERN:
    Memory is handled via session_manager parameter in Agent(), NOT as a tool or hook!
    
    ```python
    from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
    from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
    
    # Get from payload/context
    memory_id = context.get("memory_id") or os.getenv("MEMORY_ID")
    actor_id = context.get("actor_id", "default-actor")
    session_id = context.session_id if hasattr(context, 'session_id') else "default-session"
    
    # Configure memory
    memory_config = AgentCoreMemoryConfig(
        memory_id=memory_id,
        session_id=session_id,
        actor_id=actor_id
    )
    
    # Create session manager
    session_manager = AgentCoreMemorySessionManager(
        agentcore_memory_config=memory_config,
        region_name="us-east-1"
    )
    
    # Agent with session_manager (NOT hooks!)
    agent = Agent(
        model="amazon.nova-pro-v1:0",
        system_prompt="...",
        tools=[retrieve(...), handoff_to_user()],
        session_manager=session_manager  # Memory via session_manager!
    )
    ```
    
    APPROVAL CRITERIA:
    - approved: true if no critical issues (hallucinated imports, wrong patterns)
    - approved: false if any critical issues found
    - code_quality_score: 1-10 (10 = perfect, production-ready)
    
    PROVIDE SPECIFIC, ACTIONABLE FIXES:
    Instead of: "Remove manual keyword checking"
    Say: "Replace lines 45-50 with: agent = Agent(model='...', system_prompt='...', tools=[retrieve(...), handoff_to_user()])"
    
    Instead of: "Use system_prompt"
    Say: "Add system_prompt parameter to Agent() constructor on line 30. The system prompt should describe when to use each tool."
    
    OUTPUT FORMAT:
    JSON object with:
    - approved: boolean
    - code_quality_score: number (1-10)
    - critical_issues: list of strings with SPECIFIC line numbers and exact fixes
    - correct_code_example: string showing the correct pattern for the main issue
    - import_validation: string (summary of import checks)
    """

    agent_code: str = dspy.InputField(desc="Generated Python code to review")
    plan: str = dspy.InputField(desc="Original architecture plan")
    requirements: str = dspy.InputField(desc="Original requirements from SOP")


    # Output fields
    approved: bool = dspy.OutputField(
        desc="Boolean indicating if code is approved (true) or needs revision (false). True if no critical issues found."
    )
    
    review: str = dspy.OutputField(
        desc="JSON review with code_quality_score (1-10), critical_issues (list), suggestions (list), import_validation (string). Do NOT include 'approved' in this JSON - it's a separate field."
    )
