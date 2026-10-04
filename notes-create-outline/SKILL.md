---
name: notes-create-outline
description: "Creates and updates course-level and module-level outlines (notes.md and overview.md). Generates Mermaid dependency graphs with visual progress nodes, concise summaries, numbered module/lesson lists with descriptive phrases, and tracks current learning position."
license: MIT
metadata:
  author: user
---

# Notes Create Outline

Use this skill to establish the structure, dependency graphs, and tracking files for an entire course or an individual module.

> [!CAUTION]
> **WORKSPACE PATH ENFORCEMENT (CRITICAL)**:
> All course and module directories (e.g., `./notes/`, `./01-module-name/`) MUST be created inside the user's **active project workspace (Current Working Directory)**.
> **NEVER** create folders or files inside `~/.agents/`, `~/.gemini/`, or inside the skill's own installation directory.

Every learning unit requires two sibling files:
1. `notes.md`: Contains curated executive summaries, technical references, and conceptual synthesis (per-lesson check-ins, student doubts, and Hydra drills are stored directly in `questions.md`).
2. `overview.md`: The roadmap containing a high-level summary, a Mermaid dependency graph showing progression and current position, and a numbered breakdown.

---

## 1. Graph Topology Rules: True DAGs vs. Anti-Patterns

### Rule A: Ban the "Linked List" Anti-Pattern
Never chain modules or lessons linearly (`A --> B --> C --> D --> E`) unless every single step has an inescapable, direct prerequisite dependency on the immediately preceding one. Sequential linked lists are lazy curriculum design.

### Rule B: Ban the "Starburst" Anti-Pattern
Never create an artificial fan-out and fan-in graph where node 1 points to 4 disconnected leaves, and all 4 blindly converge into the final node without intermediate interactions.

### Rule C: Enforce Authentic Semantic Dependency Pathways (DAGs)
A true Directed Acyclic Graph (DAG) maps real-world dependencies:
1. **Foundations**: Establish shared root primitives.
2. **Parallel Specialized Branches**: Once foundations are met, independent concerns branch into concurrent tracks.
3. **Natural Synthesis Milestones**: Branches cross-pollinate and merge only when an application feature or system integration requires both prerequisites.
4. **Capstone Convergence**: Advanced performance, production hardening, or full-stack integration synthesize the complete graph.

---

## 2. Source Material Authority: PPT / Syllabus Rule

1. **User-Provided Syllabus / Slides / PPTs**:
   - If the user provides lecture slides, presentation outlines, or a curriculum document, the orchestrator **must adhere 100% strictly** to that exact structure.
   - Do not invent artificial re-partitioning, do not collapse modules, and do not split topics unless explicitly instructed.
2. **Scratch Generation**:
   - If generating an outline from a raw topic prompt, calibrate the intended dimension (Breadth Survey vs. Vertical Deep Dive).

---

## 3. Scope Calibration: Breadth vs. Depth & Length Tiers

Module count alone does not dictate depth, but it dictates the scope and pacing of the curriculum:
* **Vertical Deep Dive**: Laser-focused on low-level framework/engine/physics/spec internals, compiler mechanics, threat models/attack surfaces, wire layouts, or kernel socket buffers.
* **Horizontal Breadth Survey**: Broad architectural coverage across paradigms, weapon classes, technologies, trade-offs, and multi-system integration.
* **The Grounding Rule for Deep Dives**: When introducing physiological, cognitive, or low-level engineering topics, they must immediately tie to a tangible in-game or system reality (e.g. why staring at crosshairs causes you to miss heads; why JSON cannot serialize Symbols).

### Post-Diagnostic Course Length Tiers
After the diagnostic test pinpoints the student's frontier, the curriculum length tier determines the module budget:
* **Short (1–3 modules)**: Quick targeted sprint focusing strictly on the immediate frontier and core essentials. Even in a 3-module course, branch independent concepts (e.g. `M01 --> M02 & M03`) rather than defaulting to a linear chain.
* **Average (4–8 modules)**: Standard comprehensive curriculum covering core architecture, practical workflows, and real-world patterns.
* **Long (9+ modules)**: Deep, exhaustive masterclass covering low-level internals, edge cases, security, and production scale.
* **Unforced Natural Sizing**: Within the selected tier, let the natural complexity of the topic determine the exact count (e.g. a 5-module or 7-module course in the Average tier). Never pad with artificial fluff to hit a round number.

---

## 4. Course-Level Outline

When creating the root course structure (e.g. in `notes/` or `<output-dir>/`):

### Directory Layout
```
notes/
  notes.md          # Course-level technical notes, root architecture, reflections log
  overview.md       # Course summary, true DAG module dependency graph, module descriptions
```

### Course `overview.md` Template (True Branching DAG)
```markdown
# [Course Title]

[A single concise paragraph summarizing what we will tackle across this course, why it matters, and the final capability you will possess.]

## Dependency Graph

```mermaid
graph TD
    classDef done fill:#2e7d32,stroke:#1b5e20,color:#ffffff;
    classDef current fill:#0277bd,stroke:#01579b,color:#ffffff,stroke-width:3px;
    classDef pending fill:#424242,stroke:#212121,color:#ffffff;

    M01["01: Primitives & Foundations (Current)"]:::current --> M02["02: Reactive State Engine"]:::pending
    M01 --> M04["04: Spatial & Component Architecture"]:::pending
    
    M02 --> M03["03: External Sync & Side Effects"]:::pending
    M02 --> M05["05: Data Mutations & Form Actions"]:::pending
    M04 --> M05
    
    M03 --> M06["06: Full-Stack Integration & Production Scale"]:::pending
    M05 --> M06
```

**Current Position**: `Primitives & Foundations` (`01-primitives-and-foundations/`) - In Progress

## Modules Breakdown

1. **Primitives & Foundations** (`01-primitives-and-foundations/`) - [1-3 sentences describing the topic, what it tackles, and what it includes.]
2. **Reactive State Engine** (`02-reactive-state-engine/`) - [1-3 sentences describing the topic, what it tackles, and what it includes.]
3. **External Sync & Side Effects** (`03-external-sync-and-side-effects/`) - [1-3 sentences describing the topic, what it tackles, and what it includes.]
4. **Spatial & Component Architecture** (`04-spatial-and-component-architecture/`) - [1-3 sentences describing the topic, what it tackles, and what it includes.]
5. **Data Mutations & Form Actions** (`05-data-mutations-and-form-actions/`) - [1-3 sentences describing the topic, what it tackles, and what it includes.]
6. **Full-Stack Integration & Production Scale** (`06-full-stack-integration-and-production-scale/`) - [1-3 sentences describing the topic, what it tackles, and what it includes.]
```

---

## 5. Module-Level Outline

When creating a specific module folder (e.g. `01-module-name/`):

### Directory Layout
```
01-module-name/
  overview.md       # Module roadmap, lesson DAG dependency graph, lesson descriptions
  notes.md          # Curated module synthesis: Why -> Topic -> Diagram -> Summary (ZERO quiz clutter)
  questions.md      # All Q&A and quizzes: Student doubts, check-ins with codeblocks, Hydra drills, and re-quizzes
  01-descriptive-phrase-topic.md
  02-descriptive-phrase-topic.md
  ...
```

### Module `notes.md` Template (Curated Synthesis)

> [!IMPORTANT]
> **ZERO QUIZ CLUTTER IN `notes.md`**:
> `notes.md` contains NO quiz questions or test results. All assessments live in `questions.md`.
> `notes.md` is strictly the **Curated Executive Summary / Technical Reference** for the module, structured as:
> `Why` -> `Topic` -> `Diagram (if needed)` -> `Summary` -> `Topic` -> `Diagram (if needed)` -> `Summary`...

```markdown
# Module [NN]: [Module Name] - Technical Notes

## Why [Topic/Technology] Exists
[Continuous explanation of the fundamental problem space, what traditional systems lacked, why workarounds failed, and why this technology or craft was created.]

## [First Major Topic Title]
```mermaid
[Mermaid sequence/flowchart/architecture diagram if visual flow aids understanding]
```
[Concise, continuous summary paragraph(s) explaining the mechanism, moving parts, and engineering impact.]

## [Second Major Topic Title]
```mermaid
[Mermaid diagram if needed]
```
[Concise summary paragraph(s) explaining the topic.]

*(Continues iteratively for all core topics in the module)*
```

### Module `overview.md` Template (Branching Lesson DAG)
```markdown
# [Module Name]

[A single concise paragraph explaining the concrete goals of this module, the practical skill you are developing, and how the lessons fit together.]

## Lesson Dependency Graph

```mermaid
graph TD
    classDef done fill:#2e7d32,stroke:#1b5e20,color:#ffffff;
    classDef current fill:#0277bd,stroke:#01579b,color:#ffffff,stroke-width:3px;
    classDef pending fill:#424242,stroke:#212121,color:#ffffff;

    L01["01: Anatomy of Core Primitives (Current)"]:::current --> L02["02: Protocol Challenge Derivation"]:::pending
    L01 --> L03["03: Negotiation & Subprotocol Handlers"]:::pending
    L02 --> L04["04: Stream Detachment & Error Rejections"]:::pending
    L03 --> L04
```

**Current Position**: `Anatomy of Core Primitives` (`01-anatomy-of-core-primitives.md`) - Ready to start

## Lessons Breakdown

1. **Anatomy of Core Primitives** (`01-anatomy-of-core-primitives.md`) - [1-3 sentences describing the topic, what it tackles, and what it includes.]
2. **Protocol Challenge Derivation** (`02-protocol-challenge-derivation.md`) - [1-3 sentences describing the topic, what it tackles, and what it includes.]
3. **Negotiation & Subprotocol Handlers** (`03-negotiation-and-subprotocol-handlers.md`) - [1-3 sentences describing the topic, what it tackles, and what it includes.]
4. **Stream Detachment & Error Rejections** (`04-stream-detachment-and-error-rejections.md`) - [1-3 sentences describing the topic, what it tackles, and what it includes.]
```

---

## 6. Rules & Guidelines for Outlines

1. **Human-Readable Diagram Nodes (Strict)**:
   - All Mermaid graph node labels MUST be human-readable Title Case names (e.g. `01: Primitives & Foundations (Current)`).
   - **NEVER** put raw kebab-case filenames (like `01-primitives-and-foundations`) inside the Mermaid graph nodes.
2. **File and Folder Naming Rule**:
   - The actual folder and file names on disk are derived directly from the Title Case node title by:
     - Lowercasing and converting spaces to hyphens (`kebab-case`).
     - Prepending the zero-padded index number (e.g., `01-primitives-and-foundations/` or `01-anatomy-of-core-primitives.md`).
3. **Node Description Format in Breakdowns**:
   - Numbered list item: `1. **Title Case Name** (`NN-kebab-phrase/` or `NN-kebab-phrase.md`) - 1 to 3 sentences describing the topic, what it tackles, and what it includes.`
4. **Updating the Dependency Graph**:
   - As the user completes lessons and modules, update the Mermaid classes in `overview.md`:
     - `:::done` for finished modules/lessons (Green).
     - `:::current` for the active module/lesson (Blue).
     - `:::pending` for upcoming modules/lessons (Grey).
   - Update the **Current Position** text explicitly so the harness and user always know where they are.
