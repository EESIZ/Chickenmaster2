---
name: skill-extension
description: 'Protocol for creating, extending, and managing agent skills. Use when adding new capabilities or modifying existing skills for VS Code Copilot agents.'
---

# Skill Extension

Create and extend agent skills following the Agent Skills specification.

## Usage

Use this skill when:

- Creating a new skill for the project
- Extending or modifying existing skills
- Converting documentation into skills
- Setting up skill bundles with assets

## Prerequisites

Before creating a skill, understand:

1. **Skill Location**: `.github/skills/<skill-name>/SKILL.md`
2. **Naming**: Use lowercase with hyphens (e.g., `my-new-skill`)
3. **Description**: 10-1024 characters, wrapped in single quotes
4. **Assets**: Optional bundled files (templates, scripts, data)

## Protocol

### 1. Plan the Skill

```
🧠 THINKING:
- **Purpose**: What problem does this skill solve?
- **Trigger**: When should this skill be loaded?
- **Dependencies**: Does it depend on other skills or tools?
- **Assets**: Does it need templates, scripts, or data files?
```

### 2. Create Skill Structure

```bash
# Create skill folder
mkdir -p .github/skills/<skill-name>

# Create main skill file
touch .github/skills/<skill-name>/SKILL.md

# Optional: Create asset folders
mkdir -p .github/skills/<skill-name>/templates
mkdir -p .github/skills/<skill-name>/scripts
mkdir -p .github/skills/<skill-name>/data
```

### 3. Write SKILL.md

**Required Structure:**

```yaml
---
name: skill-name
description: 'Description of the skill and when to use it (10-1024 chars).'
---

# Skill Name

## Usage
When to use this skill...

## Protocol
Step-by-step instructions...

## Examples
Concrete usage examples...

## Bundled Assets (optional)
List of templates, scripts, or data files...
```

### 4. Add Bundled Assets (optional)

**Templates** (`.github/skills/<skill-name>/templates/`):
- Markdown templates for document generation
- Configuration file templates
- Code scaffolding templates

**Scripts** (`.github/skills/<skill-name>/scripts/`):
- Helper Python scripts
- Shell scripts for automation

**Data** (`.github/skills/<skill-name>/data/`):
- Reference JSON/YAML files
- Lookup tables
- Example datasets

### 5. Register in Documentation

Update `documents/skills/README.md`:

```markdown
| **new-skill** | [.github/skills/new-skill/](../../.github/skills/new-skill/SKILL.md) | Description |
```

### 6. Validate Skill

Checklist:
- [ ] YAML frontmatter is valid
- [ ] `name` field matches folder name
- [ ] `description` is 10-1024 characters
- [ ] Usage section explains when to use
- [ ] Protocol section has step-by-step instructions
- [ ] All bundled assets are referenced in SKILL.md

## Skill Template

```yaml
---
name: my-skill
description: 'Brief description of what the skill does and when it should be used.'
---

# My Skill

## Usage

Use this skill when:
- Condition 1
- Condition 2

## Prerequisites

Before using this skill:
1. Prerequisite 1
2. Prerequisite 2

## Protocol

### Step 1: [Action Name]

Description of the step...

### Step 2: [Action Name]

Description of the step...

## Examples

### Example 1: [Scenario]

```
Input: ...
Action: ...
Output: ...
```

## Bundled Assets

| Asset | Location | Description |
| :--- | :--- | :--- |
| Template | `templates/example.md` | Example template |

## Related Skills

- [skill-name](../skill-name/SKILL.md) - Related skill
```

## Converting External Documentation to Skills

Based on [Skill Seekers](../../resource/Skill_Seekers/README.md) methodology:

### 1. Identify Source

- Documentation websites
- GitHub repositories
- PDF files

### 2. Extract Key Information

- API usage patterns
- Best practices
- Common workflows
- Code examples

### 3. Structure as Skill

- **Usage**: When to apply this knowledge
- **Protocol**: Step-by-step procedures
- **Examples**: Concrete code samples
- **References**: Links to source documentation

### 4. Create Reference Files (optional)

For large skills, create reference documentation:

```
.github/skills/<skill-name>/
├── SKILL.md
├── references/
│   ├── api-reference.md
│   ├── patterns.md
│   └── examples.md
```

## Best Practices

### Writing Good Descriptions

✅ Good:
```yaml
description: 'Protocol for managing GPU jobs on SLURM clusters, including submission, monitoring, and resource optimization.'
```

❌ Bad:
```yaml
description: 'SLURM stuff'
```

### Keeping Skills Focused

- One skill = One responsibility
- Split large skills into multiple smaller ones
- Use skill references (`Related Skills`) for connections

### Maintaining Skills

- Update skills when tools or workflows change
- Keep examples current and tested
- Archive deprecated skills (don't delete)

## Transparency

```
🧠 SKILL CREATION:
- **Name**: [skill-name]
- **Purpose**: [What problem it solves]
- **Trigger Words**: [Keywords that should activate this skill]
- **Dependencies**: [Other skills or tools required]
- **Status**: [Creating/Updating/Validating]
```
