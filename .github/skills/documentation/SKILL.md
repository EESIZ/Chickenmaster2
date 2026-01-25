---
name: documentation
description: 'Standardized protocol for creating project documentation including experiment notes, technical references, and final reports. Ensures consistency and proper file placement.'
---

# Documentation Skill

## Usage

Use this skill when the user asks to "document findings", "write a report", "save a note", or when a task requires persistent recording.

## Protocol

### 1. Determine Document Type

Identify the appropriate category and path:

| Type | Path | Purpose | Language |
| :--- | :--- | :--- | :--- |
| **Exp Note** | `documents/notes/YYYY-MM-DD_<name>.md` | Daily experiment logs, quick findings | Korean |
| **Tech Note** | `documents/reference/technical/NOTE_<topic>.md` | Reusable technical knowledge, implementation details | Korean |
| **Paper Summary** | `documents/reference/papers/PAPER_<topic>.md` | Deep summary of academic papers | Korean |
| **Final Report** | `documents/final/<PHASE>_FINAL_REPORT.md` | Conclusive report for a phase | Korean |
| **Skill** | `.github/skills/<skill-name>/SKILL.md` | Reusable agent workflows | English |

### 2. Select Template

- **Tech Note**: Create `documents/reference/technical/NOTE_<topic>.md`. If you want a starting structure, use the archived template at `documents/archive/templates/TEMPLATE_NOTE.md`.
- **Exp Note**: Use the standard format (Goal, Setup, Results, Conclusion).
- **Paper**: Use the standard format (Summary, Key Points, Code).

### 3. Drafting Rules

1. **Language**:
   - **Narrative/Explanation**: Korean (for readability).
   - **Code/Config/Specs**: English (for precision).
2. **Self-Containment**: The document must be understandable without external context.
3. **Cross-Linking**: Always link to related files (e.g., `See [documents/PROJECT.md]`).
4. **Tags**: Add metadata tags for easier searching.

### 4. Verification

- Check if the file already exists to avoid accidental overwrites (append or versioning).
- Ensure all code snippets are valid.

### 5. Agentic Document Workflow (Recommended)

Use this when you want documents to be consistently reusable and easy to maintain.

1. **Define the doc contract**:
   - Target audience and scope
   - Required sections (template)
   - Acceptance criteria (what must be true when done)
2. **Collect evidence first**:
   - Prefer primary sources (official docs, papers, logs, code)
   - Record URLs and repo pointers (paths, commands)
3. **Draft structured output**:
   - Write the narrative in Korean
   - Keep code/config/spec snippets in English
   - Use short, stable headings and consistent terminology
4. **Validate**:
   - Links resolve, file paths exist
   - No accidental overwrite (append/version if needed)
   - Avoid embedding long raw logs/papers (summarize and point to sources)
5. **Index and cross-link**:
   - Add the new doc to the nearest folder README/INDEX
   - Link from related docs (PROJECT/notes/reference) when applicable

## Transparency & Thinking

```
🧠 THINKING:
- **Doc Type**: [Tech Note/Exp Note/Report]
- **Target Path**: [Path]
- **Reasoning**: [Why this location?]
- **Template**: [Which template to use?]
```
