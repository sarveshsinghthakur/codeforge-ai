"""Isolated Python runner — executes one test case in a subprocess.

Usage: python -I runner_python.py <job.json>
Job: {"code": str, "args": [...], "kwargs": {...}, "params": [names], "memory_limit_kb": int}
Writes a single JSON result to stdout.
"""
import ast
import inspect
import io
import json
import sys
import time
import traceback
import tracemalloc


def _structure_class(ns, name):
    obj = ns.get(name)
    if isinstance(obj, type):
        return obj
    return None


def build_linked_list(values, list_node_cls, pos=None):
    if not values:
        return None
    nodes = [list_node_cls(v) for v in values]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    if pos is not None and 0 <= pos < len(nodes):
        nodes[-1].next = nodes[pos]
    return nodes[0]


def build_tree(values, tree_node_cls):
    if not values:
        return None
    root = tree_node_cls(values[0])
    queue = [root]
    i = 1
    while queue and i < len(values):
        node = queue.pop(0)
        if i < len(values):
            v = values[i]
            i += 1
            if v is not None:
                node.left = tree_node_cls(v)
                queue.append(node.left)
        if i < len(values):
            v = values[i]
            i += 1
            if v is not None:
                node.right = tree_node_cls(v)
                queue.append(node.right)
    return root


def find_solution_callable(ns, param_hints):
    """Locate the function/method the test harness should call.

    Returns (callable, params_without_self, is_method).
    """
    solution_cls = ns.get("Solution")
    candidates = []
    if isinstance(solution_cls, type):
        for name, member in vars(solution_cls).items():
            if name.startswith("_") or not callable(member):
                continue
            try:
                sig = inspect.signature(member)
            except (TypeError, ValueError):
                continue
            params = [p for p in sig.parameters if p not in ("self", "cls")]
            candidates.append((member, params, True))
    for name, obj in list(ns.items()):
        if name.startswith("_") or not callable(obj) or isinstance(obj, type):
            continue
        if inspect.isclass(obj) or inspect.ismodule(obj):
            continue
        try:
            sig = inspect.signature(obj)
        except (TypeError, ValueError):
            continue
        candidates.append((obj, list(sig.parameters), False))

    if not candidates:
        return None, None, False

    hints = [h for h in (param_hints or []) if h]
    if hints:
        for fn, params, is_method in candidates:
            if params and params[0] in hints:
                return fn, params, is_method
        for fn, params, is_method in candidates:
            if any(p in hints for p in params):
                return fn, params, is_method
        # hints may be positional-only names: match by count instead
        for fn, params, is_method in candidates:
            if len(params) == len(hints):
                return fn, params, is_method

    fn, params, is_method = candidates[0]
    return fn, params, is_method


def bind_arguments(params, args, kwargs, is_method, receiver_cls):
    args = list(args or [])
    kwargs = dict(kwargs or {})
    call_kwargs = {}
    receiver = receiver_cls() if (is_method and receiver_cls is not None) else None
    for i, p in enumerate(params):
        if i < len(args):
            continue
        if p in kwargs:
            call_kwargs[p] = kwargs.pop(p)
    return receiver, args, call_kwargs



def convert_structures(params, values, kwargs, ns, extra):
    """Turn JSON lists into ListNode/TreeNode objects where appropriate."""
    list_cls = _structure_class(ns, "ListNode")
    tree_cls = _structure_class(ns, "TreeNode")

    def convert_one(param_name, value):
        if not isinstance(value, list):
            return value
        if param_name in ("root",) or (tree_cls and param_name in ("node", "tree")):
            if tree_cls is not None and (param_name == "root" or _looks_like_tree(value)):
                return build_tree(value, tree_cls)
        if param_name in ("head", "list1", "list2", "l1", "l2") and list_cls is not None:
            pos = extra.get("pos") if param_name == "head" else None
            return build_linked_list(value, list_cls, pos)
        return value

    new_values = []
    for i, v in enumerate(values):
        name = params[i] if i < len(params) else None
        new_values.append(convert_one(name, v))
    new_kwargs = {}
    for k, v in kwargs.items():
        new_kwargs[k] = convert_one(k, v)
    return new_values, new_kwargs


def _looks_like_tree(value):
    return any(v is None for v in value)


def serialize_list_node(node):
    vals = []
    seen = set()
    cur = node
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        vals.append(getattr(cur, "val", None))
        cur = getattr(cur, "next", None)
    import json as _json
    return _json.dumps(vals, separators=(",", ":"))


def serialize_tree_node(node):
    if node is None:
        return "[]"
    out = []
    queue = [node]
    while queue:
        n = queue.pop(0)
        if n is None:
            out.append(None)
            continue
        out.append(getattr(n, "val", None))
        queue.append(getattr(n, "left", None))
        queue.append(getattr(n, "right", None))
    while out and out[-1] is None:
        out.pop()
    import json as _json
    return _json.dumps(out, separators=(",", ":"))


def _node_kind(obj):
    cls = type(obj).__name__
    if cls == "ListNode" or (hasattr(obj, "val") and hasattr(obj, "next")):
        return "list"
    if cls == "TreeNode" or (hasattr(obj, "val") and hasattr(obj, "left")):
        return "tree"
    return None


def result_alternates(value):
    """Extra encodings the comparison layer may try for node results."""
    kind = _node_kind(value)
    if kind == "list":
        parts = []
        seen = set()
        cur = value
        while cur is not None and id(cur) not in seen:
            seen.add(id(cur))
            parts.append(str(getattr(cur, "val", "")))
            cur = getattr(cur, "next", None)
        alts = ["->".join(parts)]
        if parts:
            alts.append(parts[0])
        return alts
    if kind == "tree":
        alts = [serialize_tree_node(value)]
        first = getattr(value, "val", None)
        if first is not None:
            alts.append(str(first))
        return alts
    return []


def format_result(result):
    if result is None:
        return ""
    if isinstance(result, bool):
        return "true" if result else "false"
    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    if isinstance(result, (list, tuple)):
        try:
            import json as _json
            return _json.dumps(list(result), separators=(",", ":"))
        except (TypeError, ValueError):
            return str(result)
    if isinstance(result, dict):
        import json as _json
        try:
            return _json.dumps(result, separators=(",", ":"), sort_keys=True)
        except (TypeError, ValueError):
            return str(result)
    if isinstance(result, str):
        return result
    kind = _node_kind(result)
    if kind == "list":
        return serialize_list_node(result)
    if kind == "tree":
        return str(getattr(result, "val", result))
    return str(result)


def try_design_run(job, namespace):
    """Execute LeetCode-style design problems: ops + args line harness.

    Returns the result list, or None when the input is not a design call.
    """
    args = job.get("args") or []
    if len(args) != 2:
        return None
    ops, opargs = args
    if not isinstance(ops, list) or not ops or not all(isinstance(o, str) for o in ops):
        return None
    if not isinstance(opargs, list) or not opargs or not all(isinstance(a, list) for a in opargs):
        return None
    cls = namespace.get(ops[0])
    if not isinstance(cls, type):
        return None
    obj = cls(*opargs[0])
    out = [None]
    for op, a in zip(ops[1:], opargs[1:]):
        ret = getattr(obj, op)(*a)
        out.append(ret)
    return out


def main():
    job_path = sys.argv[1]
    with open(job_path, encoding="utf-8") as fh:
        job = json.load(fh)

    result = {
        "ok": False,
        "kind": "",
        "error": "",
        "traceback": "",
        "actual": "",
        "alternates": [],
        "stdout": "",
        "runtime_ms": 0,
        "memory_kb": 0,
    }

    tracemalloc.start()
    captured = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    start = time.perf_counter()
    namespace = {"__name__": "__main__"}
    try:
        sys.stdout = captured
        sys.stderr = captured
        source = job.get("code", "")
        try:
            compiled = compile(source, "<code>", "exec")
        except SyntaxError as exc:
            result["kind"] = "compile"
            result["error"] = f"SyntaxError: {exc.msg} (line {exc.lineno})"
            raise SystemExit(0)
        exec(compiled, namespace)

        params = job.get("params") or []
        design_value = try_design_run(job, namespace)
        if design_value is not None:
            value = design_value
        else:
            fn, fn_params, is_method = find_solution_callable(namespace, params)
            if fn is None:
                result["kind"] = "runtime"
                result["error"] = "No callable solution function or class `Solution` was found."
                raise SystemExit(0)

            effective_params = fn_params or params
            receiver, call_args, call_kwargs = bind_arguments(
                effective_params, job.get("args"), job.get("kwargs"),
                is_method, namespace.get("Solution") if is_method else None,
            )
            call_args, call_kwargs = convert_structures(
                effective_params, call_args, call_kwargs, namespace, job.get("kwargs") or {}
            )
            if receiver is not None:
                value = fn(receiver, *call_args, **call_kwargs)
            else:
                value = fn(*call_args, **call_kwargs)
        result["actual"] = format_result(value)
        try:
            result["alternates"] = result_alternates(value)
        except Exception:
            result["alternates"] = []
        result["ok"] = True
    except SystemExit:
        pass
    except BaseException as exc:  # noqa: BLE001 - user code may raise anything
        result["kind"] = "runtime"
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc(limit=4)
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result["runtime_ms"] = int((time.perf_counter() - start) * 1000)
        result["memory_kb"] = int(peak / 1024)
        result["stdout"] = captured.getvalue()[-4000:]

    json.dump(result, sys.stdout)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
