---
name: notes-continue
description: "Rehydrates a fresh or context-less agent from on-disk course state. Reads root agent_notes.md, overview.md, the active module overview, and recent questions/practice activity, then reports a compact status brief and asks one confirmation before continuing the lesson flow."
license: MIT
metadata:
  author: user
---

# Notes Continue - Context Rehydration for New Agents

Use this skill at the start of a session when a new agent (or a cleared conversation) needs to pick up an existing course without prior chat history. It reconstructs state from files, not from memory, and hands control back to the learner with a single confirmation.

> [!CAUTION]
> **WORKSPACE PATH ENFORCEMENT (CRITICAL)**:
> Read only from the learner's **active project workspace (Current Working Directory)**.
> **NEVER** read or write inside `~/.agents/`, `~/.gemini/`, or the skill's own installation directory.

> [!IMPORTANT]
> **READ BEFORE SPEAKING**:
> Do not ask the learner what they are studying, what their preferences are, or where they left off. All of that lives on disk. Read first, summarize, then ask at most one confirmation question.

---

## 1. Locate the Course Root

Search in this order and stop at the first match:

1. `./notes/` (the default course root).
2. A directory passed explicitly by the user.
3. `./Learning/<topic>/` if the workspace uses that layout.
4. A shallow search for `agent_notes.md` or `overview.md` (depth 2-3) when the layout is unknown.

If no course files exist, say so in one sentence and route to `notes-start`. Do not invent a workspace.

---

## 2. Read in This Order

1. **Root `agent_notes.md`**: preferences, question delivery mode, course length tier, baseline frontier, narrative motif, learner struggle points, module progress log.
2. **Root `overview.md`**: course title, current position, module graph and statuses.
3. **Active module `overview.md`**: lesson graph, current lesson, supplementary lessons.
4. **Tail of the active `questions.md`**: the last check-in, any missed items, and whether remediation is still open.
5. **Tail of `practice.md`** (if present): last practice batch and any unresolved feedback.
6. **Active lesson file** (optional): only to confirm what the learner is currently reading.

---

## 3. Produce the Status Brief (Max ~15 Lines)

Report exactly what the files say. Use this shape:

```markdown
**Course**: [Title] - [short outcome]
**Preferences**: [delivery mode] | [scope/depth] | [motif or None]
**Position**: [NN-module / NN-lesson] - [status]
**Open struggles**: [latest unresolved items, or "None recorded"]
**Last activity**: [most recent quiz/practice result and date]
**Next action**: [read current lesson / take check-in / remediation drill / module re-quiz]
```

Do not add speculation, praise, or a recap of the entire course. If any field is missing from disk, write `not recorded` rather than guessing.

---

## 4. Ask One Confirmation, Then Resume

Ask a single question with clear options:

> *"You're at [current position] in [course title]. Should I continue from there, re-explain the current lesson, or switch to a different module?"*

- **Continue**: resume the standard `notes-start` flow at the current position.
- **Re-explain**: use `notes-ask` for the current lesson, then continue.
- **Switch**: confirm the target module, update `overview.md` and `agent_notes.md`, then resume.
- **Finish / wrap up**: summarize outstanding work and stop.

Never re-run the initial grill. Only ask about settings that are genuinely absent from `agent_notes.md`.

---

## 5. Write-Back Rules

- Do not modify course files merely to "rehydrate."
- If the learner confirms a position change, update `overview.md` statuses and the `agent_notes.md` module progress log through `notes-create-outline`.
- If the learner reports a new preference, append it to `agent_notes.md` under `Learning Preferences & Settings` before proceeding.

---

## 6. Failure Modes

| Situation | Response |
| :--- | :--- |
| `agent_notes.md` exists but is empty or malformed | Say so, reconstruct what is possible from `overview.md`, and ask the learner only for the missing preferences. |
| `overview.md` exists without `agent_notes.md` | Report the roadmap position, note that preferences are missing, and offer to initialize `agent_notes.md`. |
| Files reference lessons that do not exist | List the missing files, do not fabricate them, and offer to regenerate the module through `notes-create-*`. |
| Multiple course roots found | List them and ask which course to resume. Do not merge them. |
