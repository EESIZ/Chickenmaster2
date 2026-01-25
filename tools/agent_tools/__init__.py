"""Agent Tools Module

Provides JSON-based interfaces for AI agents to operate the project.

Tools:
- get_status.py: Query project status (jobs, GPU, results, errors) with caching
- submit_job.py: Submit SLURM jobs with safety checks
- wait_for_job.py: Wait for SLURM job completion
- analyze_log.py: Analyze log files and summarize errors
- save_result.py: Save experiment results with schema validation
- compare_results.py: Compare two experiment results
- validate_config.py: Validate experiment configuration files
- analyze_python_code.py: Analyze Python source files using AST

Usage:
    uv run python -m tools.agent_tools.get_status
    uv run python -m tools.agent_tools.submit_job --script run_experiment.sh
    uv run python -m tools.agent_tools.wait_for_job --job-id <job_id>
    uv run python -m tools.agent_tools.analyze_log --job-id <job_id>
    uv run python -m tools.agent_tools.save_result --name <name> --metrics '{}'
    uv run python -m tools.agent_tools.compare_results --baseline a.json --target b.json
    uv run python -m tools.agent_tools.validate_config --config exp.yaml
    uv run python -m tools.agent_tools.analyze_python_code --file path/to/file.py
"""
