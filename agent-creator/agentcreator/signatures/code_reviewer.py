import dspy
from .types import Requirements,CodeReview, AgentPlan
class CodeReviewerSignature(dspy.Signature):
    """
    Rigorous review of generated Strands agent code for:
    - canonical import/usage,
    - deployment and entrypoint correctness,
    - hooks and state injection pattern (Chameleon architecture),
    - tool orchestration
    - and full compliance with both the Strands SDK (agents-as-tools pattern) and the Chameleon generic loader architecture.

⚠️ CRITICAL: MEMORY IS HANDLED BY CHAMELEON (NOT BY GENERATED CODE) ⚠️

MEMORY ARCHITECTURE TO VALIDATE:
- Generated code should NEVER import bedrock_agentcore.memory modules
- Generated code should NEVER create AgentCoreMemorySessionManager or MemoryClient
- Generated code MUST accept hooks and state parameters in:
  * create_agent() or create_orchestrator() function
  * invoke() function
- Generated code MUST pass hooks and state to Agent constructor: Agent(..., hooks=hooks or [], state=state or {})
- Memory is injected by Chameleon at runtime via HookProvider

⚠️ CRITICAL: USE MCP DOCUMENTATION TOOLS TO VERIFY IMPORTS AND PATTERNS ⚠️

Before reviewing, you SHOULD use MCP tools to verify patterns:
- Use 'search_docs' and 'fetch_doc' to verify Strands patterns
- Use 'search_agentcore_docs' and 'fetch_agentcore_doc' to verify AgentCore imports

**MANDATORY VALIDATION CRITERIA (Actionable Review):**

1. **Import Validation (CRITICAL - MOST COMMON ERRORS):**
   ❌ WRONG: ANY imports from bedrock_agentcore (memory is handled by Chameleon)
   ✅ CORRECT:
   ```python
   import os
   import logging
   from strands import Agent, tool
   from strands_tools import retrieve, handoff_to_user
   ```
   
   ❌ WRONG: `from strands.tools import tool` or `from strands_agents import Agent`
   ✅ CORRECT: `from strands import Agent, tool` and `from strands_tools import retrieve, handoff_to_user`
   
   ❌ WRONG: `from bedrock_agentcore.runtime import BedrockAgentCoreApp` (Chameleon handles this)
   ❌ WRONG: `from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager`
   
   - Flag ANY bedrock_agentcore import - generated code should be pure Strands
   - Use documentation tools to verify if unsure

2. **Entrypoint Pattern (CRITICAL):**
   ✅ CORRECT: Module-level `def invoke(payload, context, hooks=None, state=None)` function
   ❌ WRONG: ANY BedrockAgentCoreApp usage (Chameleon handles the app runtime)
   ❌ WRONG: `if __name__ == "__main__": app.run()` at end
   ✅ CORRECT: Generated code should be a pure Python module that Chameleon can import

3. **Hooks and State Injection Pattern (CRITICAL):**
   ✅ CORRECT: create_agent() or create_orchestrator() accepts hooks and state:
   ```python
   def create_orchestrator(hooks=None, state=None):
       return Agent(
           system_prompt="...",
           tools=[...],
           hooks=hooks or [],
           state=state or {}
       )
   ```
   
   ✅ CORRECT: invoke() function accepts hooks and state and passes them through:
   ```python
   def invoke(payload, context, hooks=None, state=None):
       agent = create_orchestrator(hooks=hooks, state=state)
       ...
   ```
   
   ❌ WRONG: Creating ANY memory-related objects (AgentCoreMemorySessionManager, MemoryClient, etc.)
   ❌ WRONG: get_session_manager() function
   ❌ WRONG: Passing session_manager to Agent (use hooks instead)

4. **Agent Invocation (CRITICAL):**
   ❌ WRONG: `agent.invoke(query)` or `agent.handle(query)` - these methods don't exist
   ✅ CORRECT: `agent(query)` or `agent({'message': query})` - Agent is callable

5. **Tool Usage (Per Plan):**
   - Only use documented community tools (`retrieve`, `handoff_to_user`, etc.)
   - If `retrieve`: ensure `os.environ["KNOWLEDGE_BASE_ID"]` is set
   - No manual tool selection (`if/else` in invoke() for routing)

6. **Multi-Agent Orchestration (If Multi-Agent):**
   ✅ CORRECT: Each specialist as @tool decorated function
   ✅ CORRECT: Orchestrator has specialist tools in its tools list
   ❌ WRONG: Manual routing with if/else in invoke()

7. **Error Handling:**
   ✅ CORRECT: Try/except in invoke(), logging, return serializable dict
   ✅ CORRECT: Handle both 'prompt' and 'input' keys in payload

**MOST CRITICAL ERRORS TO CATCH:**
1. ANY bedrock_agentcore imports (memory is handled by Chameleon, not generated code)
2. AgentCoreMemorySessionManager or MemoryClient usage
3. BedrockAgentCoreApp usage (Chameleon is the runtime)
4. Missing hooks/state parameters in create_agent/create_orchestrator
5. Missing hooks/state parameters in invoke()
6. Not passing hooks/state to Agent constructor
7. Using agent.invoke() or agent.handle() (should be agent())
8. Manual routing in invoke() function

**VALIDATION OUTPUT:**
- approved: bool (True ONLY if ALL critical import/pattern checks pass)
- code_quality_score: 1-10 (Must be <5 if ANY critical import error; <8 if other blocking issues)
- critical_issues: Line-numbered list with exact fix code
- suggestions: Non-blocking improvements
- import_validation: Exact verification of every import line
- multi_agent_compliance: Verify @tool usage and no manual routing
- hooks_state_compliance: Verify hooks/state pattern throughout
- correct_code_example: Complete corrected code for biggest issue

**REVIEW STRUCTURE:**
- Each issue and suggestion must be paired with the corrected code fragment and a one-sentence rationale.

**ALWAYS ENSURE ALL POINTS IN THIS CHECKLIST ARE ENFORCED ON EVERY REVIEW.**

Example Critical Issues:
- "Line 5: REMOVE `from bedrock_agentcore.runtime import BedrockAgentCoreApp` - Chameleon handles runtime, generated code should be pure Strands"
- "Line 10: REMOVE `from bedrock_agentcore.memory...` imports - Memory is injected by Chameleon via hooks"
- "Line 25: ADD hooks and state parameters to create_orchestrator(hooks=None, state=None)"
- "Line 45: REMOVE get_session_manager() function - Chameleon injects memory via hooks"
- "Line 60: Pass hooks and state to Agent: Agent(..., hooks=hooks or [], state=state or {})"
"""
    agent_code: str = dspy.InputField(desc="Generated Python code to review")
    plan: AgentPlan = dspy.InputField(desc="Architecture plan (from PlanDrafter)")
    requirements: Requirements = dspy.InputField(desc="Requirements from SOP/voice instructions")

    approved: bool = dspy.OutputField(desc="True if code passes all blocking criteria; False if any critical issue found.")
    review: CodeReview = dspy.OutputField(
        desc="Structured review—code_quality_score (1-10); critical_issues (line numbers + fixes + rationale); suggestions; import_validation; documentation_verification; multi_agent_compliance; hooks_state_compliance; correct_code_example."
    )
