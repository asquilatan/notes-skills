---
name: notes-view
description: "Starts a phone-friendly Markdown viewer for a notes directory over the local network. Renders Mermaid diagrams and LaTeX, follows the system dark/light theme, provides a right-side navigation drawer, and saves answers by ticking `- [ ]` checkboxes or filling `___` blanks in `questions.md` and other files passed with `--writable`. Use when the user wants to read notes on their phone or another device, browse a course directory in a browser, answer quiz or practice questions from the phone, or start the notes viewer/server."
license: MIT
metadata:
  author: user
---

# Notes View - LAN Markdown Reader

Use this skill when the learner wants to read the course notes on a phone, tablet, or another computer on the same network. The skill starts a small Python server that renders the notes directory as a browsable Markdown site.

> [!IMPORTANT]
> The viewer is **read-only except for answers**. The only writes it can make are `- [ ]` ↔ `- [x]` toggles and `___` blank fills inside allowlisted files: `questions.md` plus any filenames passed with `--writable`. It never creates, moves, deletes, or rewrites any other part of a note.

---

## 1. Locate the Notes Directory

Resolve the target directory in this order:

1. A path the user passed explicitly.
2. `./notes/` in the active workspace.
3. A shallow search for `overview.md` or `agent_notes.md` (depth 2-3).

Verify the directory exists and contains at least one `.md` file. If it does not, say so in one sentence and stop; do not create a directory or fabricate notes.

---

## 2. Start the Server

The script is in this skill's `scripts/` directory. Always launch it with an explicit directory and keep it running in the background (the process blocks).

```bash
python3 "<skill-dir>/scripts/viewer.py" --directory "<notes-dir>" --port 8080
```

- On Windows use `python`; on macOS/Linux use `python3`, falling back to `python` if needed.
- The script uses only the Python standard library. Do not install dependencies.
- Page assets ship in the skill's `static/` directory (`index.html`, `styles.css`, `app.js`) and are read per request. Edit them and refresh the browser; no build step and no server restart.
- It binds to `0.0.0.0` by default so other devices can connect.
- `questions.md` is always writable from the browser. Add `--writable practice.md` (one or more plain filenames) when the learner also wants to answer `practice.md`, or any other file that contains `- [ ]` options or `___` blanks. Paths are rejected; write access is matched by filename in any subdirectory.
- The startup banner prints an `Answers` line listing the writable filenames. Report it so the learner knows which files accept answers.
- If port `8080` is busy, retry with `--port 8081` and report the port actually used.
- If the server is already running for this directory (check `curl -fsS http://127.0.0.1:8080/api/tree`), reuse it instead of starting a second instance.

---

## 3. Report the Access URLs

Read the server's startup output and give the learner:

- **Network URL** (the one they open on their phone), for example `http://192.168.1.20:8080`.
- **Local URL**, for testing on the same machine.

Tell them the phone must be on the same Wi-Fi/LAN. On the first run, Windows Firewall may ask for permission; allow access on **private networks** only.

---

## 4. Verify Before Reporting Success

Confirm the server responds:

```bash
curl -fsS http://127.0.0.1:8080/api/tree
```

The response must be JSON containing a `tree` array and a `writable` array. If the array is empty, the directory has no Markdown files and the user will see an empty page; report that instead of a working viewer.

Do not open a browser window unless the user asks.

---

## 5. Stop or Restart

When asked to stop, terminate the background process. Restarting is only needed after changing the script or port; note edits and new files appear on a normal browser refresh because the page reloads the tree and file on every load.

---

## 6. Answering Questions from the Phone

In writable files the page turns into an answer sheet, so the learner can complete quizzes and practice rounds without a code editor:

- Every `- [ ]` / `- [x]` task checkbox becomes tappable. Tapping saves the toggle immediately.
- Every `___` on a line becomes a focusable slot. Tapping opens a small input; `Enter` or tapping away saves, `Escape` cancels.
- A short toast confirms each save. A failed save reverts the control and shows the error.
- Only the checkbox bracket or the `___` token is replaced. The rest of the file, including line endings, is byte-identical.
- The page refuses to save if the file changed after it was loaded; the learner just reloads and taps again.

After the learner answers, read the writable file to grade or evaluate, exactly as the quiz and practice skills already instruct. Do not treat a saved answer as graded.

---

## Viewer Features

- System light/dark theme via `prefers-color-scheme`, including Mermaid theme switching.
- Hamburger button at the top right opens a right-side drawer with the full directory tree.
- GFM Markdown, tables, task lists, relative links between notes, and local images/assets.
- Tappable checkboxes and `___` blank slots in writable files, saved straight to the Markdown file.
- Mermaid diagrams from fenced `mermaid` code blocks.
- LaTeX via KaTeX for `$...$`, `$$...$$`, `\(...\)`, and `\[...\]`.
- Auto-opens `README.md`, then `overview.md`, then the first note when no file is selected.

The browser needs internet access to load the pinned CDN assets (marked, KaTeX, Mermaid). If diagrams or math stay unrendered, check the CDN connection.

---

## Boundaries

- The server exposes **every readable file under the selected directory**, including images, to anyone who can reach the machine on the network. Warn the learner if that directory contains secrets or private data.
- The answer endpoint has **no authentication**, so anyone on the same network can open the page and toggle checkboxes or fill blanks in writable files. Keep it on trusted networks only.
- Never bind publicly, port-forward, or place this behind a public tunnel.
- Keep the write scope narrow: only checkboxes and `___` blanks in `questions.md` and any `--writable` files. No creating, renaming, deleting, or free-form editing of notes, and no changes to course flow.
