# GitHub Copilot Agent Instructions

Refer to `documents/PROJECT.md` for project-specific details.

> **AI Agent Operation Manual**: When operating as "Autonomous Researcher",
> refer to `documents/AGENT_MANUAL.md`.

---

## 0. Agent Tools (AI Agent Only)

### Overview

Project operations are performed via **MCP tools** (preferred) or CLI fallback.
All tools output in **JSON format** to prevent parsing errors.

### Tool Priority: MCP First

| Priority | Method | When to Use |
|----------|--------|-------------|
| 1 | **MCP Tools** | Default - real-time, integrated |
| 2 | CLI Fallback | MCP unavailable |
| 3 | Manual sbatch | Human-only (never for AI agents) |

**MCP Tools (Preferred):**
| Tool | Purpose |
|------|------|
| `mcp_slurm-agent-t_slurm_agent_get_status` | Check project/cluster status |
| `mcp_slurm-agent-t_slurm_agent_submit_job` | Submit SLURM job |
| `mcp_slurm-agent-t_slurm_agent_analyze_log` | Analyze logs/errors |
| `mcp_slurm-agent-t_slurm_agent_save_result` | Save experiment results |
| `mcp_slurm-agent-t_slurm_agent_compare_results` | Compare experiments |
| `mcp_slurm-agent-t_slurm_agent_validate_config` | Validate config files |
| `mcp_memory_*` | Store/retrieve agent memory |

**CLI Fallback (MCP Unavailable):**
```bash
uv run python -m tools.agent_tools.get_status
uv run python -m tools.agent_tools.submit_job --script script.sh
uv run python -m tools.agent_tools.analyze_log --job-id <id>
```

### Required Procedures

1. **Before experiments**: Check status with `mcp_slurm-agent-t_slurm_agent_get_status`
2. **Create configs**: Generate in `configs/generated/` (DO NOT modify base configs)
3. **Submit jobs**: Use MCP `submit_job` (DO NOT run sbatch directly)
4. **On failure**: Analyze with `analyze_log` → Store findings in Memory MCP

### Safety Policy

Follow constraints defined in `configs/agent_policy.yaml`:

- Maximum concurrent jobs: 4
- Protected files: DO NOT modify
- Auto-retry: Disabled

**Detailed procedures**: See `documents/AGENT_MANUAL.md`

### Memory Management

Use **Memory MCP** (`mcp_memory_*`) for all transient data:
- Experiment observations → `mcp_memory_store_memory`
- Prior context lookup → `mcp_memory_retrieve_memory`
- Tag-based search → `mcp_memory_search_by_tag`

**DO NOT** create local `*.memory.md` files. Use Memory MCP exclusively.

### SLURM Management

**Delegate to `@slurm-manager` agent** for all job operations.

- **Agent**: `@slurm-manager` (use `runSubagent`)
- **Skill Reference**: `.github/skills/slurm-management/SKILL.md`
- **Protocol**: Agent handles wait loops, resource optimization, and failure analysis

---

## 0.1. System Reasoning Framework

You are a very strong reasoner and planner. Use these critical instructions to structure your plans, thoughts, and responses.

Before taking any action (either tool calls _or_ responses to the user), you must proactively, methodically, and independently plan and reason about:

1. **Logical dependencies and constraints**: Analyze the intended action against the following factors. Resolve conflicts in order of importance:

   1. Policy-based rules, mandatory prerequisites, and constraints.
   2. Order of operations: Ensure taking an action does not prevent a subsequent necessary action.
      1. The user may request actions in a random order, but you may need to reorder operations to maximize successful completion of the task.
   3. Other prerequisites (information and/or actions needed).
   4. Explicit user constraints or preferences.

2. **Risk assessment**: What are the consequences of taking the action? Will the new state cause any future issues?

   1. For exploratory tasks (like searches), missing _optional_ parameters is a LOW risk. **Prefer calling the tool with the available information over asking the user, unless** your `Rule 1` (Logical Dependencies) reasoning determines that optional information is required for a later step in your plan.

3. **Abductive reasoning and hypothesis exploration**: At each step, identify the most logical and likely reason for any problem encountered.

   1. Look beyond immediate or obvious causes. The most likely reason may not be the simplest and may require deeper inference.
   2. Hypotheses may require additional research. Each hypothesis may take multiple steps to test.
   3. Prioritize hypotheses based on likelihood, but do not discard less likely ones prematurely. A low-probability event may still be the root cause.

4. **Outcome evaluation and adaptability**: Does the previous observation require any changes to your plan?

   1. If your initial hypotheses are disproven, actively generate new ones based on the gathered information.

5. **Information availability**: Incorporate all applicable and alternative sources of information, including:

   1. Using available tools and their capabilities
   2. All policies, rules, checklists, and constraints
   3. Previous observations and conversation history
   4. Information only available by asking the user

6. **Precision and Grounding**: Ensure your reasoning is extremely precise and relevant to each exact ongoing situation.

   1. Verify your claims by quoting the exact applicable information (including policies) when referring to them.

7. **Completeness**: Ensure that all requirements, constraints, options, and preferences are exhaustively incorporated into your plan.

   1. Resolve conflicts using the order of importance in #1.
   2. Avoid premature conclusions: There may be multiple relevant options for a given situation.
      1. To check for whether an option is relevant, reason about all information sources from #5.
      2. You may need to consult the user to even know whether something is applicable. Do not assume it is not applicable without checking.
   3. Review applicable sources of information from #5 to confirm which are relevant to the current state.

8. **Persistence and patience**: Do not give up unless all the reasoning above is exhausted.

   1. Don't be dissuaded by time taken or user frustration.
   2. This persistence must be intelligent: On _transient_ errors (e.g. please try again), you _must_ retry **unless an explicit retry limit (e.g., max x tries) has been reached**. If such a limit is hit, you _must_ stop. On _other_ errors, you must change your strategy or arguments, not repeat the same failed call.

9. **Inhibit your response**: only take an action after all the above reasoning is completed. Once you've taken an action, you cannot take it back.

---

## 0.2. Agent Interaction Protocol

### Subagent Invocation Rules
1.  **MUST USE** `runSubagent` to invoke specialized agents.
2.  **NEVER** simulate agent outputs. Always invoke and wait for results.
3.  **Parallel Invocation**: Call independent agents simultaneously.

### Mandatory Research Phase
>**Constraint**: Before complex implementation/optimization, perform research first.

1.  **Multi-perspective Research**: Use 2+ research agents (`@research-gpt`, `@research-gemini`, `@research-claude`)
2.  **External Verification**: Use Context7 MCP, ArXiv MCP, or web search
3.  **Explicit Citation**: Must cite actual papers/documentation

### Hardware-Aware Optimization
1.  **Check Capabilities**: Use `gpu-monitor` MCP to check hardware
2.  **Match Optimization**:
    - **H100**: FP8, TMA, FlashAttention-3
    - **A100**: BF16, FlashAttention-2
    - **Consumer GPU**: FP16, Gradient Checkpointing, LoRA

---

## 0.3. Specialized Agent Protocol

**Use specialists over generalists when available.**

| Task Domain | Specialist Agent |
| :--- | :--- |
| SLURM / GPU Jobs | `@slurm-manager` |
| CUDA / Triton Optimization | `@core-optimizer` |
| Documentation | `@doc-writer`, `@doc-reviewer` |
| Mathematical Verification | `@math-reviewer` |
| Resource Planning | `@planner-gemini` |
| Code Quality | `@code-quality-reviewer` |
| Research | `@research-gpt`, `@research-gemini`, `@research-claude` |

See `AGENTS.md` for full agent list and descriptions.

---

## 1. Language Policy

### Documentation (Korean)

Write in **Korean** for documents requiring frequent human review:

- `documents/notes/` - Experiment notes
- `documents/final/` - Final reports
- `documents/issues/` - Issue tracking
- `documents/PROJECT.md` - Project status
- `documents/AGENT_MANUAL.md` - Agent manual
- `documents/CHANGELOG.md` - Version changes

### Rationale

- **English for code**: Token efficiency, universal tooling compatibility
- **Korean for reports**: Better readability for human reviewers

### Mathematical Notation

- **Inline**: Use single `$` (e.g., $\Delta W$)
- **Block**: Use double `$$` for centered equations
- **Variables**: Use consistent notation (e.g., $W$ for weights, $x$ for input)

---

## 2. Code Guidelines

### Library Verification Strategy (Priority)

1. **Search First**: Before implementing code with external libraries, use `mcp_context7` or web search to confirm the latest API usage.
2. **Avoid Hallucination**: Do not rely solely on training data for rapidly evolving libraries (e.g., `transformers`, `accelerate`, `wandb`).
3. **Document & Reuse**:
   - If you perform a search for API usage, summarize the findings.
   - Create/Update a reference file in `documents/reference/API_<library>_<topic>.md` (in Korean).
   - Refer to this documentation in future tasks instead of searching again.

- **Korean comments**: Write comments and docstrings in Korean
- **Type hints**: STRICTLY required for all functions, arguments, and return values. Ensure compatibility with static type checkers (mypy/pyright).
- **Error handling**: Handle exceptions explicitly
- **Tests**: Write tests for core features
- **Modularity**: Separate files by function
- **Legacy code**: Move deprecated code to `주말농장/` (Weekend Farm)

### Legacy Code Management

- **Criteria**: Code that is no longer used but contains valuable logic or experimental history.
- **Action**: Move to `archive/` directories to minimize information loss.
- **Structure**:
  - `src/experiments/archive/<phase>/` - Archived experiment code
  - `scripts/archive/<phase>/` - Archived scripts
  - `results/archive/<phase>/` - Archived results
  - `documents/archive/<phase>/` - Archived documentation
- **Note**: Do NOT delete files. Move them to `archive/` instead.

### Temporary Code

- **Location**: Use the `temp/` directory in the project root for temporary scripts or experiments.
- **Restriction**: Do NOT use `/tmp` or other system directories to avoid permission issues and context loss.
- **Cleanup**: The `temp/` directory is ignored by git, but you should clean it up periodically.
- **Weekend Farm (주말농장)**: Use `주말농장/` ONLY for code/data intended to be completely discarded. Do not store valuable history here.

### Standard Library Usage (Preferred)

- **Training**: Use `transformers.Trainer` instead of custom training loops
- **Acceleration**: Use `accelerate` API instead of direct `torch.compile()` calls
- **Checkpoints**: Use `.save_pretrained()` with safetensors format when possible
- **Avoid eager mode training**: Prefer compiled/optimized execution

```python
# ❌ Avoid
for batch in dataloader:
    loss = model(batch)
    loss.backward()
    optimizer.step()

# ✅ Preferred
from transformers import Trainer, TrainingArguments
trainer = Trainer(model=model, args=training_args, ...)
trainer.train()

# ❌ Avoid direct compile
model = torch.compile(model)

# ✅ Preferred - let accelerate handle it
from accelerate import Accelerator
accelerator = Accelerator()
model = accelerator.prepare(model)
```

### Checkpoint Guidelines

- **Format**: Use safetensors (`.safetensors`) when available, fallback to `.pt`
- **Method**: Prefer `model.save_pretrained()` over `torch.save()`
- **Location**: Save to `results/<experiment>/checkpoints/`

```python
# ✅ Preferred
model.save_pretrained("results/exp/checkpoints/", safe_serialization=True)

# ✅ Acceptable for custom state
torch.save(state_dict, "results/exp/checkpoints/model.pt")
```

---

## 3. GPU Experiments (SLURM)

**Delegate to `@slurm-manager` agent for all SLURM operations.**

### Hard Rules (Non-negotiable)

- **ALL** GPU jobs **MUST** be submitted via SLURM
- **NEVER** set `CUDA_VISIBLE_DEVICES` manually
- **NEVER** hardcode device indices (`cuda:0`, `cuda:1`)
- **Memory default**: 16GB (>32GB requires justification)
- **Max concurrent jobs**: 4

### Quick Reference

```bash
# ❌ FORBIDDEN (AI Agent)
uv run python src/experiments/script.py  # Direct execution
sbatch script.sh  # AI must not use sbatch directly

# ✅ CORRECT (AI Agent)
# Use MCP or @slurm-manager agent
mcp_slurm-agent-t_slurm_agent_submit_job(script="run.sh")
```

### Detailed Protocol

→ **Skill**: `.github/skills/slurm-management/SKILL.md`
→ **Agent**: `@slurm-manager`

---

## 4. Experiment Logging

- **Path**: `results/<experiment_type>/`
- **Filename**: `YYYY-MM-DD_HH-MM-SS_<name>.json`
- **Format**: JSON with reproducible config

### Result Schema Standard

```json
{
  "experiment_name": "str",
  "timestamp": "ISO8601",
  "config": { ... },
  "metrics": {
    "loss": float,
    "accuracy": float,
    ...
  },
  "git_hash": "str",
  "notes": "str (optional)"
}
```

Document in `documents/notes/`:

```markdown
# <Title>

**Date**: YYYY-MM-DD
**Goal**: <description>

## Setup

## Results

## Conclusions
```

---

## 5. Documentation Workflow

**Use Skills and Agents for documentation tasks.**

### Available Skills

| Skill | Path | Purpose |
|-------|------|------|
| Documentation | `.github/skills/documentation/SKILL.md` | Reports, notes, technical docs |
| Data Analysis | `.github/skills/data-analysis/SKILL.md` | Result visualization |
| Code Review | `.github/skills/code-review/SKILL.md` | Code quality checklist |
| Deep Research | `.github/skills/deep-research/SKILL.md` | Literature/technical research |
| SLURM | `.github/skills/slurm-management/SKILL.md` | Job management |

### Available Agents

| Agent | Purpose |
|-------|------|
| `@doc-writer` | Create documentation |
| `@doc-reviewer` | Review documentation |
| `@research-*` | Research tasks |

### Document Locations

| Type | Path | Language |
|------|------|------|
| Final Reports | `documents/final/` | Korean |
| Drafts | `documents/drafts/` | Korean |
| Technical Reference | `documents/reference/technical/` | Korean |
| Paper Summaries | `documents/reference/papers/` | Korean |

---

## 6. Dependencies

```bash
uv add <package>    # Install
uv sync             # Sync environment
````

---

## 7. Git Workflow

- `master`: Stable
- `feature/<name>`: New features
- `experiment/<name>`: Experiments

```text
<type>: <subject>
Types: feat, fix, docs, refactor, test, chore
```

---

## 8. Project Documentation Structure

**Publish-First Approach: Documents as deliverables only**

The `documents/` directory is RESERVED for human-readable, curated reports.
Raw logs, scratchpads, and intermediate data must LIVE IN MEMORY (MCP) or `logs/`.

```text
documents/
├── PROJECT.md          # Project overview & high-level status
├── AGENT_MANUAL.md     # AI Agent operation manual
├── final/              # 🟢 PUBLISHED: Completed, verified reports
│   └── <TOPIC>_FINAL.md
├── drafts/             # 🟡 DRAFTS: Curated but not yet final
│   └── <TOPIC>_DRAFT.md
├── reference/          # 🔵 REFERENCE: External papers/docs
│   ├── papers/
│   └── technical/
└── templates/          # ⚪ TEMPLATES: Reporting templates
```

### 🚫 STRICTLY PROHIBITED in `documents/`
- **Raw Logs / Scratchpads**: Use Memory MCP (`store_memory`)
- **Daily Updates / TODOs**: Use Memory MCP (`manage_todo`)
- **"Just in case" Notes**: If it's not worth curating, it's not a document.

### The Pipeline: Capture → Curate → Publish

1.  **Capture (Memory Layer)**
    - Agent stores raw observations, errors, and intermediate thoughts in Memory MCP.
    - *Action*: `mcp_memory_store_memory(content="Experiment X failed with OOM...", tags=["exp", "error"])`

2.  **Curate (Draft Layer)**
    - Agent synthesizes multiple memory entries into a structured draft.
    - *Action*: Create `documents/drafts/EXP_ANALYSIS_DRAFT.md`

3.  **Publish (Final Layer)**
    - Human or Reviewer Agent approves the draft. Moves to `final/`.
    - *Action*: `mv documents/drafts/x.md documents/final/x.md`

### Directory Rules
- **final/**: Truth. Reviewed. Permanent.
- **drafts/**: Work in progress. Semantically structured.
- **reference/**: External knowledge source.
- **templates/**: Standard forms for new documents.

### Deprecated Paths → Memory MCP

| ❌ Deprecated | ✅ Use Instead |
|--------------|----------------|
| `documents/notes/` | `mcp_memory_store_memory` with tags |
| `documents/issues/` | `mcp_memory_store_memory` (tag: `issue`) |
| `documents/development/` | `mcp_memory_store_memory` |
| `documents/todo.md` | `manage_todo_list` tool |
| `*.memory.md` files | `mcp_memory_*` tools |

**Exception**: Major post-mortem reports go to `documents/final/`

---

## 9. Code & Script Structure

```text
src/
├── experiments/        # Main experiment code
│   └── <phase_name>/   # Active phase code
├── adapters/           # Model adapters/wrappers
├── data/               # Data loading & processing
└── utils/              # Shared utilities

scripts/
└── slurm/              # SLURM submission scripts
    └── generated/      # Auto-generated scripts

tools/
├── agent_tools/        # CLI fallback (when MCP unavailable)
│   ├── get_status.py
│   ├── submit_job.py
│   ├── analyze_log.py
│   ├── save_result.py
│   ├── compare_results.py
│   └── validate_config.py
└── mcp_servers/        # MCP servers (preferred)
    ├── slurm_agent_tools.py  # Primary SLURM interface
    ├── gpu_monitor_server.py
    └── wandb_analysis_server.py
```

### Available MCP Servers

Configured in `.vscode/mcp.json`:

| Server | Tools | Purpose |
|--------|-------|------|
| `slurm-agent-t` | `slurm_agent_*` | SLURM job management |
| `memory` | `mcp_memory_*` | Persistent agent memory |
| `context7` | `mcp_context7_*` | Library documentation |
| `sequentialthinking` | `sequentialthinking` | Complex reasoning |
| `gpu-monitor` | GPU status | Real-time GPU monitoring |
| `tb-query` | TensorBoard queries | Log analysis |
| `arxiv-mcp-server` | Paper search | Literature research |
| `wandb-analysis` | W&B queries | Experiment tracking |
```
