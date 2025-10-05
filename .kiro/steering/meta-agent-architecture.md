# Meta-Agent Architecture

## Overview

The AgentCreator meta-agent is the core innovation of Oratio. It automatically transforms user-provided SOPs into production-ready Strands agents deployed on AWS AgentCore.

## Technology Stack

### DSPy Framework
**Documentation**: https://dspy.ai/docs

DSPy is used for building the LLM-powered components of the meta-agent:

- **Signatures**: Define input/output behavior for each pipeline stage
- **Modules**: ChainOfThought, ReAct for reasoning tasks
- **Compilation**: Automatic prompt optimization
- **LLM Backend**: AWS Bedrock Claude models

**Key DSPy Components**:
```python
import dspy

# Configure DSPy with Bedrock
lm = dspy.lm(model='bedrock/anthropic.claude-3-sonnet-20240229-v1:0')
dspy.settings.configure(lm=lm)

# Define signature for SOP parsing
class SOPParser(dspy.Signature):
    """Parse SOP and extract structured requirements"""
    sop_text = dspy.InputField(desc="Standard Operating Procedure text")
    requirements = dspy.OutputField(desc="Structured requirements in JSON format")

# Create module
parser = dspy.ChainOfThought(SOPParser)
```

### LangGraph Framework
**Documentation**: https://langgraph.com/

LangGraph orchestrates the multi-stage pipeline with state management:

- **StateGraph**: Defines workflow nodes and edges
- **Cyclic Workflows**: Enables iterative refinement (plan review)
- **Conditional Edges**: Quality gates and decision points
- **State Management**: Persistent state across pipeline stages

**Key LangGraph Components**:
```python
from langgraph.graph import StateGraph, END

# Define state
class AgentCreationState(TypedDict):
    sop: str
    requirements: dict
    plan: str
    code: str
    review_count: int

# Create graph
workflow = StateGraph(AgentCreationState)

# Add nodes
workflow.add_node("parse_sop", parse_sop_node)
workflow.add_node("draft_plan", draft_plan_node)
workflow.add_node("review_plan", review_plan_node)
workflow.add_node("generate_code", generate_code_node)

# Add edges with conditions
workflow.add_conditional_edges(
    "review_plan",
    should_continue_review,
    {
        "continue": "draft_plan",
        "approve": "generate_code"
    }
)
```

### Strands Agent Framework
**Documentation**: https://strandsagents.com/latest/documentation/docs/

Generated agents follow the Strands framework specification:

- **Agent Structure**: Standardized architecture with tools, memory, reasoning
- **Tool Integration**: Function calling for external actions
- **Memory Management**: Persistent conversation state
- **Reasoning Patterns**: Multi-step planning and decision-making

**Generated Strands Agent Structure**:
```python
from strands import Agent, Tool, Memory

class CustomerServiceAgent(Agent):
    def __init__(self):
        super().__init__(
            name="customer_service_agent",
            description="Handles customer inquiries based on SOP",
            tools=[
                Tool(name="search_kb", func=self.search_knowledge_base),
                Tool(name="escalate", func=self.escalate_to_human)
            ],
            memory=Memory(type="conversation")
        )
    
    def search_knowledge_base(self, query: str) -> str:
        """Search Bedrock Knowledge Base"""
        # Implementation
        pass
    
    def escalate_to_human(self, reason: str) -> dict:
        """Trigger human handoff"""
        # Implementation
        pass
    
    async def process(self, input: str) -> str:
        """Main agent processing logic"""
        # Multi-step reasoning
        # Tool usage
        # Response generation
        pass
```

## Pipeline Architecture

### Stage 1: SOP Parsing (DSPy)
```python
class SOPParser(dspy.Signature):
    """Extract structured requirements from SOP"""
    sop_text = dspy.InputField()
    requirements = dspy.OutputField(desc="JSON with business rules, constraints, tools needed")

sop_parser = dspy.ChainOfThought(SOPParser)
```

### Stage 2: Plan Drafting (DSPy + LangGraph)
```python
class PlanDrafter(dspy.Signature):
    """Create agent architecture plan"""
    requirements = dspy.InputField()
    plan = dspy.OutputField(desc="Detailed agent architecture and implementation plan")

plan_drafter = dspy.ChainOfThought(PlanDrafter)
```

### Stage 3: Plan Review (DSPy + LangGraph Cycle)
```python
class PlanReviewer(dspy.Signature):
    """Review and improve agent plan"""
    plan = dspy.InputField()
    requirements = dspy.InputField()
    review = dspy.OutputField(desc="Feedback and approval status")

plan_reviewer = dspy.ChainOfThought(PlanReviewer)

# LangGraph handles cycling until approval
def should_continue_review(state):
    if state["review_count"] >= 3 or state["approved"]:
        return "approve"
    return "continue"
```

### Stage 4: Code Generation (DSPy)
```python
class StrandsCodeGenerator(dspy.Signature):
    """Generate Strands agent code"""
    plan = dspy.InputField()
    requirements = dspy.InputField()
    code = dspy.OutputField(desc="Complete Python code for Strands agent")

code_generator = dspy.ChainOfThought(StrandsCodeGenerator)
```

### Stage 5: Code Review (DSPy)
```python
class CodeReviewer(dspy.Signature):
    """Review generated code for quality and correctness"""
    code = dspy.InputField()
    requirements = dspy.InputField()
    review = dspy.OutputField(desc="Code quality assessment and fixes")

code_reviewer = dspy.ChainOfThought(CodeReviewer)
```

## Integration with AWS AgentCore

Generated Strands agents are deployed to AWS AgentCore:

1. **Code Storage**: Agent code stored in S3 (oratio-generated-code bucket)
2. **Deployment**: Lambda function deploys code to AgentCore
3. **Runtime**: AgentCore provides execution environment
4. **Invocation**: Voice/text services invoke agents via bedrock-agent-runtime

## Key Benefits

1. **DSPy Optimization**: Automatic prompt tuning improves generation quality
2. **LangGraph Control**: Explicit workflow with error handling and retries
3. **Strands Consistency**: Standardized agent structure across all generated agents
4. **AgentCore Integration**: Enterprise features (auth, memory, observability) built-in

## Development Guidelines

- Use DSPy Signatures to define clear input/output contracts
- Leverage DSPy compilation for prompt optimization
- Design LangGraph workflows with explicit state transitions
- Follow Strands framework patterns in generated code
- Test each pipeline stage independently
- Validate generated agents against Strands specification
- Ensure AgentCore compatibility in deployment code
