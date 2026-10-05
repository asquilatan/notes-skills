---
name: notes-create-coding-lessons
description: "Generates sequenced lesson files (01-...md to 0n-...md) for programming, software engineering, and code-based modules based on overview.md. Enforces concise 2-4 word filename slugs, runnable code examples, after-code translations, zero unexplained jargon, 2-4 sentence paragraphs, and a patient 'one dev teaching another' voice."
license: MIT
metadata:
  author: user
---

# Notes Create Coding Lessons

Use this skill to generate the complete set of lesson files for code-based and software engineering modules based on `overview.md`. For non-coding crafts (e.g. cooking, baking, concrete molding), use `notes-create-general-lessons` instead.

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
     01-what-is-laravel.md           # 3 words
     02-core-library-features.md     # 3 words
     03-how-mvc-works.md             # 3 words
     04-routing-and-controllers.md   # 3 words
     03-stochastic-simulation.md     # 2 words
     04-matrix-multiplication.md     # 2 words
     04-weather-simulator.md         # 2 words
     ```
   - **Strictly Forbidden Filename Anti-Patterns**:
     - *Overkill run-on filenames (5+ words are FORBIDDEN)*: e.g. `04-multi-step-state-transitions-and-matrix-multiplication.md` (overkill; use `04-matrix-multiplication.md`), `03-algorithmic-state-sampling-and-stochastic-simulation.md` (overkill; use `03-stochastic-simulation.md`), `04-building-the-5-day-weather-simulator-and-verifying-analytical-predictions.md` (overkill; use `04-weather-simulator.md`).
     - *Vague 1-word filenames (FORBIDDEN)*: `01-intro.md` or `02-basics.md`.

2. **Standard Lesson Skeleton**:
   ```markdown
   [← Previous: 01-what-is-laravel.md](./01-what-is-laravel.md) | [Overview](./overview.md)

   # Title in Title Case

   <1-2 paragraph bridge linking from previous lesson + what this lesson covers. Direct "you" and "we" voice.>

   ## Subsection Heading

   <Plain language explanation introducing the concept. No unexplained jargon.>

   ```<language>
   // Runnable, copy-pasteable example in the current stack's language
   ```

   <Mandatory 1-2 sentence translation: "Here, we are using..." or "In this case, the...">

   <Hands-on instruction: file path to edit, command to run, and exact expected output.>

   <Variants table or bullet comparison: shortcuts vs verbose forms, edge cases.>

   <Senior dev aside: "I usually prefer...", "I just added X here so you can see...">

   <Close with forward transition paragraph: "In the next lesson, we will explore...">

   ---
   [Next: 03-mvc-how-it-works.md →](./03-mvc-how-it-works.md)
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

1. **Stance (One Dev Teaching Another)**:
   - Patient senior engineer pair-programming with a junior.
   - Relatable, encouraging, never condescending, never using phrases like `as you obviously know` or `clearly`.
2. **Zero Unexplained Jargon Rule**:
   - Never use a technical term without defining it immediately in plain English with a concrete example.
   - Example: *"A facade is a class that provides a static interface to an underlying service. In this case, the Route facade lets us register endpoints without manually instantiating the router instance."*
   - Never stack 3 or more new terms in one paragraph. Introduce one, unpack it, and anchor it before moving to the next.
3. **Paragraph Architecture**:
   - 2 to 4 sentences maximum per paragraph.
   - Blank lines separating all paragraphs.
   - Never write walls of text.
4. **Code-First & Runnable**:
   - Every hands-on lesson must include at least one complete, runnable code block.
   - Name exact relative file paths.
   - Show broken cases and fixes where educational (e.g. 404 on unconstrained route, missing imports, unhandled exceptions).
5. **Mandatory After-Code Translation**:
   - Every code block must be followed by 1-2 sentences translating what the key lines do in plain English:
     - `Here, we are defining...`
     - `In this case, the function returns...`
     - `Notice how line 4 passes...`
6. **Sentence Templates to Reuse**:
   - **Bridge**: `We touched on X in the last lesson, but now let's see how it connects to Y.`
   - **Setup**: `Open your <path> file. You should see something like...`
   - **Check-in**: `Run the following command in your terminal. You should see...`
   - **Aside**: `I prefer to use X here because...` / `I put Y here just to keep things clean.`
7. **Mermaid Diagrams**:
   - Include a Mermaid diagram (`flowchart TD` or `sequenceDiagram`) whenever an architectural flow, data lifecycle, or multi-step coordination is easier to grasp visually.
   - Keep diagrams focused (5-10 nodes max).
   - Follow every diagram with a 1-2 sentence plain-English walkthrough.

---

## 3. Mandatory Rule for Lesson 01: Background & The Problem ("Why")

The first lesson (`01-...md`) of a course or foundational module has a unique, vital responsibility: **it must gently onboard the student and ground them in the fundamental problem space before any complex mechanics are introduced.**

Never jump straight into protocol wire headers, raw byte layouts, or complex configuration in Lesson 01. Follow this 4-part arc:

1. **How the Baseline System Works**:
   - Begin with what the student already knows or can easily visualize.
   - For example, with WebSockets: explain how traditional web browsing works—you click a link, the browser sends a request, the server sends HTML back, and the connection closes (the basic Request-Response pattern).
2. **Why the Old Way Falls Short**:
   - Show exactly where and why the old way breaks down when facing modern software requirements.
   - Explain the clunky workarounds developers were forced to invent (e.g. polling the server every 2 seconds for new messages, wasting bandwidth and eating server CPU).
3. **Why the Technology Was Invented**:
   - State the core problem it solves in one crisp, memorable sentence.
   - Explain the fundamental mechanism (e.g. *"Instead of repeatedly knocking on the door to ask if there's mail, we leave a permanent tube open between the client and server so either side can slide a message through instantly"*).
4. **The Road Ahead**:
   - Conclude by previewing how the upcoming lessons will unpack the nuts and bolts of building with it.

### Heading Style Rules (Strict)
- **No Meta-Label Prefixes**: Never use meta-labels or business-pitch labels in headings:
  - ❌ `The Pain Point: ...`
  - ❌ `The Failure: ...`
  - ❌ `The Mental Shift: ...`
  - ❌ `The Status Quo: ...`
- **Use Direct, Natural Headings**: Phrase headings naturally to describe the technology, mechanism, or "why":
  - ✅ `How the Traditional Web Functions` (rather than `The Traditional Web: Request and Response`)
  - ✅ `The Inefficiency of Polling` (rather than `The Pain Point: The Inefficiency of Polling`)
  - ✅ `Why WebSockets Were Invented` (rather than `The Mental Shift: Why WebSockets Were Invented`)
  - ✅ `Mandatory Handshake Headers`
  - ✅ `Inspecting Handshake Headers in Node.js`
  - ✅ `Key Header Comparisons`

---

## 4. Step-by-Step Creation Process (Delegated Subagent)

1. Read the target module's `overview.md` to identify the full list of planned lessons.
2. Verify the project stack, runtime versions, and file structure.
3. Generate each lesson file in sequence from `01-...md` to `0N-...md`.
4. Ensure bidirectional navigation links are intact (`01 <-> 02 <-> 03...`) with top back-links and bottom forward-links using valid relative file paths.
5. Ensure lesson files contain **pure lesson content** (all quizzes, doubts, and check-ins belong exclusively in `questions.md`).
6. Once written, invoke `notes-validate-coding-lessons` to audit the module before user study begins.

