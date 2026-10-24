const content = document.getElementById('content');
const treeEl = document.getElementById('tree');
const drawer = document.getElementById('drawer');
const scrim = document.getElementById('scrim');
const menuBtn = document.getElementById('menuBtn');
const closeBtn = document.getElementById('closeBtn');
const fileTitle = document.getElementById('fileTitle');
const breadcrumb = document.getElementById('breadcrumb');
const toast = document.getElementById('toast');

const MD_RE = /\.(md|markdown)$/i;
const ANSWER_TOKEN = '___';
const state = { current: null, tree: [], rootName: 'Notes', writable: new Set(), fingerprint: '' };

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
  state.writable = new Set(
    (Array.isArray(data.writable) ? data.writable : []).map((name) => String(name).toLowerCase())
  );
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

function fnv1a(text) {
  let hash = 2166136261;
  for (const byte of new TextEncoder().encode(text)) {
    hash ^= byte;
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return hash.toString(16).padStart(8, '0');
}

function isWritable(path) {
  return Boolean(path) && state.writable.has(basename(path).toLowerCase());
}

let toastTimer = null;
function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle('error', Boolean(isError));
  toast.classList.add('show');
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove('show'), isError ? 3600 : 1400);
}

async function submitAnswer(payload) {
  if (!state.current) throw new Error('Open a note first.');
  const response = await fetch('/api/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: state.current, source: state.fingerprint, ...payload }),
  });
  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }
  if (!response.ok) throw new Error((data && data.error) || 'Could not save the answer.');
  if (data && typeof data.source === 'string') state.fingerprint = data.source;
  showToast('Saved');
  return data;
}

function blankPositions(text) {
  const positions = [];
  let index = text.indexOf(ANSWER_TOKEN);
  while (index !== -1) {
    const before = index > 0 ? text[index - 1] : '';
    const after = text[index + ANSWER_TOKEN.length] || '';
    if (before !== '_' && after !== '_') positions.push(index);
    index = text.indexOf(ANSWER_TOKEN, index + ANSWER_TOKEN.length);
  }
  return positions;
}

function prepareCheckboxes() {
  let ordinal = 0;
  content.querySelectorAll('input[type="checkbox"]').forEach((box) => {
    box.disabled = false;
    box.dataset.checkboxIndex = String(ordinal);
    ordinal += 1;
  });
}

function prepareBlanks() {
  const walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue.includes(ANSWER_TOKEN)) return NodeFilter.FILTER_REJECT;
      const parent = node.parentElement;
      if (parent && parent.closest('pre, code, .blank-input, .blank-filled')) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);

  let ordinal = 0;
  for (const node of nodes) {
    const positions = blankPositions(node.nodeValue);
    if (!positions.length) continue;
    const fragment = document.createDocumentFragment();
    let cursor = 0;
    for (const position of positions) {
      if (position > cursor) fragment.append(node.nodeValue.slice(cursor, position));
      const slot = document.createElement('button');
      slot.type = 'button';
      slot.className = 'blank-slot';
      slot.dataset.blankIndex = String(ordinal);
      slot.setAttribute('aria-label', 'Fill in the blank');
      slot.textContent = ANSWER_TOKEN;
      fragment.append(slot);
      ordinal += 1;
      cursor = position + ANSWER_TOKEN.length;
    }
    if (cursor < node.nodeValue.length) fragment.append(node.nodeValue.slice(cursor));
    node.replaceWith(fragment);
  }
}

function prepareAnswers(path) {
  if (!isWritable(path)) return;
  prepareCheckboxes();
  prepareBlanks();
}

function renumberBlanks(filledIndex) {
  content.querySelectorAll('button.blank-slot').forEach((slot) => {
    const current = Number(slot.dataset.blankIndex);
    if (current > filledIndex) slot.dataset.blankIndex = String(current - 1);
  });
}

function startBlankEdit(slot) {
  if (slot.dataset.editing === '1') return;
  slot.dataset.editing = '1';

  const input = document.createElement('input');
  input.type = 'text';
  input.className = 'blank-input';
  input.autocomplete = 'off';
  input.placeholder = 'answer';
  input.enterKeyHint = 'done';
  input.setAttribute('aria-label', 'Your answer');
  slot.replaceWith(input);
  input.focus({ preventScroll: true });

  let settled = false;
  const restore = () => {
    if (settled) return;
    settled = true;
    input.replaceWith(slot);
    delete slot.dataset.editing;
  };

  const commit = async () => {
    if (settled) return;
    const value = input.value.trim();
    if (!value) {
      restore();
      return;
    }
    if (value.includes(ANSWER_TOKEN) || /[\r\n]/.test(value)) {
      showToast('Keep the answer on one line, without ___ inside it.', true);
      input.focus();
      return;
    }
    settled = true;
    input.disabled = true;
    const index = Number(slot.dataset.blankIndex);
    try {
      await submitAnswer({ kind: 'blank', index, value });
      const filled = document.createElement('span');
      filled.className = 'blank-filled';
      filled.textContent = value;
      input.replaceWith(filled);
      renumberBlanks(index);
    } catch (error) {
      settled = false;
      input.disabled = false;
      showToast(error.message, true);
      input.focus();
    }
  };

  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      commit();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      restore();
    }
  });
  input.addEventListener('blur', () => {
    if (!settled) commit();
  });
}

content.addEventListener('click', (event) => {
  const slot = event.target.closest('button.blank-slot');
  if (!slot) return;
  event.preventDefault();
  startBlankEdit(slot);
});

content.addEventListener('change', async (event) => {
  const box = event.target;
  if (!(box instanceof HTMLInputElement) || box.type !== 'checkbox') return;
  if (!box.dataset.checkboxIndex || !isWritable(state.current)) return;
  const desired = box.checked;
  box.disabled = true;
  try {
    await submitAnswer({ kind: 'checkbox', index: Number(box.dataset.checkboxIndex), checked: desired });
  } catch (error) {
    box.checked = !desired;
    showToast(error.message, true);
  } finally {
    box.disabled = false;
  }
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
    state.fingerprint = fnv1a(text);
    prepareAnswers(path);
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
