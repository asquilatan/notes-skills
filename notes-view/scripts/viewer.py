#!/usr/bin/env python3
"""Serve a directory of Markdown notes as a mobile-friendly web reader.

Usage:
    python viewer.py --directory ./notes
    python viewer.py --directory ./notes --port 8080

The server binds to 0.0.0.0 by default so other devices on the same
network can open the printed URL. It uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import socket
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

MARKDOWN_SUFFIXES = {".md", ".markdown"}
IGNORED_DIRS = {"node_modules", "__pycache__", "venv"}

HTML_PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1e1e1e" media="(prefers-color-scheme: dark)">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%237c3aed'/%3E%3Cpath d='M9 10h14M9 16h14M9 22h9' stroke='white' stroke-width='2.5' stroke-linecap='round'/%3E%3C/svg%3E">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css"
  integrity="sha384-nB0miv6/jRmo5UMMR1wu3Gz6NLsoTkbqJghGIsx//Rlm+ZU03BU6SQNC66uf4l5+" crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/lib/marked.umd.js"
  integrity="sha384-1k2MTWjtw1PI6EOZEAvwL3bDoJfybbsEJcaXqsRTurALpMRRfQwza/nvaUQ7S/CQ" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"
  integrity="sha384-7zkQWkzuo3B5mTepMUcHkMB5jZaolc2xDwL6VFqjFALcbeS9Ggm/Yr2r3Dy4lfFg" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  integrity="sha384-43gviWU0YVjaDtb/GhzOouOXtZMP/7XUzwPTstBeZFe/+rCMvRwr4yROQP43s0Xk" crossorigin="anonymous"></script>
<style>
  * { box-sizing: border-box; }
  :root {
    color-scheme: light dark;
    --bg: #ffffff;
    --bg-elevated: rgba(255, 255, 255, 0.88);
    --fg: #24292f;
    --muted: #6b7280;
    --border: #e6e8eb;
    --surface: #f6f7f9;
    --surface-strong: #eceef2;
    --accent: #7c3aed;
    --active-bg: rgba(124, 58, 237, 0.12);
    --code-bg: #f3f4f6;
    --code-border: #e5e7eb;
    --shadow: 0 14px 44px rgba(0, 0, 0, 0.2);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #1e1e1e;
      --bg-elevated: rgba(30, 30, 30, 0.88);
      --fg: #dfdfdf;
      --muted: #9a9a9a;
      --border: #343434;
      --surface: #252526;
      --surface-strong: #2e2e30;
      --accent: #a78bfa;
      --active-bg: rgba(167, 139, 250, 0.18);
      --code-bg: #262626;
      --code-border: #383838;
      --shadow: 0 14px 44px rgba(0, 0, 0, 0.55);
    }
  }
  html { -webkit-text-size-adjust: 100%; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--fg);
    font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
      "Helvetica Neue", Arial, sans-serif;
    font-size: 16px;
    line-height: 1.65;
    -webkit-font-smoothing: antialiased;
  }
  body.no-scroll { overflow: hidden; }
  button { font: inherit; color: inherit; }
  a { color: var(--accent); }

  .topbar {
    position: fixed;
    inset: 0 0 auto 0;
    z-index: 20;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: calc(7px + env(safe-area-inset-top)) 16px 7px;
    min-height: 56px;
    background: var(--bg-elevated);
    border-bottom: 1px solid var(--border);
    -webkit-backdrop-filter: blur(14px);
    backdrop-filter: blur(14px);
  }
  .titles { flex: 1; min-width: 0; display: flex; flex-direction: column; line-height: 1.25; }
  #fileTitle {
    font-size: 15px;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  #breadcrumb {
    font-size: 11.5px;
    color: var(--muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .icon-btn {
    flex: none;
    width: 42px;
    height: 42px;
    display: grid;
    place-items: center;
    border: 1px solid transparent;
    border-radius: 10px;
    background: transparent;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
  }
  .icon-btn:hover { background: var(--surface-strong); }
  .icon-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .icon-btn svg { width: 22px; height: 22px; }

  .scrim {
    position: fixed;
    inset: 0;
    z-index: 40;
    background: rgba(0, 0, 0, 0.38);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.22s ease;
  }
  .scrim.show { opacity: 1; pointer-events: auto; }

  .drawer {
    position: fixed;
    z-index: 50;
    top: 0;
    right: 0;
    bottom: 0;
    width: min(86vw, 360px);
    display: flex;
    flex-direction: column;
    padding-top: env(safe-area-inset-top);
    padding-bottom: env(safe-area-inset-bottom);
    background: var(--surface);
    border-left: 1px solid var(--border);
    box-shadow: var(--shadow);
    transform: translateX(102%);
    transition: transform 0.26s cubic-bezier(0.22, 0.8, 0.36, 1);
  }
  .drawer.open { transform: translateX(0); }
  .drawer-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 8px 8px 18px;
    border-bottom: 1px solid var(--border);
  }
  .drawer-head strong {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
  }
  .tree {
    flex: 1;
    overflow-y: auto;
    overscroll-behavior: contain;
    -webkit-overflow-scrolling: touch;
    padding: 8px 8px 24px;
  }
  .tree details { margin: 0; }
  .tree summary {
    display: flex;
    align-items: center;
    gap: 6px;
    min-height: 38px;
    padding: 6px 8px;
    border-radius: 7px;
    list-style: none;
    cursor: pointer;
    color: var(--muted);
    font-size: 13px;
    font-weight: 600;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
  }
  .tree summary::-webkit-details-marker { display: none; }
  .tree summary:hover { background: var(--surface-strong); }
  .tree .chevron {
    flex: none;
    width: 14px;
    text-align: center;
    transition: transform 0.15s ease;
  }
  .tree details[open] > summary .chevron { transform: rotate(90deg); }
  .tree .children {
    margin-left: 10px;
    padding-left: 4px;
    border-left: 1px solid var(--border);
  }
  .tree a.file {
    display: block;
    margin: 1px 0;
    padding: 7px 10px;
    border-radius: 7px;
    color: var(--fg);
    font-size: 14px;
    text-decoration: none;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    -webkit-tap-highlight-color: transparent;
  }
  .tree a.file:hover { background: var(--surface-strong); }
  .tree a.file.active { background: var(--active-bg); color: var(--accent); font-weight: 600; }

  .markdown-body {
    max-width: 780px;
    margin: 0 auto;
    padding: calc(76px + env(safe-area-inset-top)) 20px calc(80px + env(safe-area-inset-bottom));
    overflow-wrap: break-word;
  }
  .markdown-body > :first-child { margin-top: 0; }
  .markdown-body h1,
  .markdown-body h2,
  .markdown-body h3,
  .markdown-body h4,
  .markdown-body h5,
  .markdown-body h6 {
    margin: 1.6em 0 0.6em;
    line-height: 1.3;
    font-weight: 650;
  }
  .markdown-body h1 { font-size: 1.85em; letter-spacing: -0.02em; }
  .markdown-body h2 { font-size: 1.4em; }
  .markdown-body h3 { font-size: 1.17em; }
  .markdown-body h4 { font-size: 1em; }
  .markdown-body p,
  .markdown-body ul,
  .markdown-body ol,
  .markdown-body blockquote,
  .markdown-body pre,
  .markdown-body table { margin: 0 0 1em; }
  .markdown-body ul,
  .markdown-body ol { padding-left: 1.4em; }
  .markdown-body li { margin: 0.25em 0; }
  .markdown-body a { text-decoration: none; }
  .markdown-body a:hover { text-decoration: underline; }
  .markdown-body strong { font-weight: 650; }
  .markdown-body code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    font-size: 0.875em;
    background: var(--code-bg);
    border: 1px solid var(--code-border);
    border-radius: 5px;
    padding: 0.15em 0.35em;
  }
  .markdown-body pre {
    padding: 14px 16px;
    background: var(--code-bg);
    border: 1px solid var(--code-border);
    border-radius: 10px;
    overflow: auto;
    line-height: 1.55;
    tab-size: 2;
  }
  .markdown-body pre code {
    padding: 0;
    background: none;
    border: 0;
    font-size: 0.86em;
    white-space: pre;
  }
  .markdown-body blockquote {
    margin-left: 0;
    padding: 0.2em 0 0.2em 1em;
    border-left: 3px solid var(--accent);
    color: var(--muted);
  }
  .markdown-body blockquote > :last-child { margin-bottom: 0; }
  .markdown-body hr { margin: 2em 0; border: 0; border-top: 1px solid var(--border); }
  .markdown-body img { max-width: 100%; height: auto; border-radius: 8px; }
  .markdown-body table {
    display: block;
    width: 100%;
    border-collapse: collapse;
    overflow-x: auto;
    font-size: 0.94em;
  }
  .markdown-body th,
  .markdown-body td {
    padding: 8px 10px;
    border: 1px solid var(--border);
    text-align: left;
    vertical-align: top;
  }
  .markdown-body th { background: var(--surface); }
  .markdown-body input[type="checkbox"] {
    width: 1em;
    height: 1em;
    margin-right: 0.45em;
    vertical-align: -0.12em;
    accent-color: var(--accent);
  }
  .markdown-body .mermaid {
    margin: 1.2em 0;
    overflow-x: auto;
    overflow-y: hidden;
    -webkit-overflow-scrolling: touch;
    text-align: center;
  }
  .markdown-body .mermaid svg {
    display: block;
    margin: 0 auto;
    height: auto;
  }
  .mermaid-hint {
    margin: -0.6em 0 1.2em;
    color: var(--muted);
    font-size: 12px;
    text-align: center;
  }
  .markdown-body .katex {
    display: inline-block;
    max-width: 100%;
    overflow-x: auto;
    overflow-y: hidden;
    vertical-align: baseline;
    scrollbar-width: thin;
  }
  .katex-display { display: block; overflow-x: auto; overflow-y: hidden; padding: 2px 0; }
  .katex-display > .katex { display: block; max-width: none; overflow: visible; }

  .placeholder { padding: 2rem 0; color: var(--muted); font-size: 15px; }
  .placeholder pre {
    margin-top: 1rem;
    padding: 14px 16px;
    border: 1px solid var(--code-border);
    border-radius: 10px;
    background: var(--code-bg);
    white-space: pre-wrap;
    color: var(--fg);
  }

  @media (min-width: 900px) {
    .markdown-body { padding-top: calc(90px + env(safe-area-inset-top)); }
  }
</style>
</head>
<body>
<header class="topbar">
  <div class="titles">
    <div id="fileTitle">Notes</div>
    <div id="breadcrumb"></div>
  </div>
  <button id="menuBtn" class="icon-btn" type="button" aria-label="Open notes navigation"
    aria-controls="drawer" aria-expanded="false">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
      stroke-linecap="round" aria-hidden="true">
      <path d="M4 7h16M4 12h16M4 17h16"/>
    </svg>
  </button>
</header>

<main id="content" class="markdown-body" aria-busy="true">
  <div class="placeholder">Loading notes...</div>
</main>

<div id="scrim" class="scrim" aria-hidden="true"></div>

<aside id="drawer" class="drawer" aria-label="Notes navigation" aria-hidden="true">
  <div class="drawer-head">
    <strong>Notes</strong>
    <button id="closeBtn" class="icon-btn" type="button" aria-label="Close notes navigation">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
        stroke-linecap="round" aria-hidden="true">
        <path d="M6 6l12 12M18 6L6 18"/>
      </svg>
    </button>
  </div>
  <nav id="tree" class="tree"></nav>
</aside>

<script type="module">
const content = document.getElementById('content');
const treeEl = document.getElementById('tree');
const drawer = document.getElementById('drawer');
const scrim = document.getElementById('scrim');
const menuBtn = document.getElementById('menuBtn');
const closeBtn = document.getElementById('closeBtn');
const fileTitle = document.getElementById('fileTitle');
const breadcrumb = document.getElementById('breadcrumb');

const MD_RE = /\.(md|markdown)$/i;
const state = { current: null, tree: [], rootName: 'Notes' };

function encodePath(path) {
  return path.split('/').map(encodeURIComponent).join('/');
}

function dirname(path) {
  const index = path.lastIndexOf('/');
  return index === -1 ? '' : path.slice(0, index + 1);
}

function basename(path) {
  return path.slice(path.lastIndexOf('/') + 1);
}

function displayName(path) {
  return basename(path).replace(MD_RE, '');
}

function currentParam() {
  return new URLSearchParams(window.location.search).get('file');
}

function setDrawer(open) {
  drawer.classList.toggle('open', open);
  scrim.classList.toggle('show', open);
  drawer.setAttribute('aria-hidden', String(!open));
  menuBtn.setAttribute('aria-expanded', String(open));
  document.body.classList.toggle('no-scroll', open);
  if (open) {
    closeBtn.focus({ preventScroll: true });
    requestAnimationFrame(() => {
      const active = treeEl.querySelector('a.file.active');
      if (active) active.scrollIntoView({ block: 'nearest' });
    });
  } else if (drawer.contains(document.activeElement)) {
    menuBtn.focus({ preventScroll: true });
  }
}

menuBtn.addEventListener('click', () => {
  setDrawer(!drawer.classList.contains('open'));
});
closeBtn.addEventListener('click', () => setDrawer(false));
scrim.addEventListener('click', () => setDrawer(false));
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && drawer.classList.contains('open')) setDrawer(false);
});

function markActive() {
  treeEl.querySelectorAll('a.file').forEach((anchor) => {
    anchor.classList.toggle('active', anchor.dataset.path === state.current);
  });
  treeEl.querySelectorAll('details[data-path]').forEach((details) => {
    if (state.current && state.current.startsWith(details.dataset.path + '/')) {
      details.open = true;
    }
  });
}

function renderTree(nodes, container, depth) {
  for (const node of nodes) {
    if (node.type === 'dir') {
      const details = document.createElement('details');
      details.dataset.path = node.path;
      if (depth === 0 || (state.current && state.current.startsWith(node.path + '/'))) {
        details.open = true;
      }
      const summary = document.createElement('summary');
      const chevron = document.createElement('span');
      chevron.className = 'chevron';
      chevron.textContent = '\u203a';
      const label = document.createElement('span');
      label.textContent = node.name;
      summary.append(chevron, label);
      const children = document.createElement('div');
      children.className = 'children';
      renderTree(node.children, children, depth + 1);
      details.append(summary, children);
      container.append(details);
    } else {
      const anchor = document.createElement('a');
      anchor.className = 'file';
      anchor.href = '?file=' + encodeURIComponent(node.path);
      anchor.dataset.path = node.path;
      anchor.title = node.path;
      anchor.textContent = displayName(node.path);
      if (node.path === state.current) anchor.classList.add('active');
      container.append(anchor);
    }
  }
}

treeEl.addEventListener('click', (event) => {
  const anchor = event.target.closest('a.file');
  if (!anchor) return;
  event.preventDefault();
  setDrawer(false);
  navigate(anchor.dataset.path);
});

function pickDefault(nodes) {
  const files = [];
  const walk = (list) => list.forEach((node) => {
    if (node.type === 'dir') walk(node.children);
    else files.push(node);
  });
  walk(nodes);
  const preferred = ['readme.md', 'overview.md', 'index.md'];
  for (const name of preferred) {
    const match = files.find((file) => file.name.toLowerCase() === name);
    if (match) return match.path;
  }
  return files.length ? files[0].path : null;
}

async function loadTree() {
  const response = await fetch('/api/tree', { cache: 'no-store' });
  if (!response.ok) throw new Error('Could not load the notes index.');
  const data = await response.json();
  state.tree = Array.isArray(data.tree) ? data.tree : [];
  state.rootName = data.root || 'Notes';
  treeEl.textContent = '';
  if (!state.tree.length) {
    const empty = document.createElement('div');
    empty.className = 'placeholder';
    empty.textContent = 'No Markdown files found.';
    treeEl.append(empty);
    return;
  }
  renderTree(state.tree, treeEl, 0);
  markActive();
}

function resolveHref(href) {
  if (!href || /^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i.test(href)) return null;
  const base = 'http://notes.local/' + (state.current ? encodePath(dirname(state.current)) : '');
  let url;
  try {
    url = new URL(href, base);
  } catch {
    return null;
  }
  if (url.origin !== 'http://notes.local') return null;
  let path;
  try {
    path = decodeURIComponent(url.pathname.replace(/^\/+/, ''));
  } catch {
    return null;
  }
  if (!path) return null;
  return { path, hash: url.hash };
}

function rewriteLinks() {
  content.querySelectorAll('a[href]').forEach((anchor) => {
    const href = anchor.getAttribute('href');
    if (!href || href.startsWith('#')) return;
    const resolved = resolveHref(href);
    if (!resolved) return;
    if (MD_RE.test(resolved.path)) {
      anchor.dataset.note = resolved.path;
      anchor.href = '?file=' + encodeURIComponent(resolved.path) + resolved.hash;
    } else {
      anchor.href = '/files/' + encodePath(resolved.path) + resolved.hash;
    }
  });
  content.querySelectorAll('img[src], video[src], audio[src], source[src]').forEach((element) => {
    const src = element.getAttribute('src');
    if (!src || src.startsWith('data:')) return;
    const resolved = resolveHref(src);
    if (resolved) element.setAttribute('src', '/files/' + encodePath(resolved.path));
  });
}

content.addEventListener('click', (event) => {
  if (event.defaultPrevented || event.button !== 0 ||
      event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  const anchor = event.target.closest('a');
  if (!anchor || !anchor.dataset.note) return;
  event.preventDefault();
  navigate(anchor.dataset.note);
});

function prepareMermaid() {
  content.querySelectorAll('pre > code.language-mermaid, pre > code.lang-mermaid').forEach((code) => {
    const graph = code.textContent;
    const diagram = document.createElement('div');
    diagram.className = 'mermaid';
    diagram.dataset.graph = graph;
    diagram.textContent = graph;
    code.parentElement.replaceWith(diagram);
  });
  content.querySelectorAll('div.mermaid').forEach((diagram) => {
    if (!diagram.dataset.graph) diagram.dataset.graph = diagram.textContent;
  });
}

let mermaidPromise = null;

function getMermaid() {
  if (!mermaidPromise) {
    mermaidPromise = import('https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs')
      .then((module) => module.default);
  }
  return mermaidPromise;
}

async function renderMermaid() {
  const nodes = Array.from(content.querySelectorAll('.mermaid'));
  if (!nodes.length) return;
  let mermaid;
  try {
    mermaid = await getMermaid();
  } catch (error) {
    console.warn('Mermaid failed to load:', error);
    return;
  }
  const dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: dark ? 'dark' : 'default',
    fontFamily: 'ui-sans-serif, -apple-system, "Segoe UI", sans-serif',
    htmlLabels: false,
    flowchart: { useMaxWidth: false },
    sequence: { useMaxWidth: false },
  });
  try {
    await mermaid.run({ nodes, suppressErrors: true });
  } catch (error) {
    console.warn('Mermaid rendering failed:', error);
  }
  updateDiagramHints();
}

function updateDiagramHints() {
  content.querySelectorAll('.mermaid').forEach((diagram) => {
    const next = diagram.nextElementSibling;
    if (next && next.classList.contains('mermaid-hint')) next.remove();
    if (diagram.scrollWidth > diagram.clientWidth + 2) {
      const hint = document.createElement('div');
      hint.className = 'mermaid-hint';
      hint.textContent = 'Swipe to pan the diagram';
      diagram.after(hint);
    }
  });
}

function renderMath() {
  protectCurrencyDollars();
  try {
    if (!window.renderMathInElement) return;
    window.renderMathInElement(content, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '\\[', right: '\\]', display: true },
        { left: '$', right: '$', display: false },
        { left: '\\(', right: '\\)', display: false },
      ],
      throwOnError: false,
      ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'option'],
      ignoredClasses: ['mermaid'],
    });
  } catch (error) {
    console.warn('KaTeX rendering failed:', error);
  } finally {
    restoreDollarMarkers();
  }
}

const DOLLAR_MARKER = '\uE000';

function isEscaped(text, index) {
  let count = 0;
  for (let cursor = index - 1; cursor >= 0 && text[cursor] === '\\'; cursor -= 1) count += 1;
  return count % 2 === 1;
}

function looksLikeProse(value) {
  return !value.includes('\\') && /[A-Za-z]{2,}\s+[A-Za-z]{2,}/.test(value);
}

// Currency like "$3.00 CPM ... below $3.00" is otherwise paired as one math
// expression. A dollar followed by a digit cannot close math, and prose
// inside the span also disqualifies it.
function protectDollarsInText(text) {
  let output = '';
  let index = 0;
  while (index < text.length) {
    const char = text[index];
    if (char !== '$' || isEscaped(text, index)) {
      output += char;
      index += 1;
      continue;
    }
    if (text[index + 1] === '$') {
      const end = text.indexOf('$$', index + 2);
      if (end === -1) {
        output += text.slice(index);
        break;
      }
      output += text.slice(index, end + 2);
      index = end + 2;
      continue;
    }
    let close = -1;
    for (let cursor = index + 1; cursor < text.length; cursor += 1) {
      if (text[cursor] === '\\') {
        cursor += 1;
        continue;
      }
      if (text[cursor] !== '$') continue;
      if (text[cursor + 1] === '$') break;
      close = cursor;
      break;
    }
    const candidate = close === -1 ? '' : text.slice(index + 1, close);
    const valid = close !== -1
      && candidate.length > 0
      && !/^\s|\s$/.test(candidate)
      && !/^\d/.test(text[close + 1] || '')
      && !candidate.includes('\n')
      && !looksLikeProse(candidate);
    if (valid) {
      output += text.slice(index, close + 1);
      index = close + 1;
    } else {
      output += DOLLAR_MARKER;
      index += 1;
    }
  }
  return output;
}

function protectCurrencyDollars() {
  const walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue.includes('$')) return NodeFilter.FILTER_REJECT;
      const parent = node.parentElement;
      if (!parent || parent.closest('pre, code, script, style, textarea, .mermaid, .katex')) {
        return NodeFilter.FILTER_REJECT;
      }
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (const node of nodes) node.nodeValue = protectDollarsInText(node.nodeValue);
}

function restoreDollarMarkers() {
  const walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) {
    if (walker.currentNode.nodeValue.includes(DOLLAR_MARKER)) nodes.push(walker.currentNode);
  }
  for (const node of nodes) {
    node.nodeValue = node.nodeValue.split(DOLLAR_MARKER).join('$');
  }
}

function updateHeader(path) {
  const name = displayName(path);
  const folder = dirname(path).replace(/\/$/, '').split('/').filter(Boolean).join(' / ');
  fileTitle.textContent = name;
  breadcrumb.textContent = folder || state.rootName;
  document.title = name + ' \u00b7 Notes';
}

async function loadFile(path, { preserveScroll = false } = {}) {
  const scrollY = window.scrollY;
  state.current = path;
  markActive();
  content.setAttribute('aria-busy', 'true');
  if (!preserveScroll) {
    content.innerHTML = '<div class="placeholder">Loading...</div>';
    window.scrollTo(0, 0);
  }
  try {
    const response = await fetch('/api/file?path=' + encodeURIComponent(path), { cache: 'no-store' });
    const text = await response.text();
    if (!response.ok) throw new Error(text || 'Could not load this note.');
    if (!window.marked) {
      throw new Error('The Markdown renderer could not load. Check the connection and reload the page.');
    }
    content.innerHTML = window.marked.parse(text, { gfm: true, breaks: false });
    prepareMermaid();
    rewriteLinks();
    renderMath();
    await renderMermaid();
    updateHeader(path);
    if (preserveScroll) window.scrollTo(0, scrollY);
  } catch (error) {
    content.textContent = '';
    const box = document.createElement('div');
    box.className = 'placeholder';
    box.textContent = error.message || 'Could not load this note.';
    content.append(box);
    updateHeader(path);
  } finally {
    content.removeAttribute('aria-busy');
  }
}

function navigate(path) {
  if (path === state.current) return;
  window.history.pushState({ file: path }, '', '?file=' + encodeURIComponent(path));
  loadFile(path);
}

window.addEventListener('popstate', () => {
  const path = currentParam();
  if (path) {
    loadFile(path);
  } else if (state.tree.length) {
    const fallback = pickDefault(state.tree);
    if (fallback) loadFile(fallback);
  }
});

window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  content.querySelectorAll('.mermaid').forEach((diagram) => {
    if (!diagram.dataset.graph) return;
    diagram.removeAttribute('data-processed');
    diagram.textContent = diagram.dataset.graph;
  });
  renderMermaid();
});

let resizeTimer = null;
window.addEventListener('resize', () => {
  window.clearTimeout(resizeTimer);
  resizeTimer = window.setTimeout(updateDiagramHints, 150);
});

async function init() {
  try {
    await loadTree();
  } catch (error) {
    treeEl.textContent = '';
    const box = document.createElement('div');
    box.className = 'placeholder';
    box.textContent = error.message;
    treeEl.append(box);
  }
  const initial = currentParam();
  const target = initial || pickDefault(state.tree);
  if (!target) {
    if (!initial) {
      content.textContent = '';
      const box = document.createElement('div');
      box.className = 'placeholder';
      box.textContent = 'No Markdown files were found in this directory.';
      content.append(box);
      fileTitle.textContent = state.rootName;
      content.removeAttribute('aria-busy');
    }
    return;
  }
  if (!initial) {
    window.history.replaceState({ file: target }, '', '?file=' + encodeURIComponent(target));
  }
  await loadFile(target);
}

init();
</script>
</body>
</html>
"""


def natural_key(value: str) -> list:
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", value)]


def scan_tree(directory: Path, root: Path) -> list[dict]:
    directories: list[dict] = []
    files: list[dict] = []
    try:
        entries = sorted(directory.iterdir(), key=lambda entry: natural_key(entry.name))
    except OSError:
        return []

    for entry in entries:
        if entry.name.startswith(".") or entry.name in IGNORED_DIRS:
            continue
        try:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                children = scan_tree(entry, root)
                if children:
                    directories.append({
                        "type": "dir",
                        "name": entry.name,
                        "path": entry.relative_to(root).as_posix(),
                        "children": children,
                    })
            elif entry.is_file() and entry.suffix.lower() in MARKDOWN_SUFFIXES:
                files.append({
                    "type": "file",
                    "name": entry.name,
                    "path": entry.relative_to(root).as_posix(),
                })
        except OSError:
            continue

    return directories + files


def resolve_within(root: Path, raw: str) -> Path | None:
    raw = unquote(raw).replace("\\", "/")
    if "\x00" in raw:
        return None
    parts = [part for part in raw.split("/") if part not in ("", ".")]
    if not parts or any(part == ".." or part.startswith(".") for part in parts):
        return None
    target = root.joinpath(*parts).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target


class NotesRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    root: Path = Path(".").resolve()
    verbose: bool = False

    def log_message(self, fmt: str, *args) -> None:
        if self.verbose:
            super().log_message(fmt, *args)

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _send_text(self, status: HTTPStatus, message: str) -> None:
        self._send(status, message.encode("utf-8"), "text/plain; charset=utf-8")

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        route = parsed.path

        if route in ("/", "/index.html"):
            self._send(HTTPStatus.OK, HTML_PAGE.encode("utf-8"), "text/html; charset=utf-8")
            return

        if route == "/api/tree":
            self._send_json(HTTPStatus.OK, {
                "root": self.root.name or str(self.root),
                "tree": scan_tree(self.root, self.root),
            })
            return

        if route == "/api/file":
            requested = parse_qs(parsed.query).get("path", [""])[0]
            target = resolve_within(self.root, requested)
            if target is None or not target.is_file() or target.suffix.lower() not in MARKDOWN_SUFFIXES:
                self._send_text(HTTPStatus.NOT_FOUND, "Markdown file not found.")
                return
            try:
                text = target.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                self._send_text(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "File is not valid UTF-8.")
                return
            except OSError as exc:
                self._send_text(HTTPStatus.INTERNAL_SERVER_ERROR, f"Could not read file: {exc}")
                return
            self._send(HTTPStatus.OK, text.encode("utf-8"), "text/markdown; charset=utf-8")
            return

        if route.startswith("/files/"):
            target = resolve_within(self.root, route[len("/files/"):])
            if target is None or not target.is_file():
                self._send_text(HTTPStatus.NOT_FOUND, "File not found.")
                return
            content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if content_type.startswith("text/"):
                content_type += "; charset=utf-8"
            try:
                payload = target.read_bytes()
            except OSError as exc:
                self._send_text(HTTPStatus.INTERNAL_SERVER_ERROR, f"Could not read file: {exc}")
                return
            self._send(HTTPStatus.OK, payload, content_type)
            return

        if route == "/favicon.ico":
            self._send(HTTPStatus.NO_CONTENT, b"", "image/x-icon")
            return

        self._send_text(HTTPStatus.NOT_FOUND, "Not found.")


class NotesServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address) -> None:
        error = sys.exc_info()[1]
        if isinstance(error, (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


def lan_address() -> str | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Serve a Markdown notes directory to devices on your local network."
    )
    parser.add_argument(
        "--directory", "-d", default="notes",
        help="Directory containing the notes (default: ./notes)",
    )
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port to listen on (default: 8080)")
    parser.add_argument("--host", default="0.0.0.0", help="Address to bind (default: 0.0.0.0)")
    parser.add_argument("--verbose", action="store_true", help="Log every HTTP request")
    args = parser.parse_args()

    if not 0 <= args.port <= 65535:
        print("error: --port must be between 0 and 65535", file=sys.stderr)
        return 2

    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        print(f"error: directory not found: {root}", file=sys.stderr)
        return 2

    handler = type("BoundNotesHandler", (NotesRequestHandler,), {"root": root, "verbose": args.verbose})
    try:
        server = NotesServer((args.host, args.port), handler)
    except OSError as exc:
        print(f"error: could not start the server on {args.host}:{args.port} ({exc})", file=sys.stderr)
        print("Try a different port, for example: --port 8081", file=sys.stderr)
        return 1

    port = server.server_address[1]

    print()
    print("  Notes viewer")
    print(f"  Serving   {root}")
    print(f"  Local     http://localhost:{port}")
    if args.host in ("0.0.0.0", ""):
        ip = lan_address()
        if ip:
            print(f"  Network   http://{ip}:{port}")
        else:
            print("  Network   use your computer's LAN IP")
    else:
        print(f"  Network   http://{args.host}:{port}")
    print()
    print("  Open the Network URL on your phone (same Wi-Fi). Press Ctrl+C to stop.")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
