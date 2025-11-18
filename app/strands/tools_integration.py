"""Integration with strands-agents-tools library for enhanced agent capabilities.

This module provides a bridge between Jenny's agent architecture and the
strands-agents-tools library, which offers 50+ pre-built tools including:
- File operations (read, write, edit)
- Web search and content extraction
- Code execution
- Browser automation
- And more...

Usage:
    from app.strands.tools_integration import get_available_tools, execute_tool

    tools = get_available_tools()
    result = await execute_tool("web_search", query="AI agents", limit=5)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Flag to track if strands-agents-tools is available
STRANDS_TOOLS_AVAILABLE = False

try:
    # Try importing strands-agents-tools
    from strands_tools import (
        file_read,
        file_write,
        web_search,
        http_request,
        python_repl,
    )

    STRANDS_TOOLS_AVAILABLE = True
    logger.info("Strands Agents Tools loaded successfully")
except ImportError:
    logger.warning(
        "strands-agents-tools not available. "
        "Install with: pip install strands-agents-tools"
    )
    # Define dummy functions for graceful degradation
    file_read = None
    file_write = None
    web_search = None
    http_request = None
    python_repl = None


def get_available_tools() -> List[Dict[str, Any]]:
    """
    Get a list of available tools from strands-agents-tools.

    Returns:
        List of tool dictionaries with name, description, and function
    """
    if not STRANDS_TOOLS_AVAILABLE:
        return []

    tools = []

    if file_read:
        tools.append({
            "name": "file_read",
            "description": "Read contents of a file",
            "function": file_read,
            "category": "file_operations"
        })

    if file_write:
        tools.append({
            "name": "file_write",
            "description": "Write content to a file",
            "function": file_write,
            "category": "file_operations"
        })

    if web_search:
        tools.append({
            "name": "web_search",
            "description": "Search the web for information",
            "function": web_search,
            "category": "web"
        })

    if http_request:
        tools.append({
            "name": "http_request",
            "description": "Make HTTP requests to APIs",
            "function": http_request,
            "category": "web"
        })

    if python_repl:
        tools.append({
            "name": "python_repl",
            "description": "Execute Python code",
            "function": python_repl,
            "category": "code_execution"
        })

    return tools


async def execute_tool(
    tool_name: str,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Execute a tool from strands-agents-tools.

    Args:
        tool_name: Name of the tool to execute
        **kwargs: Arguments to pass to the tool

    Returns:
        Dictionary with result or error
    """
    if not STRANDS_TOOLS_AVAILABLE:
        return {
            "error": "strands-agents-tools not available",
            "message": "Please install: pip install strands-agents-tools"
        }

    tools_map = {
        "file_read": file_read,
        "file_write": file_write,
        "web_search": web_search,
        "http_request": http_request,
        "python_repl": python_repl,
    }

    tool_func = tools_map.get(tool_name)
    if not tool_func:
        return {
            "error": f"Tool '{tool_name}' not found",
            "available_tools": list(tools_map.keys())
        }

    try:
        result = tool_func(**kwargs)
        return {"success": True, "result": result}
    except Exception as exc:
        logger.error(f"Error executing tool {tool_name}: {exc}")
        return {"success": False, "error": str(exc)}


def is_available() -> bool:
    """Check if strands-agents-tools is available."""
    return STRANDS_TOOLS_AVAILABLE


__all__ = [
    "get_available_tools",
    "execute_tool",
    "is_available",
    "STRANDS_TOOLS_AVAILABLE",
]
