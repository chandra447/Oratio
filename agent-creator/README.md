# AgentCreator - Meta-Agent for Generating Strands Agents

Transform SOPs into production-ready AI agents automatically.

## Quick Start

```bash
# Install dependencies
uv sync

# Run test pipeline
uv run python -m scripts.test_pipeline
```

## What It Does

1. **Parses SOP** → Extracts requirements
2. **Drafts Plan** → Creates agent architecture
3. **Generates Code** → Produces Strands agent code
4. **Creates Prompt** → Generates system prompt

## Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete system architecture
- **[MCP_INTEGRATION.md](./MCP_INTEGRATION.md)** - MCP server setup

## Key Technologies

- **DSPy** - LLM-powered reasoning
- **LangGraph** - Workflow orchestration
- **MCP** - Documentation access (Strands + AWS)
- **AWS Bedrock AgentCore** - Agent deployment

## Project Structure

```
agentcreator/
├── signatures/          # DSPy signatures (one per file)
├── modules.py          # DSPy modules
├── pipeline.py         # LangGraph pipeline
├── mcp_tools.py        # MCP integration
└── tools.py            # Code validation tools
```

## Generated Agent Structure

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands_agents import Agent

app = BedrockAgentCoreApp()
agent = Agent(system_prompt="...", tools=[...])

@app.entrypoint
def invoke(payload: dict) -> dict:
    return {"result": agent(payload["prompt"])}
```

## Two-Tier Architecture

```
Voice Agent (Nova Sonic)
    ↓ invokes as tool
Generated Agent (Business Logic)
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for details.

## Development

```bash
# Run tests
uv run python -m scripts.test_pipeline

# Check imports
uv run python -c "from agentcreator.signatures import SOPParserSignature; print('✓')"
```

## Archive

Historical docs in `docs/archive/` - kept for reference but not actively maintained.
