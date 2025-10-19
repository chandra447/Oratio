"""
LangGraph Pipeline for AgentCreator
Orchestrates the DSPy modules in a workflow with review cycles

Pipeline Flow:
1. Parse Voice Personality → Convert unstructured text to structured format (if provided)
2. Parse SOP → Extract structured requirements
3. Draft Plan → Create agent architecture (with review cycle up to 3 iterations)
4. Generate Code → Use ReAct with code interpreter tool for validation
5. Review Code → Validate generated code
6. Generate Prompt → Create system prompt with personality

DSPy Module Selection:
- ChainOfThought: Used for reasoning tasks (parsing, planning, reviewing)
- ReAct: Used for CodeGenerator to enable tool usage (code interpreter)
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, TypedDict

import dspy
from langgraph.graph import END, StateGraph

from openinference.instrumentation.dspy import DSPyInstrumentor
from opentelemetry import baggage, context, trace as trace_api
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter


# Configure OpenTelemetry TracerProvider with proper resource attributes
resource = Resource(attributes={
    SERVICE_NAME: "agentcreator-meta-agent",
    SERVICE_VERSION: "1.0.0",
    "deployment.environment": os.getenv("ENVIRONMENT", "production"),
})

# Create TracerProvider with resource
tracer_provider = TracerProvider(resource=resource)

# Configure span exporters
# 1. Console exporter for local debugging (optional, can be removed in production)
if os.getenv("OTEL_DEBUG", "false").lower() == "true":
    console_processor = BatchSpanProcessor(ConsoleSpanExporter())
    tracer_provider.add_span_processor(console_processor)

# 2. OTLP exporter for sending traces to observability backend
# Supports AWS X-Ray, CloudWatch, or any OTLP-compatible endpoint
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
if otlp_endpoint:
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    otlp_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(otlp_processor)

# Set the global tracer provider
trace_api.set_tracer_provider(tracer_provider)

# Instrument DSPy with the configured tracer provider
DSPyInstrumentor().instrument(tracer_provider=tracer_provider)

from .modules import (
    CodeGenerator,
    CodeReviewer,
    PlanDrafter,
    PlanReviewer,
    PromptGenerator,
    SOPParser,
    VoicePersonalityParserModule,
)
from .signatures.types import (
    PlanReview,
    CodeReview,
    Requirements,
    AgentPlan,
    SystemPrompt,
    CodeGenerationOutput,
)

logger = logging.getLogger(__name__)


def set_session_context(agent_id: str, user_id: Optional[str] = None):
    """
    Set the session ID and user ID in OpenTelemetry baggage for trace correlation.
    
    This follows AWS best practices for distributed tracing, allowing all spans
    in the agent creation pipeline to be correlated by session/agent ID.
    
    Args:
        agent_id: The unique agent ID to track across all spans
        user_id: Optional user ID for additional correlation
    
    Returns:
        OpenTelemetry context token that can be used to restore previous context
    """
    ctx = baggage.set_baggage("session.id", agent_id)
    if user_id:
        ctx = baggage.set_baggage("user.id", user_id, context=ctx)
    
    token = context.attach(ctx)
    logger.info(f"Session ID '{agent_id}' attached to telemetry context")
    return token


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
    voice_personality_text: Optional[str]  # Raw unstructured text from user
    voice_personality: Optional[Dict[str, Any]]  # Structured voice personality (parsed)

    # Intermediate fields (populated during pipeline execution)
    requirements: Requirements
    plan: AgentPlan
    review_iteration: int
    plan_approved: bool 
    plan_review: PlanReview
    agent_code: str
    code_validation_status: str
    documentation_references: List[str]
    implementation_notes: str
    model_id: str
    enable_memory_hooks: bool
    code_review: CodeReview
    code_approved: bool
    code_review_feedback: str
    code_iteration: int

    # Output fields (final results)
    generated_prompt: SystemPrompt
    final_agent_code: str


# Initialize DSPy modules (PlanDrafter, CodeGenerator and CodeReviewer will be initialized with MCP tools)
sop_parser = SOPParser()
prompt_generator = PromptGenerator()
plan_reviewer = PlanReviewer()
voice_personality_parser = VoicePersonalityParserModule()

# PlanDrafter, CodeGenerator and CodeReviewer initialized separately with MCP tools
plan_drafter = None
code_generator = None
code_reviewer = None


async def parse_voice_personality_node(state: AgentCreatorState) -> AgentCreatorState:
    """Parse unstructured voice personality text into structured format"""
    
    # If voice_personality_text is provided, parse it
    if state.get("voice_personality_text"):
        logger.info("Parsing voice personality text...")
        
        structured_personality = await voice_personality_parser.aforward(
            voice_personality_text=state["voice_personality_text"],
            sop=state["sop"],
            knowledge_base_description=state["knowledge_base_description"],
        )
        
        logger.info(f"Voice personality parsed: {structured_personality}")
        return {**state, "voice_personality": structured_personality}
    else:
        logger.info("No voice personality text provided, skipping parsing")
        return state


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
    #if iteration<3 then add the plan_review
    plan_review = None
    if state.get('plan_review'):
        plan_review = state['plan_review']

    result  = await plan_drafter.acall(
        requirements=state["requirements"],
        bedrock_knowledge_base_id=state["bedrock_knowledge_base_id"],
        plan_review = plan_review
    )

    plan = getattr(result, "plan", None)

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
    review_obj: PlanReview = getattr(result, "review", None)
    
    logger.info(f"Plan review complete: approved={approved}")

    return {
        **state,
        "plan_approved": approved,
        "plan_review": review_obj,
        "review_iteration": state["review_iteration"] + 1,
    }


def should_continue_review(state: AgentCreatorState) -> str:
    """Decide whether to continue reviewing or proceed to code generation"""
    # Continue reviewing if not approved and less than 4 iterations
    if not state["plan_approved"] and state["review_iteration"] < 4:
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

    # Extract from CodeGenerationOutput object
    output_obj: CodeGenerationOutput = getattr(generation_result, "output", None)

    agent_code = output_obj.agent_code
    validation_status = output_obj.validation_status
    documentation_references = output_obj.documentation_references
    implementation_notes = output_obj.implementation_notes

    logger.info("Agent code generated")
    return {
        **state,
        "agent_code": agent_code,
        "code_validation_status": validation_status,
        "documentation_references": documentation_references,
        "implementation_notes": implementation_notes,
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
    review_obj = getattr(result, "review", None)
    
    # Extract details from CodeReview object
    critical_issues = []
    suggestions = []
    if review_obj:
        critical_issues = review_obj.critical_issues
        suggestions = review_obj.suggestions
    
    # Create feedback for next iteration
    feedback = ""
    if not approved:
        if critical_issues:
            feedback = "Critical issues found:\n" + "\n".join(f"- {issue}" for issue in critical_issues)
        if suggestions:
            feedback += f"\n\nSuggestions:\n" + "\n".join(f"- {sug}" for sug in suggestions)
        if not feedback and review_obj:
            # If no specific issues but not approved, use the import_validation
            feedback = f"Code review feedback:\n{review_obj.import_validation[:500]}"  # First 500 chars

    logger.info(f"Code review complete: approved={approved}, iteration={code_iteration}")

    return {
        **state,
        "code_review": review_obj,
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

    result = await prompt_generator.acall(
        requirements=state["requirements"],
        plan=state["plan"],
        voice_personality=voice_personality_str,
    )

    # Extract SystemPrompt object
    system_prompt_obj = getattr(result, "system_prompt", None)

    logger.info("System prompt generated")

    return {
        **state,
        "generated_prompt": system_prompt_obj,
        "final_agent_code": state["agent_code"],
    }


async def create_agent_creator_pipeline():
    """Create and configure the AgentCreator LangGraph pipeline"""
    global plan_drafter, code_generator, code_reviewer
    
    logger.info("Creating AgentCreator pipeline...")

    # Configure DSPy LLM
    # Use DeepSeek for fast, cost-effective testing
    # Can also use: "bedrock/anthropic.claude-3-sonnet-20240229-v1:0"
    lm = dspy.LM(model="bedrock/amazon.nova-pro-v1:0",cache=False)
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
    plan_drafter = PlanDrafter(strands_tools=mcp_tools)

    # Create the state graph
    workflow = StateGraph(AgentCreatorState)

    # Add nodes
    workflow.add_node("parse_voice_personality", parse_voice_personality_node)
    workflow.add_node("parse_sop", parse_sop_node)
    workflow.add_node("draft_plan", draft_plan_node)
    workflow.add_node("review_plan", review_plan_node)
    workflow.add_node("generate_code", generate_code_node)
    workflow.add_node("review_code", review_code_node)
    workflow.add_node("generate_prompt", generate_prompt_node)

    # Set entry point - start with voice personality parsing
    workflow.set_entry_point("parse_voice_personality")

    # Add edges
    workflow.add_edge("parse_voice_personality", "parse_sop")
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
