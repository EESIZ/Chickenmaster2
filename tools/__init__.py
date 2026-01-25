"""Tools Module

Provides AI agent integration tools for the project.

Submodules:
- agent_tools: CLI tools for AI agents (JSON output)
- mcp_servers: MCP servers for real-time agent integration

Usage:
    # Agent Tools (CLI)
    uv run python -m tools.agent_tools.get_status
    uv run python -m tools.agent_tools.submit_job --script run_experiment.sh

    # MCP Servers (configured in .vscode/mcp.json)
    # Started automatically by VS Code when configured
"""
