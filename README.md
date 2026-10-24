# notes-skills

My collection of skills for learning and note-taking with AI agents

```mermaid
graph TD
    Start["notes-start"]
    Continue["notes-continue"]
    Outline["notes-create-outline"]
    Quiz["notes-conduct-quiz"]
    Ask["notes-ask"]
    Practice["notes-practice"]
    CodingLessons["notes-create-coding-lessons"]
    GeneralLessons["notes-create-general-lessons"]
    ValidateCode["notes-validate-coding-lessons"]
    ValidateGeneral["notes-validate-general-lessons"]
    HouseRules["notes-validate-house-rules"]

    Start --> Continue
    Continue --> Outline
    Start --> Outline
    Start --> Quiz
    Start --> Ask
    Start --> Practice
    Start --> CodingLessons
    Start --> GeneralLessons
    CodingLessons --> ValidateCode
    GeneralLessons --> ValidateGeneral
    ValidateCode --> HouseRules
    ValidateGeneral --> HouseRules
```

### Skills

- **[`notes-start`](./notes-start/)**: This skill orchestrates the learning flow, runs the initial grill (capturing topic, scope, and quiz delivery preferences), initializes `agent_notes.md` for context-less agent handoffs, and coordinates all sub-skills.
- **[`notes-continue`](./notes-continue/)**: This skill rehydrates a new or context-less agent from on-disk course state, summarizes the current position and open struggles, and asks one confirmation before resuming.
- **[`notes-view`](./notes-view/)**: This skill serves a phone-friendly Markdown viewer for the notes over the local network, with Mermaid and LaTeX rendering, system dark/light mode, and a right-side navigation drawer. It also lets the learner answer quiz and practice questions from the phone by ticking `- [ ]` checkboxes or filling `___` blanks in `questions.md` and other files passed with `--writable`.
- **[`notes-create-outline`](./notes-create-outline/)**: This skill generates root `agent_notes.md` (settings, preferences, struggle tracker) and true DAG `overview.md` roadmaps. Modules contain `overview.md` and `questions.md` (no module `notes.md`).
- **[`notes-conduct-quiz`](./notes-conduct-quiz/)**: This skill conducts diagnostics, check-in quizzes, and reviews via the built-in question tool (`ask_question`) or token-saving Markdown checkboxes (`- [ ]`), logging struggle points to `agent_notes.md`.
- **[`notes-ask`](./notes-ask/)**: This skill answers mid-lesson questions, generates Mermaid diagrams, logs Q&As to `questions.md`, and notes learner friction in `agent_notes.md`.
- **[`notes-practice`](./notes-practice/)**: This skill conducts dedicated, low-risk sandbox practice sessions (MCQs, identification, bug hunts, real-file code writing) persisted to `practice.md` across Fixed, Unlimited, and Dynamic modes.
- **[`notes-create-coding-lessons`](./notes-create-coding-lessons/)**: This skill generates coding lessons with runnable examples and explanations.
- **[`notes-create-general-lessons`](./notes-create-general-lessons/)**: This skill generates lessons for non-coding and practical craft topics.
- **[`notes-validate-coding-lessons`](./notes-validate-coding-lessons/)**: This skill checks coding lessons for syntax errors and API accuracy.
- **[`notes-validate-general-lessons`](./notes-validate-general-lessons/)**: This skill checks non-coding lessons for factual accuracy and realism.
- **[`notes-validate-house-rules`](./notes-validate-house-rules/)**: This skill audits voice, banned AI-isms, paragraph limits, jargon discipline, filenames, navigation, and content purity, then auto-patches editorial violations.

## Installation & Management

Run the interactive CLI using `npx`:

```bash
npx --allow-git=all github:asquilatan/notes-skills
```

*(Note: npm 11+ disables git packages by default. Run `npm config set allow-git all` once to use plain `npx github:...` without the flag).*

It will ask whether you want to **install**, **update**, or **remove** skills, and whether to target your current repo (`.agents/skills`) or globally (`~/.agents/skills`).

You can also use flags directly:

```bash
# Install
npx github:asquilatan/notes-skills --repo      # Local repo
npx github:asquilatan/notes-skills --global    # Global

# Update (overwrites installed skills with latest version)
npx github:asquilatan/notes-skills --update --repo
npx github:asquilatan/notes-skills --update --global

# Remove
npx github:asquilatan/notes-skills --remove --repo
npx github:asquilatan/notes-skills --remove --global
```

### Usage

Start a topic by running:

```text
/notes-start [topic]
```

or simply:

```text
Teach me [topic]
```

For a quick, low-scaffolding session with no modules or course files:

```text
Teach me [topic] ad-hoc - no full course
```

To resume an existing course in a fresh session or with a different agent:

```text
/notes-continue
```

To read your notes on a phone or another device on the same network:

```bash
python notes-view/scripts/viewer.py --directory ./notes --writable practice.md
```

Open the printed **Network** URL on the other device (default port `8080`). In `questions.md` and the extra `--writable` files, you can tick `- [ ]` options and fill `___` blanks right from the phone; the answers are written back into the Markdown file.

### Flow

1. **Initial Grill**: The agent asks questions one at a time to establish your goals, target scope (deep dive vs. breadth), and preferred question delivery format (built-in question tool vs. token-saving `- [ ]` markdown checkboxes). It saves these settings to root `agent_notes.md` so any new agent can pick up your exact preferences without prior context.
2. **Diagnostic Quiz**: It runs a quick adaptive diagnostic to determine your baseline knowledge frontier.
3. **Curriculum Outline**: It generates `overview.md` with a true DAG dependency graph and sets up module directories (`overview.md` + `questions.md`; no module `notes.md`).
4. **Lesson Generation & Validation**: The orchestrator delegates drafting to a dedicated creator subagent, invokes a **completely separate subagent** for technical or factual validation, then invokes a **third independent subagent** to audit voice and house rules before logging verification status to `agent_notes.md`.
5. **Check-ins & Progression**: You read each lesson and take check-ins via your preferred mode (built-in question tool or checking `- [x]` in `questions.md`). Any missed questions activate remediation drills and log struggle points in `agent_notes.md` to ensure mastery before advancing.
