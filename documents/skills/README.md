# Skills Reference

**Official Location**: `.github/skills/`

Agent Skills are stored in `.github/skills/` following the [Agent Skills specification](https://agentskills.io/specification). Each skill is a folder containing:

- `SKILL.md`: Instructions with YAML frontmatter (required)
- Bundled assets: Scripts, templates, data files (optional)

## Available Skills

| Skill | Location | Description |
| :--- | :--- | :--- |
| **deep-research** | [.github/skills/deep-research/](../../.github/skills/deep-research/SKILL.md) | Recursive research workflow with multi-source verification |
| **documentation** | [.github/skills/documentation/](../../.github/skills/documentation/SKILL.md) | Standardized documentation creation protocol |
| **slurm-management** | [.github/skills/slurm-management/](../../.github/skills/slurm-management/SKILL.md) | GPU job submission and monitoring |
| **data-analysis** | [.github/skills/data-analysis/](../../.github/skills/data-analysis/SKILL.md) | Experiment result visualization and comparison |
| **code-review** | [.github/skills/code-review/](../../.github/skills/code-review/SKILL.md) | Research code quality checklist |
| **skill-extension** | [.github/skills/skill-extension/](../../.github/skills/skill-extension/SKILL.md) | Create and extend agent skills |
| **external-skill-generation** | [.github/skills/external-skill-generation/](../../.github/skills/external-skill-generation/SKILL.md) | Generate skills from external docs (Skill Seekers) |

## How Skills Work

Skills are automatically loaded by GitHub Copilot based on context:

1. **Discovery**: Copilot reads skill `name` and `description` from frontmatter
2. **Loading**: When a request matches a skill, the `SKILL.md` body is loaded
3. **Resources**: Additional files in the skill folder are accessed as needed

## Skill Architecture

```
.github/skills/
├── <skill-name>/
│   ├── SKILL.md           # Main skill file (required)
│   ├── templates/         # Template files (optional)
│   ├── scripts/           # Helper scripts (optional)
│   └── data/              # Reference data (optional)
```

### Skill Discovery Flow

```
User Request
    ↓
Copilot analyzes skill descriptions (YAML frontmatter)
    ↓
Matches relevant skill(s) based on context
    ↓
Loads SKILL.md content
    ↓
Accesses bundled assets as needed
    ↓
Executes skill protocol
```

## Creating New Skills

### 1. Create Skill Folder

```bash
mkdir -p .github/skills/<skill-name>
```

### 2. Create SKILL.md

```yaml
---
name: skill-name
description: 'Clear description of what the skill does (10-1024 chars)'
---

# Skill Name

## Usage
When to use this skill...

## Protocol
Step-by-step instructions...

## Examples
Concrete examples of usage...

## Templates (optional)
Reference templates bundled with this skill...
```

### 3. Add Bundled Assets (optional)

```bash
# Templates
.github/skills/<skill-name>/templates/template.md

# Scripts
.github/skills/<skill-name>/scripts/helper.py

# Data
.github/skills/<skill-name>/data/reference.json
```

## Skill Quality Checklist

- [ ] **Name**: Lowercase with hyphens, matches folder name
- [ ] **Description**: 10-1024 characters, wrapped in single quotes
- [ ] **Usage**: Clear explanation of when to use the skill
- [ ] **Protocol**: Step-by-step instructions
- [ ] **Examples**: At least one concrete example
- [ ] **Assets**: All bundled assets are referenced in SKILL.md

## Related Resources

- [AGENTS.md](../../AGENTS.md) - Full project agent documentation
- [Agent Skills Spec](https://agentskills.io/specification) - Official specification
- [Skill Seekers](../reference/technical/NOTE_skill_seekers.md) - External skill generation tool
