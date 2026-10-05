---
name: notes-validate-general-lessons
description: "Audits and fact-checks generated module lessons for non-code and practical craft topics (e.g. baking, concrete molding, perfumery, cooking, carpentry). Verifies factual accuracy of claims, scientific/physical mechanisms, craft realism, and safety without micromanaging numbers."
license: MIT
metadata:
  author: user
---

# Notes Validate General Lessons (Craft & Non-Code Topics)

Use this skill to audit and fact-check lesson files within non-code and practical craft modules (e.g. baking, concrete molding, perfumery, cooking, carpentry, physical crafts).

> [!CAUTION]
> **WORKSPACE PATH ENFORCEMENT (CRITICAL)**:
> This skill validates **only the target module** (e.g., `./01-module/`) inside the user's **active project workspace (Current Working Directory)**.
> **NEVER** inspect or edit files inside `~/.agents/` or `~/.gemini/`.

> [!IMPORTANT]
> **MANDATORY DISTINCT SUBAGENT ENFORCEMENT**:
> The craft/fact auditor MUST be a **completely different, freshly invoked subagent instance** from the subagent that authored the lessons.
> **NEVER** reuse the creator subagent to audit its own lessons. An independent subagent guarantees unbiased fact-checking, realistic physics verification, and safety auditing.

---

## 1. Craft Fact-Checking Workflow

```mermaid
flowchart TD
    Start["Craft Lessons Created in Module"] --> Aud["Subagent: Craft & Fact Auditor"]
    Aud --> Check{"Any Factually Inaccurate Claims or Safety Hazards?"}
    Check -- Yes --> Fix["Auto-Patch Factual Errors in Lesson Files"]
    Check -- No --> Pass["Mark Module Validated"]
    Fix --> Pass
    Pass --> Done["Module Ready for Student"]
```

### Craft & Factual Auditor Subagent
- **Role**: `Module Craft Fact Auditor`
- **Scope**: Fact-checks all claims, explanations of mechanisms, and physical behaviors in the lesson markdown files against established real-world science and artisan standards.
- **Checklist**:
  *(Note: Numbers, exact measurements, and minor computations are flexible and fine—do not waste time micromanaging them. Focus solely on whether the underlying facts and science are true.)*
  1. **Factual Accuracy of Claims**: Are the facts presented about the craft, ingredients, raw materials, and tools accurate?
  2. **Scientific & Physical Mechanism Truth**: Are explanations of *why* things happen physically or chemically true (e.g. yeast biology, cement hydration, saponification, fragrance volatility curves)?
  3. **Craft Realism & Viability**: Does the sequence of physical actions reflect genuine workshop/kitchen practice without omitting critical real-world steps?
  4. **Safety Realism**: Are safety warnings, curing hazards, or toxicity facts accurate and clearly stated where relevant?
  5. **Bidirectional Navigation Links**: Does every lesson file have the top back-link (`[← Previous: ...]`) and bottom forward-link (`[Next: ... →]`) with valid relative Markdown links forming a clean `01 <-> 02 <-> 03` chain?
  6. **Concise Filename Slugs (2–4 Words)**: Confirm that all lesson filenames adhere strictly to the **2 to 4 word limit** (excluding the `NN-` number prefix) and do not contain bloated, run-on phrases (5+ words). If a filename is bloated (e.g. `03-bulk-fermentation-and-stretch-and-fold.md`), rename it to a concise 2–4 word slug (e.g. `03-bulk-fermentation.md`) and update relative links.

---

## 2. Execution Steps

1. **Locate Target Files**:
   Scan all `.md` lesson files under the target module directory:
   `<module-dir>/01-*.md`, `<module-dir>/02-*.md`, etc. (excluding `overview.md` and `questions.md`).
2. **Invoke Craft Audit**:
   Launch the `Module Craft Fact Auditor` subagent to review the lesson files against the checklist above.
3. **Resolve Factual Inaccuracies**:
   If the auditor identifies inaccurate facts, unscientific claims, or missing safety warnings, auto-patch the affected lesson files immediately.
4. **Log Validation Summary**:
   Append a concise verification note into the root `agent_notes.md` under `## Module Progress Log`:
   ```markdown
   - **[NN-module-name]**: Validated by Module Craft Fact Auditor (real-world craft facts, mechanisms, and safety precautions confirmed). Ready for Lesson 01.
   ```
5. **Notify Orchestrator**:
   Signal to the orchestrator that validation is complete so the student can begin Lesson 01.
