from __future__ import annotations

import ast
import hashlib
import re


ALLOWED_IMPORTS = {
    "bisect",
    "collections",
    "functools",
    "heapq",
    "itertools",
    "math",
    "statistics",
}

FORBIDDEN_CALLS = {
    "__import__",
    "breakpoint",
    "compile",
    "delattr",
    "dir",
    "eval",
    "exec",
    "getattr",
    "globals",
    "help",
    "input",
    "locals",
    "open",
    "setattr",
    "vars",
}

FORBIDDEN_NAMES = {
    "__builtins__",
    "builtins",
    "importlib",
    "operator",
    "subprocess",
    "sys",
    "typing",
}

FORBIDDEN_ATTRIBUTES = {
    "format",
    "format_map",
    "mro",
}


def code_hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()[:16]


def extract_code(text: str) -> str:
    match = re.search(r"```(?:python)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text.strip()


def _unsafe_binding(name: str, asname: str | None) -> bool:
    if name.startswith("_") or name in FORBIDDEN_NAMES:
        return True
    if asname is None:
        return False
    return asname.startswith("_") or asname in FORBIDDEN_NAMES


def validate_candidate_code(code: str, function_name: str = "solve") -> tuple[bool, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"syntax error: {exc.msg}"

    has_function = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name.split(".")[0] for alias in node.names]
            blocked = sorted(set(modules) - ALLOWED_IMPORTS)
            if blocked:
                return False, f"forbidden import: {', '.join(blocked)}"
            for alias in node.names:
                if _unsafe_binding(alias.name, alias.asname):
                    return False, f"forbidden binding: {alias.asname or alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                return False, "relative imports are forbidden"
            module = (node.module or "").split(".")[0]
            if module not in ALLOWED_IMPORTS:
                return False, f"forbidden import: {module or '<missing module>'}"
            for alias in node.names:
                if _unsafe_binding(alias.name, alias.asname):
                    return False, f"forbidden binding: {alias.asname or alias.name}"
        if isinstance(node, ast.Call):
            name = ""
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name in FORBIDDEN_CALLS:
                return False, f"forbidden call: {name}"
        if isinstance(node, ast.Attribute) and (
            node.attr.startswith("_")
            or node.attr in FORBIDDEN_ATTRIBUTES
            or node.attr in FORBIDDEN_NAMES
        ):
            return False, f"forbidden attribute access: {node.attr}"
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return False, f"forbidden name: {node.id}"
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            has_function = True

    if not has_function:
        return False, f"candidate must define function `{function_name}`"
    return True, "ok"


def normalize_code(code: str) -> str:
    return "\n".join(line.rstrip() for line in code.strip().splitlines()) + "\n"
