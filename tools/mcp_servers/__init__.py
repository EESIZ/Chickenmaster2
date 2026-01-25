"""MCP Servers for AI Agent Integration.

Provides Model Context Protocol servers for SLURM resource tracking
and other infrastructure monitoring capabilities.

Servers:
- slurm_server.py: SLURM job and resource tracking MCP server
- slurm_agent_tools.py: MCP wrapper for agent tools (submit, wait, analyze, etc.)
- web_search_server.py: Lightweight web search + page fetching MCP server

Usage:
    # Start servers via VS Code MCP configuration (.vscode/mcp.json)
    # Or manually:
    uv run python -m tools.mcp_servers.slurm_server
    uv run python -m tools.mcp_servers.slurm_agent_tools
    uv run python -m tools.mcp_servers.web_search_server
"""
