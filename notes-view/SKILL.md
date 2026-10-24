---
name: notes-view
description: "Starts a read-only, phone-friendly Markdown viewer for a notes directory over the local network. Renders Mermaid diagrams and LaTeX, follows the system dark/light theme, and provides a right-side navigation drawer. Use when the user wants to read notes on their phone or another device, browse a course directory in a browser, or start the notes viewer/server."
license: MIT
metadata:
  author: user
---

# Notes View - LAN Markdown Reader

Use this skill when the learner wants to read the course notes on a phone, tablet, or another computer on the same network. The skill starts a small Python server that renders the notes directory as a browsable Markdown site.

> [!IMPORTANT]
> This is a **read-only viewer**. Never edit, move, or delete note files as part of this skill.

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
- It binds to `0.0.0.0` by default so other devices can connect.
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

The response must be JSON containing a `tree` array. If the array is empty, the directory has no Markdown files and the user will see an empty page; report that instead of a working viewer.

Do not open a browser window unless the user asks.

---

## 5. Stop or Restart

When asked to stop, terminate the background process. Restarting is only needed after changing the script or port; note edits and new files appear on a normal browser refresh because the page reloads the tree and file on every load.

---

## Viewer Features

- System light/dark theme via `prefers-color-scheme`, including Mermaid theme switching.
- Hamburger button at the top right opens a right-side drawer with the full directory tree.
- GFM Markdown, tables, task lists, relative links between notes, and local images/assets.
- Mermaid diagrams from fenced `mermaid` code blocks.
- LaTeX via KaTeX for `$...$`, `$$...$$`, `\(...\)`, and `\[...\]`.
- Auto-opens `README.md`, then `overview.md`, then the first note when no file is selected.

The browser needs internet access to load the pinned CDN assets (marked, KaTeX, Mermaid). If diagrams or math stay unrendered, check the CDN connection.

---

## Boundaries

- The server exposes **every readable file under the selected directory**, including images, to anyone who can reach the machine on the network. Warn the learner if that directory contains secrets or private data.
- Never bind publicly, port-forward, or place this behind a public tunnel.
- Keep the read-only stance: no note writes, no course-flow changes, no quiz state changes.
