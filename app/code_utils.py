from __future__ import annotations

import ast
import hashlib
import re


FORBIDDEN_IMPORTS = {
    "asyncio",
    "ctypes",
    "multiprocessing",
    "os",
    "pathlib",
    "pickle",
    "shutil",
    "signal",
    "socket",
    "subprocess",
    "sys",
    "threading",
}

FORBIDDEN_CALLS = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "globals",
    "input",
    "locals",
    "open",
    "vars",
}


def code_hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()[:16]


def extract_code(text: str) -> str:
    match = re.search(r"```(?:python)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text.strip()


def validate_candidate_code(code: str, function_name: str = "solve") -> tuple[bool, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"syntax error: {exc.msg}"

    has_function = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name.split(".")[0] for alias in node.names]
            if isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module.split(".")[0])
            blocked = sorted(set(names) & FORBIDDEN_IMPORTS)
            if blocked:
                return False, f"forbidden import: {', '.join(blocked)}"
        if isinstance(node, ast.Call):
            name = ""
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name in FORBIDDEN_CALLS:
                return False, f"forbidden call: {name}"
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return False, "dunder attribute access is forbidden"
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            has_function = True

    if not has_function:
        return False, f"candidate must define function `{function_name}`"
    return True, "ok"


def normalize_code(code: str) -> str:
    return "\n".join(line.rstrip() for line in code.strip().splitlines()) + "\n"
