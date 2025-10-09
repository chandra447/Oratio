"""
MCP Tools Integration for AgentCreator

Provides documentation access via MCP servers:
1. Strands MCP Server - Strands agent framework documentation
2. AWS Documentation MCP Server - AWS Bedrock AgentCore documentation

Based on: https://dspy.ai/tutorials/mcp/

Note: MCP sessions must be kept alive for tools to work.
"""

import asyncio
import logging
from typing import List, Optional, Tuple, Dict
from contextlib import AsyncExitStack

import dspy
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

# Global MCP sessions and exit stacks (kept alive for tool usage)
_mcp_sessions: Dict[str, ClientSession] = {}
_exit_stacks: Dict[str, AsyncExitStack] = {}
_mcp_tools: Optional[List[dspy.Tool]] = None


async def initialize_mcp_server(
    server_name: str,
    command: str,
    args: List[str],
    env: Optional[Dict[str, str]] = None
) -> Tuple[List[dspy.Tool], ClientSession, AsyncExitStack]:
    """Initialize an MCP server and get tools
    
    Args:
        server_name: Name of the MCP server (for logging)
        command: Command to run (e.g., "uvx")
        args: Arguments for the command
        env: Optional environment variables
    
    Returns:
        Tuple of (tools list, session, exit_stack) - all must be kept alive!
    """
    
    # MCP server parameters
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=env or {},
    )
    
    tools = []
    
    # Use AsyncExitStack to properly manage context managers
    exit_stack = AsyncExitStack()
    
    try:
        # Enter the stdio_client context
        read, write = await exit_stack.enter_async_context(stdio_client(server_params))
        
        # Create and enter session context
        session = ClientSession(read, write)
        await exit_stack.enter_async_context(session)
        
        # Initialize connection
        await session.initialize()
        
        # List available tools
        mcp_tools = await session.list_tools()
        
        # Convert MCP tools to DSPy tools
        # DSPy's from_mcp_tool creates async tools that work with async modules
        for mcp_tool in mcp_tools.tools:
            # Correct order: session first, then tool
            dspy_tool = dspy.Tool.from_mcp_tool(session, mcp_tool)
            tools.append(dspy_tool)
        
        logger.info(f"Loaded {len(tools)} tools from {server_name} MCP server")
        
        return tools, session, exit_stack
        
    except Exception as e:
        # Clean up on error
        await exit_stack.aclose()
        raise


async def initialize_strands_mcp() -> Tuple[List[dspy.Tool], ClientSession, AsyncExitStack]:
    """Initialize Strands MCP server and get tools
    
    Returns:
        Tuple of (tools list, session, exit_stack) - all must be kept alive!
    """
    return await initialize_mcp_server(
        server_name="Strands",
        command="uvx",
        args=["strands-agents-mcp-server"],
        env={"FASTMCP_LOG_LEVEL": "ERROR"}
    )


async def initialize_aws_docs_mcp() -> Tuple[List[dspy.Tool], ClientSession, AsyncExitStack]:
    """Initialize AWS Documentation MCP server and get tools
    
    Provides access to AWS Bedrock AgentCore documentation.
    
    Returns:
        Tuple of (tools list, session, exit_stack) - all must be kept alive!
    """
    return await initialize_mcp_server(
        server_name="AWS Bedrock agent core documentation",
        command="uvx",
        args=["awslabs.amazon-bedrock-agentcore-mcp-server@latest"],
        env={
            "FASTMCP_LOG_LEVEL": "ERROR"
        }
    )


async def get_all_mcp_tools(force_reload: bool = False, strands_only = False) -> List[dspy.Tool]:
    """Get all MCP tools from both Strands and AWS Documentation servers
    
    Uses uvx 
    Caches the tools globally to avoid creating multiple sessions.
    
    Args:
        force_reload: If True, force reload even if tools are cached
    
    Returns:
        List of DSPy tools from all MCP servers
    """
    global _mcp_sessions, _exit_stacks, _mcp_tools
    
    # Return cached tools if available
    if _mcp_tools and not force_reload:
        logger.info(f"Returning {len(_mcp_tools)} cached MCP tools")
        return _mcp_tools
    
    all_tools = []
    
    # Initialize Strands MCP server
   
    try:
        tools, session, exit_stack = await initialize_strands_mcp()
        _mcp_sessions["strands"] = session
        _exit_stacks["strands"] = exit_stack
        all_tools.extend(tools)
        logger.info(f"✓ Loaded {len(tools)} tools from Strands MCP server")
    except Exception as e:
        logger.warning(f"Failed to load Strands MCP tools: {e}")
    
    # Initialize AWS agentcore docs MCP server

    try:
        tools, session, exit_stack = await initialize_aws_docs_mcp()
        _mcp_sessions["aws_docs"] = session
        _exit_stacks["aws_docs"] = exit_stack
        all_tools.extend(tools)
        logger.info(f"✓ Loaded {len(tools)} tools from AWS agentcore MCP server")
    except Exception as e:
        logger.warning(f"Failed to load AWS Documentation MCP tools: {e}")

    # Cache all tools
    _mcp_tools = all_tools
    logger.info(f"Successfully loaded {len(all_tools)} total MCP tools")
    
    return all_tools


async def get_strands_mcp_tools(force_reload: bool = False) -> List[dspy.Tool]:
    """Get Strands documentation tools from MCP server
    
    Deprecated: Use get_all_mcp_tools() instead to get both Strands and AWS docs.
    
    Args:
        force_reload: If True, force reload even if tools are cached
    
    Returns:
        List of DSPy tools for Strands documentation
    """
    return await get_all_mcp_tools(force_reload=force_reload)


async def cleanup_mcp_sessions():
    """Clean up all MCP sessions and resources
    
    Note: Due to async context manager limitations, cleanup may fail if called
    from a different async context than where sessions were created. This is
    expected behavior and the sessions will be cleaned up when the process exits.
    """
    global _mcp_sessions, _exit_stacks, _mcp_tools
    
    for server_name, exit_stack in list(_exit_stacks.items()):
        try:
            await exit_stack.aclose()
            logger.info(f"MCP session cleaned up: {server_name}")
        except (RuntimeError, asyncio.CancelledError) as e:
            # Expected error when cleaning up from different async context
            logger.debug(f"MCP session cleanup skipped for {server_name} (will cleanup on exit): {e}")
        except Exception as e:
            logger.warning(f"Unexpected error cleaning up {server_name} MCP session: {e}")
    
    _mcp_sessions.clear()
    _exit_stacks.clear()
    _mcp_tools = None
    logger.info("MCP sessions marked for cleanup")


def get_strands_tools_sync() -> List[dspy.Tool]:
    """Synchronous wrapper for getting Strands MCP tools
    
    Returns:
        List of DSPy tools for Strands documentation
    """
    return asyncio.run(get_strands_mcp_tools())
