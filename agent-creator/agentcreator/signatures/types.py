from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

class PlanReview(BaseModel):
    """Structured feedback on plan review."""
    strengths: List[str] = Field(..., description="Aspects of the plan that are well-designed or exceed requirements.")
    weaknesses: List[str] = Field(..., description="Areas where the plan needs improvement or lacks clarity.")
    suggestions: List[str] = Field(..., description="Concrete, actionable steps to strengthen the plan.")
    missing_elements: List[str] = Field(..., description="Essential components absent from the plan—required for deployment.")

class CodeReview(BaseModel):
    """Structured feedback on agent code review."""
    code_quality_score: int = Field(..., description="Code quality on a 1 (poor) to 10 (excellent/production) scale.")
    critical_issues: List[str] = Field(..., description="Critical code problems needing immediate fix—each with line reference and correction.")
    suggestions: List[str] = Field(..., description="Non-critical or structural improvements and refinements.")
    import_validation: str = Field(..., description="Summary of which imports are correct/incorrect and why.")
    correct_code_example: Optional[str] = Field(None, description="Optional: Snippet demonstrating the best/correct approach to main issue.")
    multi_agent_compliance: Optional[str] = Field(None, description="(Multi-agent only) Compliance summary for agent orchestration, handoff, agent role config.")

class Requirements(BaseModel):
    """Parsed requirements from SOP and personality/config."""
    core_goal: str = Field(..., description="Primary business objective.")
    requires_escalation: bool = Field(..., description="True if the agent must escalate to human/handoff.")
    integration_needed: List[str] = Field(..., description="List of external system/integration needs (by keyword).")
    knowledge_domains: List[str] = Field(..., description="What specialized knowledge or RAG is needed?")
    tone: str = Field(..., description="Target voice/tone for agent (e.g. formal, warm, concise).")
    personality_traits: Dict[str, Any] = Field(..., description="Specific behaviors, qualities, patterns from input (e.g. 'helpful', 'patient').")
    behavioral_guidelines: Optional[str] = Field(None, description="Additional communication or behavioral instructions.")

class AgentPlan(BaseModel):
    """Agent architecture output plan with all aspects for codegen."""
    architecture_type: Literal['single_agent','multi_agent'] = Field(..., description="Agent design: 'single_agent' or 'multi_agent'.")
    agent_roles: List[str] = Field(..., description="Explicit roles for agent/subagent(s).")
    required_tools: List[str] = Field(..., description="Community tools included (e.g. ['retrieve', 'handoff_to_user']).")
    tool_configurations: Dict[str, Any] = Field(..., description="Configuration or environment for each tool (e.g. {'retrieve': {'env_var': 'KNOWLEDGE_BASE_ID'}}).")
    memory_strategy: Optional[Dict[str, Any]] = Field(None, description="Memory configuration dict with keys: 'type', 'description', 'implementation'. For Chameleon: {'type': 'chameleon_injected', 'description': '...', 'implementation': '...'}")
    interaction_patterns: str = Field(..., description="Natural language/logic description of message flow, handoff, tool activation.")
    system_prompt_outline: str = Field(..., description="Outline of main system prompt structure for the agent.")
    error_handling: Dict[str, Any] = Field(..., description="Fallback, escalation, and recovery logic.")
    constraints: Optional[str] = Field(None, description="Any special business/tech/procedural limitations.")

class SystemPrompt(BaseModel):
    """Detailed system prompt data for agent codegen and voice interface."""
    identity_role: str = Field(..., description="Role/identity summary ('customer service rep', etc.).")
    personality_communication: Optional[str] = Field(None, description="Behavioral/communicative guidelines.")
    core_responsibilities: str = Field(..., description="Bulleted outline of specific agent tasks.")
    behavioral_guidelines: str = Field(..., description="Formal, concise description of ideal agent behaviors.")
    specific_instructions: str = Field(..., description="Edge-case or task-specific rules, if any.")
    tool_usage: str = Field(..., description="Instructions on when/how to invoke tools.")
    full_prompt: str = Field(..., description="Full string to use as system_prompt for the generated Strands agent.")
    voice_prompt: Optional[str] = Field(None, description="Voice-optimized system prompt for Nova Sonic (brief, conversational, with tool usage instructions).")

class CodeGenerationOutput(BaseModel):
    """Output for code generation block."""
    agent_code: str = Field(..., description="Generated Python agent code as a string.")
    validation_status: str = Field(..., description="'valid' or 'invalid'—result of code syntax/behavior checks.")
    documentation_references: List[str] = Field(..., description="Doc sources/URLs referenced during codegen.")
    implementation_notes: str = Field(..., description="Any implementation-specific caveats, workarounds, or next steps.")
