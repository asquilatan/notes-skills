# notes-skills

My collection of skills for learning and note-taking with AI agents

```mermaid
graph TD
    Start["notes-start"]
    Outline["notes-create-outline"]
    Quiz["notes-conduct-quiz"]
    Ask["notes-ask"]
    CodingLessons["notes-create-coding-lessons"]
    GeneralLessons["notes-create-general-lessons"]
    ValidateCode["notes-validate-coding-lessons"]
    ValidateGeneral["notes-validate-general-lessons"]

    Start --> Outline
    Start --> Quiz
    Start --> Ask
    Start --> CodingLessons
    Start --> GeneralLessons
    CodingLessons --> ValidateCode
    GeneralLessons --> ValidateGeneral
```

### Skills

- **[`notes-start`](./notes-start/)**: This skill orchestrates the learning flow, runs the diagnostic questions, and coordinates the other skills.
- **[`notes-create-outline`](./notes-create-outline/)**: This skill generates and updates outlines (`notes.md` and `overview.md`) with Mermaid diagrams and progress tracking.
- **[`notes-conduct-quiz`](./notes-conduct-quiz/)**: This skill conducts diagnostics, check-in quizzes, and review questions.
- **[`notes-ask`](./notes-ask/)**: This skill answers mid-lesson questions and logs them to `questions.md`.
- **[`notes-create-coding-lessons`](./notes-create-coding-lessons/)**: This skill generates coding lessons with runnable examples and explanations.
- **[`notes-create-general-lessons`](./notes-create-general-lessons/)**: This skill generates lessons for non-coding and practical craft topics.
- **[`notes-validate-coding-lessons`](./notes-validate-coding-lessons/)**: This skill checks coding lessons for syntax errors and API accuracy.
- **[`notes-validate-general-lessons`](./notes-validate-general-lessons/)**: This skill checks non-coding lessons for factual accuracy and realism.

## Installation

Run the interactive installer using `npx`:

```bash
npx github:asquilatan/notes-skills
```

It will ask whether you want to install the skills in your current repo (`.agent/skills`) or globally (`~/.gemini/config/skills`).

### Usage

Once installed, ask your agent:

```text
Teach me [topic]
```

or:

```text
/learn [topic]
```
