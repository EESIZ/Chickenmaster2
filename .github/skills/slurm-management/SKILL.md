---
name: slurm-management
description: 'Protocol for managing GPU jobs on SLURM clusters, including submission, monitoring, and resource optimization. Essential for all heavy computations.'
---

# SLURM Management Skill

## Usage

Use this skill for all GPU jobs and heavy computations. NEVER run heavy computations on the login node directly.

## Tools (MCP)

| Tool | Description |
| :--- | :--- |
| `slurm_agent_get_status` | Get status (jobs/gpu/results) |
| `slurm_agent_wait_for_job` | Wait for completion |
| `slurm_agent_submit_job` | Submit SLURM job |
| `slurm_agent_analyze_log` | Analyze error logs |
| `slurm_agent_save_result` | Save experiment metrics |

## Protocol

### 1. Submission

**NEVER** run heavy computations on the login node. Always use `sbatch` or `submit_job`.

**Template** (`scripts/slurm/template.sh`):

```bash
#!/bin/bash
#SBATCH --job-name=exp_name
#SBATCH --output=logs/slurm/%j_%x.out
#SBATCH --error=logs/slurm/%j_%x.err
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=24:00:00

cd $PROJECT_ROOT
uv run python src/experiments/run.py "$@"
```

### 2. Waiting Logic (Agent Pattern)

Since MCP has a timeout, use a loop for long-running jobs:

1. Call `slurm_agent_wait_for_job(job_id, timeout=60)`.
2. If result is `timeout`, perform other tasks or wait again.
3. If result is `success`, proceed to analysis.

**Example Agent Loop**:

```python
# Pseudocode for agent waiting pattern
while True:
    result = slurm_agent_wait_for_job(job_id, timeout=60)
    if result.status == "COMPLETED":
        break
    elif result.status == "FAILED":
        analyze_log(job_id)
        raise Exception("Job failed")
    # else: timeout, continue waiting
```

### 3. Resource Optimization

- **Memory**: Default to 16GB. Requesting >32GB may delay scheduling.
- **Parallelism**: Submit multiple independent jobs rather than one sequential job.
- **GPU Assignment**: Do NOT set `CUDA_VISIBLE_DEVICES` manually. Let SLURM handle it.

### 4. Best Practices

1. **Create separate scripts** for each experiment configuration.
2. **Submit all at once** to maximize cluster utilization.
3. **Use generous time limits** (e.g., 24 hours) to prevent premature termination.
4. **Log everything** to `logs/slurm/` for debugging.

## Transparency & Thinking

```
🧠 THINKING:
- **Action**: [Submit/Wait/Analyze]
- **Job ID**: [Job ID if applicable]
- **Status**: [Pending/Running/Completed/Failed]
- **Next Step**: [What to do next?]
```
