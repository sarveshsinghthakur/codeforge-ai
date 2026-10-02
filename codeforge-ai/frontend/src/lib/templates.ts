/**
 * Predefined code template engine.
 *
 * Splits a problem's starter code into a locked header (class + function
 * signature), an editable coding block (the function body) and a locked
 * footer (closing braces). The editor only ever shows the coding block, so
 * the user never has to write boilerplate — it is re-attached automatically
 * before the code is sent to the judge.
 */

export type TemplateMode = 'body' | 'full';

export interface TemplateInfo {
  mode: TemplateMode;
  /** Locked boilerplate shown above the editor (class + signature line). */
  header: string;
  /** Default content of the coding block (dedented, ready to edit). */
  body: string;
  /** Locked boilerplate shown below the editor (closing braces), may be ''. */
  footer: string;
  /** Indentation re-applied to every body line when the full code is built. */
  baseIndent: string;
  language: string;
  /** Human readable reason when the template falls back to full editing. */
  note?: string;
}

const INDENT = '    ';

function lineIndent(line: string): number {
  const m = line.match(/^[ \t]*/);
  return m ? m[0].replace(/\t/g, INDENT).length : 0;
}

function indentOf(line: string): string {
  const m = line.match(/^[ \t]*/);
  return m ? m[0] : '';
}

function dedent(lines: string[]): { lines: string[]; indent: string } {
  const nonBlank = lines.filter(l => l.trim() !== '');
  if (nonBlank.length === 0) return { lines: [], indent: '' };
  let common = indentOf(nonBlank[0]);
  for (const line of nonBlank) {
    const ind = indentOf(line);
    let i = 0;
    while (i < common.length && i < ind.length && common[i] === ind[i]) i++;
    common = common.slice(0, i);
  }
  return {
    lines: lines.map(l => (l.trim() === '' ? '' : l.slice(common.length))),
    indent: common,
  };
}

function fallback(language: string, reason: string): TemplateInfo {
  return { mode: 'full', header: '', body: '', footer: '', baseIndent: '', language, note: reason };
}

// ── Python ────────────────────────────────────────────────────────────────
function analyzePython(code: string): TemplateInfo {
  const lines = code.replace(/\r\n/g, '\n').split('\n');
  // Prefer `class Solution`; helper classes (ListNode/TreeNode) often come first.
  let classIdx = lines.findIndex(l => /^class\s+Solution\b/.test(l));
  if (classIdx === -1) {
    const classes = lines.map((l, i) => (/^class\s+\w+/.test(l) ? i : -1)).filter(i => i >= 0);
    if (classes.length > 1) {
      // several top-level classes and no Solution -> whole file is editable
      return { mode: 'full', header: '', body: code, footer: '', baseIndent: '', language: 'python' };
    }
    classIdx = classes.length === 1 ? classes[0] : -1;
  }
  let defIdx = -1;
  for (let i = classIdx + 1; i < lines.length; i++) {
    if (/^\s*def\s+\w+\s*\(/.test(lines[i])) {
      defIdx = i;
      break;
    }
  }
  if (defIdx === -1 && classIdx === -1) {
    // module-level function template
    defIdx = lines.findIndex(l => /^def\s+\w+\s*\(/.test(l));
  }
  if (defIdx === -1) return fallback('python', 'Could not find the solution function in the template');

  const defIndent = lineIndent(lines[defIdx]);
  // multiple methods on the same level -> the whole class is the coding area
  for (let i = defIdx + 1; i < lines.length; i++) {
    if (/^\s*def\s+\w+\s*\(/.test(lines[i]) && lineIndent(lines[i]) === defIndent) {
      return { mode: 'full', header: '', body: code, footer: '', baseIndent: '', language: 'python' };
    }
  }

  const header = lines.slice(0, defIdx + 1).join('\n');
  const bodyLines: string[] = [];
  for (let i = defIdx + 1; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim() !== '' && lineIndent(line) <= defIndent) break;
    bodyLines.push(line);
  }
  while (bodyLines.length && bodyLines[bodyLines.length - 1].trim() === '') bodyLines.pop();
  const { lines: dedented, indent } = dedent(bodyLines);
  return {
    mode: 'body',
    header,
    body: dedented.join('\n'),
    footer: '',
    baseIndent: indent || INDENT.repeat(lineIndent(lines[defIdx]) / INDENT.length + 1),
    language: 'python',
  };
}

// ── brace languages (javascript / typescript / java / cpp / c) ───────────
interface Scan {
  open: number; // index of the brace that starts the coding block
  close: number; // index of the brace that ends it
  depthTransitions: number; // how many times depth went from 1 -> 2
}

function scanBraces(code: string): Scan | null {
  let depth = 0;
  let maxDepth = 0;
  let firstDepth2Open = -1;
  let firstDepth2Close = -1;
  let transitions = 0;
  let quote = '';
  for (let i = 0; i < code.length; i++) {
    const ch = code[i];
    if (quote) {
      if (ch === '\\') { i++; continue; }
      if (ch === quote) quote = '';
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') { quote = ch; continue; }
    if (ch === '/' && code[i + 1] === '/') {
      const nl = code.indexOf('\n', i);
      i = nl === -1 ? code.length : nl;
      continue;
    }
    if (ch === '{') {
      depth++;
      if (depth === 2) {
        transitions++;
        if (firstDepth2Open === -1) firstDepth2Open = i;
      }
      if (depth > maxDepth) maxDepth = depth;
    } else if (ch === '}') {
      if (depth === 2 && firstDepth2Open !== -1 && firstDepth2Close === -1) {
        firstDepth2Close = i;
      }
      depth--;
    }
  }
  if (maxDepth === 0) return null;
  if (maxDepth === 1) {
    // single top-level block: the whole block is the coding area
    let open = code.indexOf('{');
    let depth2 = 0;
    let close = -1;
    quote = '';
    for (let i = open; i < code.length; i++) {
      const ch = code[i];
      if (quote) {
        if (ch === '\\') { i++; continue; }
        if (ch === quote) quote = '';
        continue;
      }
      if (ch === '"' || ch === "'" || ch === '`') { quote = ch; continue; }
      if (ch === '{') depth2++;
      else if (ch === '}') {
        depth2--;
        if (depth2 === 0) { close = i; break; }
      }
    }
    if (open === -1 || close === -1) return null;
    return { open, close, depthTransitions: 1 };
  }
  if (firstDepth2Open === -1 || firstDepth2Close === -1) return null;
  return { open: firstDepth2Open, close: firstDepth2Close, depthTransitions: transitions };
}

function countTopLevelFunctions(code: string, language: string): number {
  if (language === 'java') {
    // constructors + methods: "public Foo(...)" / "private int bar(...)" followed by {
    return (code.match(/^\s*(public|private|protected)\s+[\w<>\[\]]+\s+\w+\s*\([^;]*\)\s*\{/gm) || []).length;
  }
  const fn = code.match(/(\bfunction\s*\(|=\s*function\b|function\s+\w+\s*\()/g) || [];
  return fn.length;
}

function analyzeBraced(code: string, language: string): TemplateInfo {
  if (countTopLevelFunctions(code, language) > 1) {
    return { mode: 'full', header: '', body: code, footer: '', baseIndent: '', language };
  }
  const scan = scanBraces(code);
  if (!scan) return fallback(language, 'Could not find the function body in the template');
  if (scan.depthTransitions > 1) {
    // several methods/constructors -> the whole class is the coding area
    return { mode: 'full', header: '', body: code, footer: '', baseIndent: '', language };
  }

  const header = code.slice(0, scan.open + 1);
  // start the footer at the closing brace's line so its indentation survives
  const closeLineStart = code.lastIndexOf('\n', scan.close) + 1;
  const footer = code.slice(closeLineStart);
  const interior = code.slice(scan.open + 1, closeLineStart);
  const interiorLines = interior.replace(/\r\n/g, '\n').split('\n');
  const { lines: dedented, indent } = dedent(interiorLines);
  while (dedented.length && dedented[dedented.length - 1].trim() === '') dedented.pop();
  while (dedented.length && dedented[0].trim() === '') dedented.shift();

  const openLine = code.slice(0, scan.open).split('\n').pop() || '';
  const baseIndent = indent || indentOf(openLine) + INDENT;
  return {
    mode: 'body',
    header: header.replace(/\s+$/, ''),
    body: dedented.join('\n'),
    footer: footer.replace(/^\s+$/, ''),
    baseIndent,
    language,
  };
}

// ── public API ────────────────────────────────────────────────────────────
export function analyzeTemplate(code: string, language: string): TemplateInfo {
  const raw = (code || '').replace(/\r\n/g, '\n').trimEnd();
  if (!raw.trim()) return fallback(language, 'No predefined template for this language');
  if (language === 'python') return analyzePython(raw);
  return analyzeBraced(raw, language);
}

/** Re-attach the locked boilerplate around an edited coding block. */
export function assembleCode(info: TemplateInfo | null, body: string): string {
  if (!info || info.mode === 'full') return body;
  let clean = body.replace(/\r\n/g, '\n').replace(/\n+$/, '');
  if (info.language === 'python' && clean.trim() === '') clean = 'pass';
  const indented = clean
    .split('\n')
    .map(l => (l.trim() === '' ? '' : info.baseIndent + l))
    .join('\n');
  const parts = [info.header.replace(/\s+$/, ''), indented];
  if (info.footer) parts.push(info.footer.replace(/^\s+$/, ''));
  return parts.join('\n') + '\n';
}

/**
 * Recover the coding block from a stored draft. Older drafts contain the
 * full template (header included); newer drafts only contain the body.
 */
export function extractDraftBody(draft: string, info: TemplateInfo): string {
  if (!draft) return info.body;
  if (info.mode === 'full') return draft;
  const signature = info.header.split('\n').filter(l => l.trim()).pop();
  if (signature && draft.includes(signature)) {
    const analyzed = analyzeTemplate(draft, info.language);
    if (analyzed.mode === 'body') return analyzed.body;
  }
  return draft;
}

/** Small inline lock icon used by the template strips. */
export const LOCK_SVG =
  '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>';
