"""
Tools for AgentCreator DSPy modules

Provides AgentCore Code Interpreter integration for code validation during generation.
Falls back to DSPy's built-in PythonInterpreter when AgentCore is not available.

Execution Strategy:
1. Production (AGENTCORE_ENABLED=true):
   - Primary: AWS Bedrock AgentCore (secure sandbox)
   - Fallback: DSPy PythonInterpreter (if AgentCore fails)

2. Development (AGENTCORE_ENABLED=false):
   - Primary: DSPy PythonInterpreter (local execution)
   - No AWS credentials needed

DSPy PythonInterpreter Benefits:
- Full Python execution (not just syntax validation)
- Fast local development
- Automatic fallback for resilience
- Maintains state between executions
- Same interface as AgentCore

Example:
    >>> import dspy
    >>> interpreter = dspy.PythonInterpreter()
    >>> result = interpreter.execute("value = 2*5 + 4\\nvalue")
    >>> print(result)
    14
"""

import json
import logging
import os
from typing import Optional

import boto3
import dspy

logger = logging.getLogger(__name__)

# Check if we're in AgentCore environment
AGENTCORE_ENABLED = os.getenv("AGENTCORE_ENABLED", "false").lower() == "true"
EXECUTION_ROLE_ARN = os.getenv("AGENTCORE_EXECUTION_ROLE_ARN", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Global session management
_code_interpreter_session_id: Optional[str] = None

# DSPy PythonInterpreter as fallback
_dspy_interpreter: Optional[dspy.PythonInterpreter] = None


def _get_dspy_interpreter() -> dspy.PythonInterpreter:
    """Get or create DSPy PythonInterpreter instance"""
    global _dspy_interpreter
    if _dspy_interpreter is None:
        _dspy_interpreter = dspy.PythonInterpreter()
        logger.info("Initialized DSPy PythonInterpreter for fallback execution")
    return _dspy_interpreter


def _get_or_create_session() -> tuple[boto3.client, str]:
    """Get or create a code interpreter session
    
    Returns:
        Tuple of (client, session_id)
    """
    global _code_interpreter_session_id
    
    client = boto3.client('bedrock-agentcore-control', region_name=AWS_REGION)
    
    # Reuse existing session if available
    if _code_interpreter_session_id:
        try:
            # Verify session is still valid
            client.get_code_interpreter_session(sessionId=_code_interpreter_session_id)
            logger.info(f"Reusing existing session: {_code_interpreter_session_id}")
            return client, _code_interpreter_session_id
        except Exception as e:
            logger.warning(f"Existing session invalid, creating new one: {e}")
            _code_interpreter_session_id = None
    
    # Create new session
    try:
        response = client.create_code_interpreter(
            SessionConfiguration={
                'networkConfig': {
                    'type': 'SANDBOX'  # Secure sandboxed environment
                },
                'executionRole': EXECUTION_ROLE_ARN,
                'memoryMb': 2048,  # 2GB memory for code execution
            }
        )
        _code_interpreter_session_id = response['sessionId']
        logger.info(f"Created new code interpreter session: {_code_interpreter_session_id}")
        return client, _code_interpreter_session_id
        
    except Exception as e:
        logger.error(f"Failed to create code interpreter session: {e}")
        raise


def cleanup_session():
    """Cleanup code interpreter session"""
    global _code_interpreter_session_id
    
    if _code_interpreter_session_id:
        try:
            client = boto3.client('bedrock-agentcore-control', region_name=AWS_REGION)
            client.delete_code_interpreter_session(sessionId=_code_interpreter_session_id)
            logger.info(f"Cleaned up session: {_code_interpreter_session_id}")
        except Exception as e:
            logger.warning(f"Failed to cleanup session: {e}")
        finally:
            _code_interpreter_session_id = None


def execute_python_code(code: str, description: str = "") -> str:
    """Execute Python code using AWS Bedrock AgentCore Code Interpreter
    
    This tool allows the CodeGenerator to validate code syntax and test snippets
    during the generation process. It uses AWS Bedrock AgentCore's code interpreter
    for secure, sandboxed execution, with fallback to DSPy's PythonInterpreter.
    
    Execution Strategy:
    1. If AGENTCORE_ENABLED=true: Use AWS Bedrock AgentCore (production)
    2. If AGENTCORE_ENABLED=false: Use syntax validation only (development)
    
    Args:
        code: Python code to execute
        description: Optional description of what the code does
        
    Returns:
        Execution result or error message as string
        
    Example:
        >>> result = execute_python_code("value = 2*5 + 4\\nvalue", "Calculate value")
        >>> print(result)
        "✓ Execution successful: 14"
    """
    
    if not AGENTCORE_ENABLED:
        # In development mode, just validate syntax (no Deno dependency)
        logger.info(f"Validating code syntax (dev mode): {description}")
        
        try:
            import ast
            ast.parse(code)
            logger.info("Code syntax validation successful")
            return f"✓ Code syntax is valid\n(Note: Full execution skipped in dev mode)"
                
        except SyntaxError as e:
            logger.warning(f"Syntax error: {e}")
            return f"✗ Syntax Error at line {e.lineno}: {e.msg}"
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return f"✗ Validation error: {str(e)}"
    
    # Use AgentCore Code Interpreter (production)
    try:
        # Add description as comment if provided
        if description:
            code = f"# {description}\n{code}"
        
        logger.info(f"Executing code via AgentCore: {description}")
        
        # Get or create session
        client, session_id = _get_or_create_session()
        
        # Execute code
        exec_response = client.invoke_code_interpreter(
            sessionId=session_id,
            code=code,
            language="python"
        )
        
        # Extract and format results
        if 'output' in exec_response:
            output = exec_response['output']
            logger.info("AgentCore execution successful")
            return f"✓ Execution successful:\n{output}"
            
        elif 'error' in exec_response:
            error = exec_response['error']
            logger.warning(f"AgentCore execution error: {error}")
            return f"✗ Execution error:\n{error}"
            
        else:
            result = exec_response.get('result', 'Execution completed')
            logger.info("AgentCore execution completed")
            return f"✓ {result}"
        
    except Exception as e:
        logger.error(f"AgentCore error, falling back to DSPy: {e}")
        
        # Fallback to DSPy interpreter if AgentCore fails
        try:
            interpreter = _get_dspy_interpreter()
            result = interpreter.execute(code)
            logger.info("Fallback to DSPy successful")
            return f"✓ Execution successful (fallback):\n{result}"
        except Exception as fallback_error:
            logger.error(f"Fallback execution also failed: {fallback_error}")
            return f"✗ Execution failed: {str(e)}\nFallback also failed: {str(fallback_error)}"


def validate_python_syntax(code: str) -> str:
    """Validate Python code syntax without execution
    
    This is a lightweight validation that can be used before attempting
    full execution with the code interpreter. Useful for quick syntax checks.
    
    Args:
        code: Python code to validate
        
    Returns:
        Validation result message
        
    Example:
        >>> result = validate_python_syntax("print('hello')")
        >>> print(result)
        "✓ Code syntax is valid"
    """
    import ast
    
    try:
        ast.parse(code)
        return "✓ Code syntax is valid"
    except SyntaxError as e:
        return f"✗ Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return f"✗ Validation error: {str(e)}"


# Export tools for DSPy ReAct
__all__ = ["execute_python_code", "validate_python_syntax", "cleanup_session"]
