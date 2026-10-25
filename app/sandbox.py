from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from app.code_utils import ALLOWED_IMPORTS, validate_candidate_code
from app.schemas import CandidateStatus, ProblemSpec, SandboxResult


_SAFE_BUILTIN_NAMES: tuple[str, ...] = (
    "__build_class__",
    "abs",
    "all",
    "any",
    "bin",
    "bool",
    "bytearray",
    "bytes",
    "callable",
    "chr",
    "complex",
    "dict",
    "divmod",
    "enumerate",
    "filter",
    "float",
    "format",
    "frozenset",
    "hash",
    "hex",
    "id",
    "int",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "list",
    "map",
    "max",
    "min",
    "next",
    "object",
    "oct",
    "ord",
    "pow",
    "print",
    "range",
    "repr",
    "reversed",
    "round",
    "set",
    "slice",
    "sorted",
    "str",
    "sum",
    "tuple",
    "zip",
    "ArithmeticError",
    "AssertionError",
    "AttributeError",
    "BaseException",
    "Exception",
    "FloatingPointError",
    "IndexError",
    "KeyError",
    "MemoryError",
    "NameError",
    "NotImplementedError",
    "OverflowError",
    "RuntimeError",
    "StopIteration",
    "TypeError",
    "ValueError",
    "ZeroDivisionError",
)


class SandboxExecutor:
    def __init__(self, timeout_seconds: float = 2.0) -> None:
        self.timeout_seconds = timeout_seconds

    def run(self, code: str, problem: ProblemSpec) -> SandboxResult:
        valid, reason = validate_candidate_code(code, problem.function_name)
        if not valid:
            return SandboxResult(status=CandidateStatus.REJECTED, error=reason)

        cases = [
            {
                key: case[key]
                for key in ("input", "args", "kwargs")
                if key in case
            }
            for case in problem.tests
        ]
        token = secrets.token_hex(32)
        with tempfile.TemporaryDirectory() as temp_dir:
            script = Path(temp_dir) / "candidate_run.py"
            result_path = Path(temp_dir) / f"result-{secrets.token_hex(8)}.json"
            script.write_text(
                self._build_harness(code, problem.function_name, cases, ALLOWED_IMPORTS),
                encoding="utf-8",
            )
            env = self._sandbox_env(token)
            started = time.perf_counter()
            process = subprocess.Popen(
                [sys.executable, "-I", str(script), str(result_path)],
                cwd=temp_dir,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                **self._process_group_kwargs(),
            )
            try:
                _, stderr = process.communicate(timeout=self.timeout_seconds)
            except subprocess.TimeoutExpired:
                self._kill_process_tree(process)
                try:
                    _, stderr = process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    stderr = ""
                return SandboxResult(
                    status=CandidateStatus.TIMEOUT,
                    runtime_ms=round((time.perf_counter() - started) * 1000, 3),
                    stderr=stderr or "",
                    error="execution timed out",
                )
            runtime_ms = round((time.perf_counter() - started) * 1000, 3)

            if not result_path.is_file():
                detail = (stderr or "").strip() or "result channel was not written"
                return SandboxResult(
                    status=CandidateStatus.ERROR,
                    runtime_ms=runtime_ms,
                    stderr=stderr or "",
                    error=detail[:1000],
                )

            try:
                envelope = json.loads(result_path.read_text(encoding="utf-8"))
                body = envelope["body"]
                signature = envelope["signature"]
                if not isinstance(body, str) or not isinstance(signature, str):
                    raise ValueError("malformed result envelope")
            except (OSError, ValueError, KeyError, TypeError) as exc:
                return SandboxResult(
                    status=CandidateStatus.ERROR,
                    runtime_ms=runtime_ms,
                    stderr=stderr or "",
                    error=f"invalid result channel: {exc}",
                )

            expected = hmac.new(
                token.encode("utf-8"), body.encode("utf-8"), hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(expected, signature):
                return SandboxResult(
                    status=CandidateStatus.ERROR,
                    runtime_ms=runtime_ms,
                    stderr=stderr or "",
                    error="result channel signature mismatch",
                )

            try:
                payload = json.loads(body)
            except json.JSONDecodeError as exc:
                return SandboxResult(
                    status=CandidateStatus.ERROR,
                    runtime_ms=runtime_ms,
                    stderr=stderr or "",
                    error=f"invalid result payload: {exc}",
                )

            if payload.get("status") != "ok":
                return SandboxResult(
                    status=CandidateStatus.ERROR,
                    outputs=tuple(payload.get("outputs", ())),
                    runtime_ms=runtime_ms,
                    stderr=stderr or "",
                    error=str(payload.get("error", "candidate error"))[:1000],
                )
            return SandboxResult(
                status=CandidateStatus.PASSED,
                outputs=tuple(payload.get("outputs", ())),
                runtime_ms=runtime_ms,
                stderr=stderr or "",
            )

    @staticmethod
    def _sandbox_env(token: str) -> dict[str, str]:
        names = ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG", "LC_ALL")
        env = {name: os.environ[name] for name in names if name in os.environ}
        env["EVOCODE_RESULT_TOKEN"] = token
        return env

    @staticmethod
    def _process_group_kwargs() -> dict[str, Any]:
        if os.name == "nt":
            return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        return {"start_new_session": True}

    @staticmethod
    def _kill_process_tree(process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                capture_output=True,
                text=True,
                check=False,
            )
            return
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            process.kill()

    @staticmethod
    def _build_harness(
        code: str,
        function_name: str,
        cases: list[dict[str, Any]],
        allowed_imports: set[str],
    ) -> str:
        return (
            "import builtins\n"
            "import hashlib\n"
            "import hmac\n"
            "import json\n"
            "import os\n"
            "import sys\n"
            "import traceback\n"
            "from pathlib import Path\n\n"
            f"ALLOWED_IMPORTS = {sorted(allowed_imports)!r}\n"
            f"FUNCTION_NAME = {function_name!r}\n"
            f"CASES = json.loads({json.dumps(cases)!r})\n"
            f"CANDIDATE_CODE = {code!r}\n"
            f"SAFE_BUILTIN_NAMES = {list(_SAFE_BUILTIN_NAMES)!r}\n\n"
            "def _main():\n"
            "    token = os.environ.pop('EVOCODE_RESULT_TOKEN', '')\n"
            "    result_path = Path(sys.argv[1])\n\n"
            "    def _write(payload):\n"
            "        body = json.dumps(payload, sort_keys=True, default=str)\n"
            "        signature = hmac.new(\n"
            "            token.encode('utf-8'), body.encode('utf-8'), hashlib.sha256\n"
            "        ).hexdigest()\n"
            "        result_path.write_text(\n"
            "            json.dumps({'body': body, 'signature': signature}), encoding='utf-8'\n"
            "        )\n\n"
            "    def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):\n"
            "        if level or name.split('.')[0] not in ALLOWED_IMPORTS:\n"
            "            raise ImportError(f'import of {name!r} is not allowed')\n"
            "        return __import__(name, globals, locals, fromlist, level)\n\n"
            "    safe_builtins = {\n"
            "        name: getattr(builtins, name)\n"
            "        for name in SAFE_BUILTIN_NAMES\n"
            "        if hasattr(builtins, name)\n"
            "    }\n"
            "    safe_builtins['__import__'] = _safe_import\n\n"
            "    def _run():\n"
            "        namespace = {'__builtins__': safe_builtins, '__name__': 'candidate'}\n"
            "        exec(CANDIDATE_CODE, namespace)\n"
            "        fn = namespace.get(FUNCTION_NAME)\n"
            "        if not callable(fn):\n"
            "            raise RuntimeError(f'candidate must define function {FUNCTION_NAME!r}')\n"
            "        outputs = []\n"
            "        for case in CASES:\n"
            "            if 'args' in case:\n"
            "                outputs.append(fn(*case['args']))\n"
            "            elif 'kwargs' in case:\n"
            "                outputs.append(fn(**case['kwargs']))\n"
            "            else:\n"
            "                outputs.append(fn(case.get('input')))\n"
            "        return outputs\n\n"
            "    try:\n"
            "        _write({'status': 'ok', 'outputs': _run()})\n"
            "    except BaseException:\n"
            "        _write({'status': 'error', 'error': traceback.format_exc()[:4000]})\n\n"
            "if __name__ == '__main__':\n"
            "    _main()\n"
        )
