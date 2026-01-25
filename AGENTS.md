# AGENTS.md

## Project Overview

This is a research experiment template repository designed for ML/AI experiments with GPU cluster (SLURM) integration. It provides:

- **Custom Agents**: Specialized AI agents for research tasks (deep research, autonomous fixing)
- **Agent Skills**: Reusable workflows for common operations (SLURM management, documentation, code review)
- **Experiment Infrastructure**: Standardized logging, result tracking, and documentation

## Repository Structure

```
.
├── .github/
│   ├── agents/              # Custom agent definitions (.agent.md)
│   ├── skills/              # Agent Skills (folders with SKILL.md)
│   └── copilot-instructions.md  # Global Copilot instructions
├── configs/                 # Experiment configurations
├── documents/               # Project documentation
│   ├── notes/               # Experiment notes
│   ├── final/               # Final reports
│   ├── reference/           # Technical references
│   └── skills/              # Human-readable skill references
├── logs/slurm/              # SLURM job logs
├── results/                 # Experiment results (JSON)
├── scripts/
│   └── slurm/               # SLURM submission scripts
├── src/                     # Source code
│   ├── experiments/         # Main experiment code
│   ├── data/                # Data processing
│   └── utils/               # Utilities
├── tools/                   # AI Agent tools
│   ├── agent_tools/         # CLI tools for AI agents (JSON output)
│   └── mcp_servers/         # MCP servers for real-time integration
└── tests/                   # Test files
```

## Setup Commands

```bash
# Install dependencies
uv sync

# Check project status (AI agent via MCP - preferred)
# Use mcp_slurm-agent-t_slurm_agent_get_status

# CLI fallback (when MCP unavailable)
uv run python -m tools.agent_tools.get_status

# Submit SLURM job (humans only - AI agents use MCP)
sbatch scripts/slurm/run_experiment.sh

# Run tests
uv run pytest tests/
```

## Development Workflow

### Working with Agents, Skills, and Chat Modes

#### Agent Files (`*.agent.md`)

Location: `.github/agents/`

Custom agent definitions with specialized behaviors and tool access.

**Required Frontmatter:**
- `name`: Agent identifier (lowercase with hyphens)
- `description`: What the agent does (wrapped in single quotes)

**Optional Frontmatter:**
- `tools`: Array of tool names/patterns the agent can use
- `argument-hint`: Describes expected input format
- `model`: Preferred LLM model
- `infer`: Enable inference mode

Example:
```yaml
---
name: my-agent
description: 'Description of what the agent does and when to use it.'
tools:
  - read
  - search
  - execute
  - memory/*
---

# Agent Instructions
...
```

#### Chat Mode Files (`*.chatmode.md`) - DEPRECATED

> **Note**: As of VS Code 1.100+, chat modes have been merged into agents.
> Use `.agent.md` files in `.github/agents/` instead.

#### Prompt Files (`*.prompt.md`)

Location: `.github/prompts/`

Reusable prompt templates. Configure via `chat.promptFilesLocations` setting.

**Frontmatter:**
- `agent`: Agent name to use ('agent' mode is now 'agent' field)
- `tools`: Array of tools to use
- `description`: Short description

Example:
```yaml
---
agent: 'agent'
tools: ['codebase', 'githubRepo']
description: 'Generate a new experiment configuration'
---

Your goal is to create a new experiment config...
```

#### Instruction Files (`*.instructions.md`)

Location: `.github/` or configured folders

Modular instruction sets that can be combined. Configure via `chat.instructionsFilesLocations` setting.

#### Agent Skills (`skills/*/SKILL.md`)

Location: `.github/skills/<skill-name>/SKILL.md`

- Each skill is a folder containing a `SKILL.md` file
- SKILL.md must have `name` field (lowercase with hyphens, matching folder name)
- SKILL.md must have `description` field (wrapped in single quotes, 10-1024 chars)
- Skills can include bundled assets (scripts, templates, data files)
- Skills follow the [Agent Skills specification](https://agentskills.io/specification)

Example:
```yaml
---
name: my-skill
description: 'Description of the skill and when it should be loaded.'
---

# My Skill

## Usage
...

## Protocol
...
```

### Adding New Resources

**For Agents:**
1. Create `.github/agents/<name>.agent.md` with proper frontmatter
2. Define the agent's purpose, tools, and instructions
3. Test the agent with sample prompts

**For Skills:**
1. Create `.github/skills/<skill-name>/SKILL.md`
2. Add YAML frontmatter with `name` and `description`
3. Write clear instructions and examples
4. Optionally add bundled assets (scripts, templates)

## GPU/SLURM Policy

**CRITICAL**: All GPU jobs must be submitted via SLURM. Never run heavy computations on the login node.

```bash
# ❌ Wrong
uv run python train.py

# ✅ Correct
sbatch scripts/slurm/train.sh
```

Key constraints:
- Default memory: 16GB (avoid 32GB+ unless necessary)
- Submit multiple parallel jobs rather than sequential runs
- Use MCP tools (`slurm_agent_get_status`, `slurm_agent_wait_for_job`) for job management

## Language Policy

| Content | Language |
| :--- | :--- |
| Source code, configs, logs | English |
| Documentation, reports, notes | Korean |
| Skills, agent instructions | English |

## Available Agents

| Agent | Description |
| :--- | :--- |
| `@research-gemini` | Implementation-focused research (Code, API, Hardware) |
| `@research-gpt` | Theory-focused research (Concepts, Prior Work) |
| `@research-claude` | System/Safety-focused research (Complexity, Constraints) |
| `@fixer` | Autonomous problem-solving & execution agent. Diagnoses issues, implements fixes, executes code/tests, and verifies solutions. |
| `@planner-gemini` | Feasibility & Resource Planning (Quantitative) |
| `@planner-gpt` | Architecture & Strategy Planning (Structural) |
| `@planner-claude` | Risk & QA Planning (Safety) |
| `@idea-generator-gemini` | Feasibility & Resource Optimization Ideas |
| `@idea-generator-gpt` | System Architecture & Business Strategy Ideas |
| `@idea-generator-claude` | UX, Safety & Divergent Thinking Ideas |
| `@validator` | Verification and validation of code, configs, and outputs |
| `@code-generator` | Code generation with best practices and type safety |
| `@code-quality-reviewer` | Code quality assessment and improvement recommendations |
| `@doc-writer` | Documentation creation with proper formatting and structure |
| `@doc-reviewer` | Documentation review for completeness and accuracy |
| `@orchestrator` | Autonomous Task Manager. Interprets commands, plans workflows, and delegates to specialized subagents. |
| `@slurm-manager` | SLURM job submission, monitoring, and resource optimization |
| `@core-optimizer` | High-performance Triton/CUDA kernel optimization with strong verification |
| `@citation-tracer` | Builds research lineage via DFS citation chaining. Identifies foundational papers. |
| `@experience-curator` | Learns from project history. Extracts reusable patterns from logs, failures, and reviews. |
| `@math-reviewer` | Mathematical verification of research paper implementations. |
| `@qa-regression-sentinel` | Execution-based quality verification, reproduction scripts, and flaky test detection. |
| `@rubric-verifier` | Multi-perspective quality verification with rubrics and independent critics. |

## Available Skills

| Skill | Description |
| :--- | :--- |
| `deep-research` | Recursive research workflow (STORM-style) |
| `documentation` | Standardized documentation creation |
| `slurm-management` | GPU job submission and monitoring |
| `data-analysis` | Result visualization and comparison |
| `code-review` | Research code quality checklist |
| `skill-extension` | Create and extend agent skills |
| `external-skill-generation` | Generate skills from external docs (Skill Seekers) |

## Pull Request Guidelines

### Code Review Checklist

For agent files (`*.agent.md`):
- [ ] Has YAML frontmatter
- [ ] Has `name` field (lowercase with hyphens)
- [ ] Has non-empty `description` field in single quotes
- [ ] File name follows pattern `<name>.agent.md`

For skills (`skills/*/SKILL.md`):
- [ ] Folder contains a SKILL.md file
- [ ] SKILL.md has YAML frontmatter
- [ ] Has `name` field matching folder name
- [ ] Has non-empty `description` field (10-1024 characters)
- [ ] Any bundled assets are referenced in SKILL.md

For experiment code:
- [ ] Random seeds are fixed
- [ ] All hyperparameters in config files
- [ ] Type hints on all functions
- [ ] No data leakage between train/test
- [ ] Model in `.eval()` mode during validation

## Related Resources

- [Agent Skills Specification](https://agentskills.io/specification)
- [GitHub Awesome Copilot](https://github.com/github/awesome-copilot)
- [VS Code Copilot Customization](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
- [Skill Seekers](documents/reference/technical/NOTE_skill_seekers.md) - External skill generation tool (optional)
