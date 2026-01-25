---
name: deep-research
description: 'Comprehensive research workflow that performs iterative, deep analysis using multiple sources, verification, and synthesis. Ideal for technical reports, literature review, and complex problem exploration.'
---

# Deep Research Skill

## Usage

Use this skill when the user asks for "deep research", "comprehensive report", or "detailed analysis" of a complex topic.

## Protocol

### Phase 1: Outline & Perspective Planning

1. **Analyze the Request**: Identify key entities and constraints.
2. **Draft Outline**: Create a hierarchical Table of Contents (ToC) for the final report.
3. **Select Perspectives**: Choose 2-3 lenses (e.g., Security, Performance, Cost) to analyze the topic.
4. **Set Parameters**: Define **Breadth** (topics) and **Depth** (recursion limit).

### Phase 2: Recursive Execution (The Loop)

For each section of the Outline:

1. **Search**: Execute search queries using the priority strategy (Tavily/VS Code first).
2. **Adversarial Search**: Search for "limitations", "failures", and "alternatives" (The Skeptic).
3. **Filter**: Discard low-quality/AI-generated sources.
4. **Acquire**:
   - **ArXiv**: Use `arxiv-mcp-server`.
   - **Other PDFs**: Use `wget` to download to `temp/` and read manually.
5. **Read & Analyze**: Extract "Learnings" to fill the Outline.
6. **Evaluate & Recurse**:
   - If information is missing, generate **Follow-up Questions**.
   - Repeat the search process for these new questions (up to Depth limit).
7. **Verify (Optional)**:
   - If technical details are ambiguous, write a **standalone test script** in `temp/`.
   - Run the script to confirm behavior (e.g., API compatibility).
   - *Constraint*: Do NOT modify project source code.

### Phase 3: Synthesis & Reporting

1. **Structure**: Use the drafted Outline as the skeleton.
2. **Draft**: Write the content in the requested language (English for code, Korean for reports).
3. **Cite**: Provide links/references for all claims.
4. **Crystallize**: If the topic is fully solved/established, propose creating a new Skill file.

## Transparency & Thinking

You must display your thinking process:

```
🧠 THINKING:
- Current Depth: [1/3]
- Perspective: [e.g., Security]
- Question: [Current sub-question]
- Findings: [What has been found so far?]
- Missing: [What is still unknown?]
- Next Action: [Search/Download/Test/Synthesize]
```
