"""Tools agent that leverages strands-agents-tools for extended capabilities."""

from __future__ import annotations

from typing import Any, Dict

from app.strands.tools_integration import execute_tool, get_available_tools, is_available


async def tools_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent that uses strands-agents-tools for extended capabilities.

    Handles queries like:
    - "Search the web for information about..."
    - "Read file at path..."
    - "Execute this Python code..."
    - "Make HTTP request to..."

    Args:
        query: User query
        context: Context dictionary with user_id, session, etc.

    Returns:
        Dictionary with reply and result
    """
    if not is_available():
        return {
            "reply": (
                "Advanced tools are not available. "
                "Install with: pip install strands-agents-tools"
            )
        }

    # Detect intent from query
    query_lower = query.lower()

    # Web search
    if any(kw in query_lower for kw in ["search", "find", "look up", "google"]):
        # Extract search query (simplified)
        search_query = query
        for prefix in ["search for ", "find ", "look up ", "google "]:
            if prefix in query_lower:
                search_query = query[query_lower.index(prefix) + len(prefix):]
                break

        result = await execute_tool("web_search", query=search_query, limit=5)
        if result.get("success"):
            return {
                "reply": f"I found information about '{search_query}'",
                "results": result.get("result"),
                "tool_used": "web_search"
            }
        return {
            "reply": f"Sorry, I couldn't search for that: {result.get('error')}",
            "tool_used": "web_search"
        }

    # File read
    if any(kw in query_lower for kw in ["read file", "show file", "file content"]):
        # Try to extract file path
        parts = query.split()
        file_path = None
        for i, part in enumerate(parts):
            if part.lower() in ["file", "path"] and i + 1 < len(parts):
                file_path = parts[i + 1]
                break

        if not file_path:
            return {
                "reply": "Please specify a file path. Example: 'read file /path/to/file.txt'"
            }

        result = await execute_tool("file_read", path=file_path)
        if result.get("success"):
            content = result.get("result", "")
            preview = content[:500] + "..." if len(content) > 500 else content
            return {
                "reply": f"File content:\n{preview}",
                "full_content": content,
                "tool_used": "file_read"
            }
        return {
            "reply": f"Couldn't read file: {result.get('error')}",
            "tool_used": "file_read"
        }

    # List available tools
    if "what tools" in query_lower or "list tools" in query_lower:
        tools = get_available_tools()
        if not tools:
            return {
                "reply": "No tools currently available."
            }

        tools_by_category: Dict[str, list] = {}
        for tool in tools:
            category = tool.get("category", "other")
            if category not in tools_by_category:
                tools_by_category[category] = []
            tools_by_category[category].append(
                f"- {tool['name']}: {tool['description']}"
            )

        response_parts = ["Available tools:\n"]
        for category, tool_list in tools_by_category.items():
            response_parts.append(f"\n{category.upper()}:")
            response_parts.extend(tool_list)

        return {
            "reply": "\n".join(response_parts),
            "tools": tools
        }

    # Default response
    return {
        "reply": (
            "I have access to advanced tools like web search, file operations, "
            "and code execution. Try asking: 'search for...' or 'list tools'"
        )
    }


__all__ = ["tools_agent"]
