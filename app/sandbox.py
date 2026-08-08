from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from app.code_utils import validate_candidate_code
from app.schemas import CandidateStatus, ProblemSpec, SandboxResult


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
        harness = self._build_harness(code, problem.function_name, cases)
        with tempfile.TemporaryDirectory() as temp_dir:
            script = Path(temp_dir) / "candidate_run.py"
            script.write_text(harness, encoding="utf-8")
            started = time.perf_counter()
            try:
                completed = subprocess.run(
                    [sys.executable, str(script)],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                return SandboxResult(
                    status=CandidateStatus.TIMEOUT,
                    runtime_ms=round((time.perf_counter() - started) * 1000, 3),
                    stdout=exc.stdout or "",
                    stderr=exc.stderr or "",
                    error="execution timed out",
                )

        runtime_ms = round((time.perf_counter() - started) * 1000, 3)
        if completed.returncode != 0:
            return SandboxResult(
                status=CandidateStatus.ERROR,
                runtime_ms=runtime_ms,
                stdout=completed.stdout,
                stderr=completed.stderr,
                error=(completed.stderr or completed.stdout or "candidate failed").strip()[:1000],
            )
        try:
            payload = json.loads(completed.stdout.strip() or "{}")
        except json.JSONDecodeError as exc:
            return SandboxResult(
                status=CandidateStatus.ERROR,
                runtime_ms=runtime_ms,
                stdout=completed.stdout,
                stderr=completed.stderr,
                error=f"invalid json output: {exc}",
            )
        if payload.get("status") != "ok":
            return SandboxResult(
                status=CandidateStatus.ERROR,
                outputs=tuple(payload.get("outputs", [])),
                runtime_ms=runtime_ms,
                error=str(payload.get("error", "candidate error"))[:1000],
            )
        return SandboxResult(
            status=CandidateStatus.PASSED,
            outputs=tuple(payload.get("outputs", [])),
            runtime_ms=runtime_ms,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    @staticmethod
    def _build_harness(code: str, function_name: str, cases: list[dict[str, Any]]) -> str:
        return (
            "import json\n"
            "import math\n"
            "import statistics\n"
            "import traceback\n\n"
            f"{code.strip()}\n\n"
            f"CASES = {json.dumps(cases)}\n\n"
            "def _run():\n"
            "    outputs = []\n"
            f"    fn = globals()[{function_name!r}]\n"
            "    for case in CASES:\n"
            "        if 'args' in case:\n"
            "            outputs.append(fn(*case['args']))\n"
            "        elif 'kwargs' in case:\n"
            "            outputs.append(fn(**case['kwargs']))\n"
            "        else:\n"
            "            outputs.append(fn(case.get('input')))\n"
            "    return outputs\n\n"
            "try:\n"
            "    print(json.dumps({'status': 'ok', 'outputs': _run()}, default=str))\n"
            "except Exception:\n"
            "    print(json.dumps({'status': 'error', 'error': traceback.format_exc()}))\n"
        )
