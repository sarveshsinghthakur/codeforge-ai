// Isolated Node runner — executes one test case.
// Usage: node runner_node.mjs <job.json>
import fs from "node:fs";
import vm from "node:vm";

const job = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

function ListNode(val, next) {
  this.val = val === undefined ? 0 : val;
  this.next = next === undefined ? null : next;
}

function TreeNode(val, left, right) {
  this.val = val === undefined ? 0 : val;
  this.left = left === undefined ? null : left;
  this.right = right === undefined ? null : right;
}

function buildList(values, pos) {
  if (!values || values.length === 0) return null;
  const nodes = values.map((v) => new ListNode(v));
  for (let i = 0; i < nodes.length - 1; i++) nodes[i].next = nodes[i + 1];
  if (Number.isInteger(pos) && pos >= 0 && pos < nodes.length) {
    nodes[nodes.length - 1].next = nodes[pos];
  }
  return nodes[0];
}

function buildTree(values) {
  if (!values || values.length === 0 || values[0] === null) return null;
  const root = new TreeNode(values[0]);
  const queue = [root];
  let i = 1;
  while (queue.length && i < values.length) {
    const node = queue.shift();
    if (i < values.length) {
      const v = values[i++];
      if (v !== null && v !== undefined) {
        node.left = new TreeNode(v);
        queue.push(node.left);
      }
    }
    if (i < values.length) {
      const v = values[i++];
      if (v !== null && v !== undefined) {
        node.right = new TreeNode(v);
        queue.push(node.right);
      }
    }
  }
  return root;
}

function paramNames(fn) {
  try {
    const src = Function.prototype.toString.call(fn);
    const m = src.match(/function[^(]*\(([^)]*)\)|\(([^)]*)\)\s*=>|([A-Za-z_$][\w$]*)\s*=>/);
    const raw = m ? (m[1] ?? m[2] ?? m[3] ?? "") : "";
    return raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  } catch {
    return [];
  }
}

function nodeKind(value) {
  if (value === null || typeof value !== "object") return null;
  if (value.next !== undefined && value.val !== undefined) return "list";
  if (value.left !== undefined && value.val !== undefined) return "tree";
  return null;
}

function serializeListNode(head) {
  const vals = [];
  const seen = new Set();
  let cur = head;
  while (cur !== null && cur !== undefined && !seen.has(cur)) {
    seen.add(cur);
    vals.push(cur.val);
    cur = cur.next;
  }
  return JSON.stringify(vals);
}

function serializeTreeNode(root) {
  if (!root) return "[]";
  const out = [];
  const queue = [root];
  while (queue.length) {
    const n = queue.shift();
    if (n === null || n === undefined) {
      out.push(null);
      continue;
    }
    out.push(n.val);
    queue.push(n.left === undefined ? null : n.left);
    queue.push(n.right === undefined ? null : n.right);
  }
  while (out.length && out[out.length - 1] === null) out.pop();
  return JSON.stringify(out);
}

function resultAlternates(value) {
  const kind = nodeKind(value);
  if (kind === "list") {
    const parts = [];
    const seen = new Set();
    let cur = value;
    while (cur !== null && cur !== undefined && !seen.has(cur)) {
      seen.add(cur);
      parts.push(String(cur.val));
      cur = cur.next;
    }
    const alts = [parts.join("->")];
    if (parts.length) alts.push(parts[0]);
    return alts;
  }
  if (kind === "tree") {
    const alts = [serializeTreeNode(value)];
    if (value !== null && value !== undefined && value.val !== undefined && value.val !== null) {
      alts.push(String(value.val));
    }
    return alts;
  }
  return [];
}

function formatResult(value) {
  if (value === undefined || value === null) return "";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return String(value);
  if (typeof value === "string") return value;
  const kind = nodeKind(value);
  if (kind === "list") return serializeListNode(value);
  if (kind === "tree") return String(value.val);
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function tryDesignRun(job, sandbox) {
  const args = job.args || [];
  if (args.length !== 2) return null;
  const [ops, opargs] = args;
  if (!Array.isArray(ops) || !ops.length || !ops.every((o) => typeof o === "string")) return null;
  if (!Array.isArray(opargs) || !opargs.length || !opargs.every((a) => Array.isArray(a))) return null;
  const Ctor = sandbox[ops[0]];
  if (typeof Ctor !== "function") return null;
  const obj = new Ctor(...opargs[0]);
  const out = [null];
  for (let i = 1; i < ops.length && i < opargs.length; i++) {
    const ret = typeof obj[ops[i]] === "function" ? obj[ops[i]](...opargs[i]) : undefined;
    out.push(ret === undefined ? null : ret);
  }
  return out;
}

function buildCallArgs(names, positional, kwargs, pos) {
  const rest = { ...kwargs };
  const args = [];
  for (let i = 0; i < names.length; i++) {
    if (i < positional.length) args.push(positional[i]);
    else if (names[i] in rest) {
      args.push(rest[names[i]]);
      delete rest[names[i]];
    } else args.push(undefined);
  }
  for (let i = 0; i < names.length; i++) {
    const n = names[i];
    const v = args[i];
    if (n === "head" && Array.isArray(v)) args[i] = buildList(v, pos);
    else if (n === "root" && Array.isArray(v)) args[i] = buildTree(v);
    else if (["list1", "list2", "l1", "l2"].includes(n) && Array.isArray(v))
      args[i] = buildList(v, null);
  }
  return args;
}

const logLines = [];
const sandbox = {
  ListNode,
  TreeNode,
  Math,
  JSON,
  Array,
  Object,
  String,
  Number,
  Boolean,
  Map,
  Set,
  Date,
  RegExp,
  Infinity,
  NaN,
  parseInt,
  parseFloat,
  isNaN,
  isFinite,
  console: {
    log: (...a) => logLines.push(a.map((x) => stringify(x)).join(" ")),
    error: (...a) => logLines.push(a.map((x) => stringify(x)).join(" ")),
    warn: (...a) => logLines.push(a.map((x) => stringify(x)).join(" ")),
    info: (...a) => logLines.push(a.map((x) => stringify(x)).join(" ")),
  },
};

function stringify(x) {
  try {
    return typeof x === "object" ? JSON.stringify(x) : String(x);
  } catch {
    return String(x);
  }
}

const result = {
  ok: false,
  kind: "",
  error: "",
  trace: "",
  actual: "",
  alternates: [],
  stdout: "",
  runtime_ms: 0,
  memory_kb: 0,
};
const start = Date.now();

try {
  vm.createContext(sandbox);
  const builtinKeys = new Set(Object.keys(sandbox));
  vm.runInContext(job.code, sandbox, { timeout: 8000, displayErrors: true });
  const defined = Object.keys(sandbox).filter(
    (k) => !builtinKeys.has(k) && typeof sandbox[k] === "function"
  );

  const hints = job.params || [];
  const positional = job.args || [];
  const kwargs = job.kwargs || {};
  const pos = Number.isInteger(kwargs.pos) ? kwargs.pos : null;
  let value;

  const design = tryDesignRun(job, sandbox);
  if (design !== null) {
    value = design;
  } else if (typeof sandbox.Solution === "function" && defined.includes("Solution")) {
    const proto = sandbox.Solution.prototype;
    const methods = Object.getOwnPropertyNames(proto).filter(
      (k) => k !== "constructor" && typeof proto[k] === "function"
    );
    if (!methods.length) throw new Error("Solution class has no public methods");
    const method = methods.find((m) => hints.includes(m)) || methods[0];
    const names = paramNames(proto[method]).filter((n) => n !== "this");
    const instance = new sandbox.Solution();
    value = instance[method](...buildCallArgs(names, positional, kwargs, pos));
  } else {
    const candidates = defined;
    if (!candidates.length) throw new Error("No callable function found in code");
    const arity = positional.length || Object.keys(kwargs).filter((k) => k !== "pos").length;
    let fnName = candidates[0];
    let best = -1;
    for (const k of candidates) {
      const ps = paramNames(sandbox[k]);
      let score = 0;
      if (hints.length && ps.some((p) => hints.includes(p))) score = 2;
      else if (hints.length && ps.length === hints.length) score = 1;
      else if (!hints.length && arity && ps.length === arity) score = 1;
      if (score > best) {
        best = score;
        fnName = k;
      }
      if (best === 2) break;
    }
    const names = paramNames(sandbox[fnName]);
    value = sandbox[fnName](...buildCallArgs(names, positional, kwargs, pos));
  }

  result.actual = formatResult(value);
  try {
    result.alternates = resultAlternates(value);
  } catch {
    result.alternates = [];
  }
  result.ok = true;
} catch (err) {
  result.kind = err && err.code === "ERR_SCRIPT_EXECUTION_TIMEOUT" ? "timeout" : "runtime";
  result.error = String((err && err.message) || err);
  result.trace = String((err && err.stack) || "").slice(0, 1500);
}

result.runtime_ms = Date.now() - start;
result.stdout = logLines.join("\n").slice(-4000);
const mem = process.memoryUsage ? process.memoryUsage().heapUsed : 0;
result.memory_kb = Math.round(mem / 1024);
process.stdout.write(JSON.stringify(result));
