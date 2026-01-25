# Template Setup Guide

This guide explains how to use this template for new research projects.

## 1. Creating a New Project

### Option A: GitHub Template (Recommended)

1. Click "Use this template" on GitHub
2. Name your new repository
3. Clone and start working

### Option B: Manual Copy

```bash
# Clone the template
git clone https://github.com/<owner>/template.git new-project
cd new-project

# Re-initialize Git
rm -rf .git
git init
git add .
git commit -m "Initial commit from template"
```

## 2. Initial Configuration

### Step 1: Environment Setup

```bash
# Install dependencies with uv
uv sync

# Verify installation
uv run python -c "import torch; print(torch.cuda.is_available())"
```

### Step 2: Update Project Files

1. **`pyproject.toml`**: Update project name, description, authors
2. **`README.md`**: Replace template description with your project info
3. **`documents/PROJECT.md`**: Define your research goals

### Step 3: Configure VS Code

Recommended extensions (automatically prompted):
- **GitHub Copilot** + **Copilot Chat**: AI assistance
- **Python** + **Pylance**: Python support
- **Context7 MCP Server**: Library documentation
- **Web Search for Copilot**: Web searching in Copilot

## 3. Understanding the AI Integration

### GitHub Copilot Instructions

The file `.github/copilot-instructions.md` contains rules for AI agents:

- **SLURM Policy**: All GPU jobs must use `sbatch`
- **Language Policy**: Code in English, docs in Korean
- **File Structure**: Where to save results, logs, notes

**Do not remove this file** — it ensures consistent AI behavior.

### AGENTS.md

The `AGENTS.md` file at the root provides:
- Project overview for AI agents
- Repository structure explanation
- Development workflow guidelines
- Code review checklists

### Custom Agents

Located in `.github/agents/`:
- `orchestrator.agent.md`: Autonomous task manager and delegator
- `fixer.agent.md`: General-purpose problem solver
- `research-{gemini,gpt,claude}.agent.md`: Model-specialized research agents
- `planner-{gemini,gpt,claude}.agent.md`: Specialized planning agents
- `idea-generator-{gemini,gpt,claude}.agent.md`: Specialized ideation agents
- `code-generator.agent.md`: For writing production code
- `validator.agent.md`: For cross-verification

### Agent Skills

Located in `.github/skills/`:

| Skill | When Loaded |
| :--- | :--- |
| `deep-research` | "research", "analyze", "investigate" |
| `documentation` | "document", "write report", "save note" |
| `slurm-management` | "submit job", "GPU", "SLURM" |
| `data-analysis` | "plot", "visualize", "compare results" |
| `code-review` | "review code", "check quality" |

Skills are automatically loaded based on your prompt.

## 4. Development Workflow

### Experiment Cycle

1. **Plan**: Create `documents/development/PHASE_PLAN.md`
2. **Implement**: Write code in `src/experiments/`
3. **Configure**: Define hyperparams in `configs/`
4. **Run**: Submit via SLURM
   ```bash
   sbatch scripts/slurm/run_experiment.sh
   ```
5. **Log**: Results auto-saved to `results/`
6. **Document**: Write note in `documents/notes/`

### Using AI Agent Tools

```bash
# Check project status
uv run python -m tools.agent_tools.get_status

# Submit SLURM job
uv run python -m tools.agent_tools.submit_job --script run_experiment.sh

# Wait for job completion
uv run python -m tools.agent_tools.wait_for_job --job-id <id>

# Analyze failed job
uv run python -m tools.agent_tools.analyze_log --job-id <id>
```

### Temporary Code

- **Directory**: `temp/` (git-ignored)
- **Purpose**: Quick tests, throwaway scripts, downloaded PDFs
- **Warning**: Do NOT use system `/tmp` — use project `temp/` instead

## 5. Directory Reference

```text
.
├── .github/
│   ├── agents/              # Custom AI agents
│   ├── skills/              # Agent Skills
│   └── copilot-instructions.md  # Global AI rules
├── AGENTS.md                # AI agent documentation
├── configs/
│   ├── default.yaml         # Base config
│   └── generated/           # AI-generated configs
├── documents/
│   ├── PROJECT.md           # Project overview
│   ├── notes/               # Daily experiment logs
│   ├── final/               # Final reports
│   ├── reference/           # Tech notes, papers
│   └── skills/              # Skills reference (links)
├── logs/slurm/              # SLURM job logs
├── results/                 # Experiment results
├── scripts/
│   ├── slurm/               # SLURM scripts
│   └── examples/            # Example scripts
├── tools/
│   ├── agent_tools/         # Python tools for AI
│   └── mcp_servers/          # MCP servers
├── src/
│   ├── experiments/         # Main experiment code
│   ├── data/                # Data loaders
│   └── utils/               # Utilities
├── temp/                    # Temporary files (ignored)
├── tests/                   # Test files
└── 주말농장/                # Throwaway code (ignored)
```

## 6. Key Policies

| Policy | Rule |
| :--- | :--- |
| **Language** | Code/configs in English, reports/notes in Korean |
| **GPU** | Always use SLURM, never run directly |
| **Memory** | Default 16GB, avoid 32GB+ |
| **Seeds** | Always fix seeds for reproducibility |
| **Legacy** | Move to `archive/`, never delete |
| **Type Hints** | Required for all functions |

## 7. Customization Checklist

Before starting your project:

- [ ] Update `pyproject.toml` with project metadata
- [ ] Update `README.md` with project description
- [ ] Edit `documents/PROJECT.md` with research goals
- [ ] Review `.github/copilot-instructions.md` for project-specific rules
- [ ] Create initial experiment config in `configs/`
- [ ] Test SLURM submission with a simple job
- [ ] Verify VS Code extensions are installed

---

**Happy Experimenting!** 🚀
