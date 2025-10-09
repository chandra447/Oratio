"""
LangGraph Pipeline for AgentCreator
Orchestrates the DSPy modules in a workflow with review cycles

Pipeline Flow:
1. Parse SOP → Extract structured requirements
2. Draft Plan → Create agent architecture (with review cycle up to 3 iterations)
3. Generate Code → Use ReAct with code interpreter tool for validation
4. Review Code → Validate generated code
5. Generate Prompt → Create system prompt with personality

DSPy Module Selection:
- ChainOfThought: Used for reasoning tasks (parsing, planning, reviewing)
- ReAct: Used for CodeGenerator to enable tool usage (code interpreter)
"""

import json
import logging
from typing import Any, Dict, List, Optional, TypedDict

import dspy
from langgraph.graph import END, StateGraph

from .modules import (
    CodeGenerator,
    CodeReviewer,
    PlanDrafter,
    PlanReviewer,
    PromptGenerator,
    SOPParser,
)

logger = logging.getLogger(__name__)


class AgentCreatorState(TypedDict, total=False):
    """State for the AgentCreator pipeline
    
    All fields are optional (total=False) to allow incremental state building.
    """

    # Input fields (required at start)
    sop: str
    knowledge_base_description: str
    human_handoff_description: str
    bedrock_knowledge_base_id: str
    agent_id: str
    voice_personality: Optional[Dict[str, Any]]

    # Intermediate fields (populated during pipeline execution)
    requirements: str
    plan: str
    review_iteration: int
    plan_approved: bool
    agent_code: str
    code_validation_status: str
    documentation_references: List[str]
    implementation_notes: str
    model_id: str
    enable_memory_hooks: bool
    code_review: str
    code_approved: bool
    code_review_feedback: str
    code_iteration: int

    # Output fields (final results)
    generated_prompt: str
    final_agent_code: str


# Initialize DSPy modules (PlanDrafter, CodeGenerator and CodeReviewer will be initialized with MCP tools)
sop_parser = SOPParser()
prompt_generator = PromptGenerator()
plan_reviewer = PlanReviewer()

# PlanDrafter, CodeGenerator and CodeReviewer initialized separately with MCP tools
plan_drafter = None
code_generator = None
code_reviewer = None


async def parse_sop_node(state: AgentCreatorState) -> AgentCreatorState:
    """Parse SOP into structured requirements"""
    logger.info("Parsing SOP...")

    voice_personality_str = None
    if state.get("voice_personality"):
        voice_personality_str = json.dumps(state["voice_personality"])

    requirements = await sop_parser.acall(
        sop=state["sop"],
        knowledge_base_description=state["knowledge_base_description"],
        human_handoff_description=state["human_handoff_description"],
        voice_personality=voice_personality_str,
    )

    logger.info("SOP parsed successfully")
    return {**state, "requirements": requirements, "review_iteration": 0}


async def draft_plan_node(state: AgentCreatorState) -> AgentCreatorState:
    """Draft agent architecture plan"""
    logger.info(f"Drafting plan (iteration {state['review_iteration']})...")

    plan = await plan_drafter.acall(
        requirements=state["requirements"],
        bedrock_knowledge_base_id=state["bedrock_knowledge_base_id"],
    )

    logger.info("Plan drafted")
    return {**state, "plan": plan}


async def review_plan_node(state: AgentCreatorState) -> AgentCreatorState:
    """Review the drafted plan"""
    logger.info(f"Reviewing plan (iteration {state['review_iteration']})...")

    result = await plan_reviewer.acall(
        plan=state["plan"],
        requirements=state["requirements"],
        review_iteration=state["review_iteration"],
    )

    # Extract approved field directly (it's now a separate field, not in JSON)
    approved = getattr(result, "approved", False)  # Default to False for safety
    review_text = getattr(result, "review", "")
    
    logger.info(f"Plan review complete: approved={approved}")

    return {
        **state,
        "plan_approved": approved,
        "review_iteration": state["review_iteration"] + 1,
    }


def should_continue_review(state: AgentCreatorState) -> str:
    """Decide whether to continue reviewing or proceed to code generation"""
    # Continue reviewing if not approved and less than 3 iterations
    if not state["plan_approved"] and state["review_iteration"] < 3:
        logger.info("Plan not approved, continuing review cycle")
        return "draft_plan"
    else:
        logger.info("Plan approved or max iterations reached, proceeding to code generation")
        return "generate_code"


def should_continue_code_review(state: AgentCreatorState) -> str:
    """Decide whether to regenerate code or proceed to prompt generation"""
    code_iteration = state.get("code_iteration", 0)
    
    # Continue if not approved and less than 3 iterations
    if not state["code_approved"] and code_iteration < 3:
        logger.info(f"Code not approved, regenerating (iteration {code_iteration}/3)")
        return "generate_code"
    else:
        if state["code_approved"]:
            logger.info("Code approved, proceeding to prompt generation")
        else:
            logger.warning(f"Code not approved but max iterations reached ({code_iteration}/3), proceeding anyway")
        return "generate_prompt"


async def generate_code_node(state: AgentCreatorState) -> AgentCreatorState:
    """Generate Strands agent code"""
    code_iteration = state.get("code_iteration", 0)
    logger.info(f"Generating agent code (iteration {code_iteration})...")

    model_id = state.get("model_id", "amazon.nova-pro-v1:0")
    enable_memory_hooks = state.get("enable_memory_hooks", True)
    
    # Get feedback from previous review (if any)
    code_review_feedback = state.get("code_review_feedback", "")

    generation_result = await code_generator.acall(
        plan=state["plan"],
        requirements=state["requirements"],
        bedrock_knowledge_base_id=state["bedrock_knowledge_base_id"],
        model_id=model_id,
        enable_memory_hooks=enable_memory_hooks,
        code_review_feedback=code_review_feedback,
    )

    logger.info("Agent code generated")
    return {
        **state,
        "agent_code": generation_result.agent_code,
        "code_validation_status": getattr(generation_result, "validation_status", "unknown"),
        "documentation_references": getattr(generation_result, "documentation_references", []),
        "implementation_notes": getattr(generation_result, "implementation_notes", ""),
        "model_id": model_id,
        "enable_memory_hooks": enable_memory_hooks,
        "code_iteration": code_iteration,
    }


async def review_code_node(state: AgentCreatorState) -> AgentCreatorState:
    """Review generated code"""
    code_iteration = state.get("code_iteration", 0)
    logger.info(f"Reviewing generated code (iteration {code_iteration})...")

    result = await code_reviewer.acall(
        agent_code=state["agent_code"],
        plan=state["plan"],
        requirements=state["requirements"],
    )

    # Extract approved field directly (it's now a separate field, not in JSON)
    approved = getattr(result, "approved", True)  # Default to True if not found
    review_text = getattr(result, "review", "")
    
    # Try to parse review JSON for additional details
    critical_issues = []
    suggestions = []
    try:
        if review_text:
            review_data = json.loads(review_text)
            critical_issues = review_data.get("critical_issues", [])
            suggestions = review_data.get("suggestions", [])
    except json.JSONDecodeError:
        logger.debug("Could not parse review JSON, using approved field only")
    
    # Create feedback for next iteration
    feedback = ""
    if not approved:
        if critical_issues:
            feedback = "Critical issues found:\n" + "\n".join(f"- {issue}" for issue in critical_issues)
        if suggestions:
            feedback += f"\n\nSuggestions:\n" + "\n".join(f"- {sug}" for sug in suggestions)
        if not feedback:
            # If no specific issues but not approved, use the review text
            feedback = f"Code review feedback:\n{review_text[:500]}"  # First 500 chars

    logger.info(f"Code review complete: approved={approved}, iteration={code_iteration}")

    return {
        **state,
        "code_review": review_text,
        "code_approved": approved,
        "code_review_feedback": feedback,
        "code_iteration": code_iteration + 1,
    }


async def generate_prompt_node(state: AgentCreatorState) -> AgentCreatorState:
    """Generate system prompt"""
    logger.info("Generating system prompt...")

    voice_personality_str = None
    if state.get("voice_personality"):
        voice_personality_str = json.dumps(state["voice_personality"])

    system_prompt = await prompt_generator.acall(
        requirements=state["requirements"],
        plan=state["plan"],
        voice_personality=voice_personality_str,
    )

    logger.info("System prompt generated")

    return {
        **state,
        "generated_prompt": system_prompt,
        "final_agent_code": state["agent_code"],
    }


async def create_agent_creator_pipeline():
    """Create and configure the AgentCreator LangGraph pipeline"""
    global plan_drafter, code_generator, code_reviewer
    
    logger.info("Creating AgentCreator pipeline...")

    # Configure DSPy LLM
    # Use DeepSeek for fast, cost-effective testing
    # Can also use: "bedrock/anthropic.claude-3-sonnet-20240229-v1:0"
    lm = dspy.LM(model="openrouter/anthropic/claude-sonnet-4.5",
    max_tokens=64000)
    dspy.configure(lm=lm)
    
    # Initialize MCP tools for documentation access
    logger.info("Loading MCP tools (Strands + AgentCore Documentation)...")
    try:
        from .mcp_tools import get_all_mcp_tools
        mcp_tools = await get_all_mcp_tools()
        logger.info(f"Loaded {len(mcp_tools)} MCP tools total")
    except Exception as e:
        logger.warning(f"Failed to load MCP tools: {e}. Continuing without documentation access.")
        mcp_tools = None
    
    
    # Initialize CodeGenerator and CodeReviewer with MCP tools
    code_generator = CodeGenerator(strands_mcp_tools=mcp_tools)
    code_reviewer = CodeReviewer(strands_mcp_tools=mcp_tools)
    plan_drafter = PlanDrafter(strands_tools=mcp_tools[:2])

    # Create the state graph
    workflow = StateGraph(AgentCreatorState)

    # Add nodes
    workflow.add_node("parse_sop", parse_sop_node)
    workflow.add_node("draft_plan", draft_plan_node)
    workflow.add_node("review_plan", review_plan_node)
    workflow.add_node("generate_code", generate_code_node)
    workflow.add_node("review_code", review_code_node)
    workflow.add_node("generate_prompt", generate_prompt_node)

    # Set entry point
    workflow.set_entry_point("parse_sop")

    # Add edges
    workflow.add_edge("parse_sop", "draft_plan")
    workflow.add_edge("draft_plan", "review_plan")

    # Conditional edge for review cycle
    workflow.add_conditional_edges(
        "review_plan",
        should_continue_review,
        {
            "draft_plan": "draft_plan",
            "generate_code": "generate_code",
        },
    )

    workflow.add_edge("generate_code", "review_code")
    
    # Conditional edge for code review cycle (max 3 iterations)
    workflow.add_conditional_edges(
        "review_code",
        should_continue_code_review,
        {
            "generate_code": "generate_code",
            "generate_prompt": "generate_prompt",
        },
    )
    
    workflow.add_edge("generate_prompt", END)

    # Compile the graph
    app = workflow.compile()

    logger.info("AgentCreator pipeline created successfully")
    return app
