---
name: notes-create-general-lessons
description: "Generates sequenced lesson files (01-...md to 0n-...md) for non-code and real-world topics (e.g. baking, cooking, concrete molding, perfumery, honey making, carpentry). Enforces concise 2-4 word filename slugs, structured execution protocols, sensory verification checks, broken cases & recoveries, and a patient 'senior artisan teaching an apprentice' voice."
license: MIT
metadata:
  author: user
---

# Notes Create General Lessons (Non-Code / Practical Crafts)

Use this skill to generate the complete set of lesson files for non-coding modules—such as baking, concrete molding, perfumery, honey making, cooking, carpentry, mechanics, or physical sciences.

> [!CAUTION]
> **WORKSPACE PATH ENFORCEMENT (CRITICAL)**:
> All lesson files MUST be created inside the target module folder located within the user's **active project workspace (Current Working Directory)** (e.g., `./01-module-name/`).
> **NEVER** write or create folders inside `~/.agents/`, `~/.gemini/`, or inside the skill's own installation directory.

---

## 1. File Naming & Structure

1. **Concise Phrase Filename Naming (Strict 2–4 Word Limit)**:
   - Filenames on disk MUST use zero-padded numbers and concise kebab-case slugs strictly capped at **2 to 4 words** (excluding the numeric prefix).
   - *Internal Title vs. Filename*: While the `# Lesson Heading` inside the file, the Mermaid node title, and the overview breakdown can be full, descriptive, and comprehensive, the **filename itself must be punchy and trimmed to the core 2–4 words**.
   - **Allowed Filename Examples (2–4 words)**:
     ```
     01-why-sourdough-works.md       # 3 words
     02-flour-and-hydration.md       # 3 words
     03-bulk-fermentation.md         # 2 words
     04-proofing-and-baking.md       # 3 words
     ```
   - **Strictly Forbidden Filename Anti-Patterns**:
     - *Overkill run-on filenames (5+ words are FORBIDDEN)*: e.g. `03-bulk-fermentation-and-stretch-and-fold.md` (overkill; use `03-bulk-fermentation.md`), `04-shaping-banneton-proofing-and-baking.md` (overkill; use `04-proofing-and-baking.md`), `02-flour-hydration-and-gluten-networks.md` (overkill; use `02-flour-and-hydration.md`).
     - *Vague 1-word filenames (FORBIDDEN)*: `01-intro.md` or `02-basics.md`.

2. **Standard Non-Code Lesson Skeleton**:
   ```markdown
   [← Previous: 01-why-sourdough-fermentation-works.md](./01-why-sourdough-fermentation-works.md) | [Overview](./overview.md)

   # Title in Title Case

   <1-2 paragraph bridge linking from previous lesson + what this lesson covers. Direct "you" and "we" voice.>

   ## Subsection Heading

   <Plain-language explanation of the physical/chemical mechanism. No unexplained jargon.>

   ### Equipment & Materials / Mise en Place
   - Item 1: Exact measurement, temperature, or tool specification
   - Item 2: Specific material grade or container type

   ### The Protocol / Action Steps
   1. Step 1: Concrete physical action with exact timing or heat level.
   2. Step 2: Clear physical manipulation.

   ### Sensory Check (What to Look, Smell, Hear, or Feel For)
   <Direct description of sensory indicators: e.g. "The mixture should look opaque and glossy, smelling faintly of toasted hazelnuts. If it smells acrid or separates into a clear puddle, the heat was too high.">

   ### The Broken Case & Recovery
   <The most common physical failure state + exact recovery action: "If the emulsion splits: remove from heat and whisk in 1 teaspoon of cold water.">

   <Senior artisan aside: "I usually prefer...", "I always let the mold sit for...">

   <Close with forward transition paragraph: "In the next lesson, we will explore...">

   ---
   [Next: 03-bulk-fermentation-and-stretch-and-fold.md →](./03-bulk-fermentation-and-stretch-and-fold.md)
   ```

3. **Bidirectional Lesson Navigation (`<->`) (Mandatory Default)**:
   Every lesson file MUST include top and bottom relative markdown links creating a seamless navigation chain:
   - **Top Back-Link (Header)**:
     - Placed at the very top of the markdown file (Line 1).
     - **Lesson 01**: `[← Back to Overview](./overview.md)`
     - **Lesson 02 onward**: `[← Previous: NN-previous-lesson.md](./NN-previous-lesson.md) | [Overview](./overview.md)`
   - **Bottom Forward-Link (Footer)**:
     - Placed at the very end of the file following a horizontal rule (`---`).
     - **Lesson 01 to (N-1)**: `[Next: NN-next-lesson.md →](./NN-next-lesson.md)`
     - **Final Lesson (N)**: `[Next: Module Overview & Quizzes →](./overview.md)`


---

## 2. Voice & House Style Rules (Strict)

1. **Stance (Senior Artisan Teaching an Apprentice)**:
   - Patient master showing an apprentice the craft in the workshop/kitchen.
   - Relatable, encouraging, never condescending, never using phrases like `as you obviously know` or `clearly`.
2. **Zero Unexplained Jargon Rule**:
   - Never use technical or trade jargon without defining it immediately in plain English with a concrete example.
   - Example: *"Hydrophilic means water-loving. In perfumery, these compounds bind easily with moisture, which dictates how quickly they evaporate off the skin."*
   - Never stack 3 or more new terms in one paragraph. Introduce one, unpack it, and anchor it before moving to the next.
3. **Paragraph Architecture**:
   - 2 to 4 sentences maximum per paragraph.
   - Blank lines separating all paragraphs. Never write walls of text.
4. **Concrete & Actionable**:
   - Every lesson must include a structured **Protocol / Action Steps** block with exact quantities, temperatures, or ratios.
   - Every protocol must have a **Sensory Check** so the learner knows whether they performed the step correctly in the real world.
5. **Sentence Templates to Reuse**:
   - **Bridge**: `We talked about X in the last lesson, but now let's see what happens when we introduce Y.`
   - **Setup**: `Gather your materials. You'll want...` / `Make sure your work surface is...`
   - **Check-in**: `Touch the surface gently. It should feel...` / `Observe the liquid carefully: you should see tiny bubbles forming along the rim.`
   - **Aside**: `I usually prefer to use X here because...` / `I always keep a damp towel nearby to...`
6. **Mermaid Diagrams**:
   - Include a Mermaid diagram (`flowchart TD`, `flowchart LR`, or `sequenceDiagram`) whenever a process workflow, chemical/physical transformation, or timing sequence benefits from visual clarity.
   - Keep diagrams focused (5-10 nodes max).
   - Follow every diagram with a 1-2 sentence plain-English walkthrough.

---

## 3. Mandatory Rule for Lesson 01: Background & The Problem ("Why")

The first lesson (`01-...md`) of a course or foundational module has a unique, vital responsibility: **it must gently onboard the student and ground them in the fundamental problem space before any complex techniques are introduced.**

Never jump straight into complex chemistry, exact industrial ratios, or niche tools in Lesson 01. Follow this 4-part arc:

1. **How the Baseline System / Natural State Works**:
   - Begin with what the student already knows or can easily visualize (e.g. in baking: flour, water, and heat make flat hardtack; in perfumery: raw flowers smell good but fade in 10 minutes).
2. **Why the Primitive Way Falls Short**:
   - Show where the simple approach fails (e.g. hardtack is dense and inedible; raw floral water turns sour and oxidizes quickly).
3. **Why the Craft / Technique Was Invented**:
   - Introduce the breakthrough technique or foundational science that solved the problem.
   - State the core mechanism in one crisp sentence.
4. **The Road Ahead**:
   - Preview how the upcoming lessons will take you from raw materials to a finished, repeatable product.

### Heading Style Rules (Strict)
- **No Meta-Label Prefixes**: Never use meta-labels or business-pitch labels in headings:
  - ❌ `The Pain Point: ...`
  - ❌ `The Failure: ...`
  - ❌ `The Mental Shift: ...`
  - ❌ `The Status Quo: ...`
- **Use Direct, Natural Headings**: Phrase headings naturally to describe the craft, material, or "why":
  - ✅ `How Primitive Dough Reacts to Heat`
  - ✅ `The Limitations of Natural Extraction`
  - ✅ `Why Fermentation Transforms Bread`
  - ✅ `Controlling the Hydration Ratio`
  - ✅ `Monitoring the Setting Reaction in Concrete`

---

## 4. Step-by-Step Creation Process (Delegated Subagent)

1. Read the target module's `overview.md` to identify the full list of planned lessons.
2. Confirm the craft's required tools, safety considerations, and materials.
3. Generate each lesson file in sequence from `01-...md` to `0N-...md`.
4. Ensure bidirectional navigation links are intact (`01 <-> 02 <-> 03...`) with top back-links and bottom forward-links using valid relative file paths.
5. Ensure lesson files contain **pure lesson content** (all quizzes, doubts, and check-ins belong exclusively in `questions.md`).
6. Once written, invoke `notes-validate-general-lessons` to audit the module before user study begins.

