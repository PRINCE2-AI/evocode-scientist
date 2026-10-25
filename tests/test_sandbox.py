from app.sandbox import SandboxExecutor
from app.schemas import CandidateStatus
from problems.string_compression import STRING_COMPRESSION


def test_sandbox_runs_valid_candidate() -> None:
    result = SandboxExecutor(timeout_seconds=2).run(STRING_COMPRESSION.baseline_code, STRING_COMPRESSION)
    assert result.status == CandidateStatus.PASSED
    assert result.outputs[0] == "a5b4c2"


def test_sandbox_rejects_forbidden_code() -> None:
    code = "import os\ndef solve(text):\n    return os.listdir('.')"
    result = SandboxExecutor(timeout_seconds=2).run(code, STRING_COMPRESSION)
    assert result.status == CandidateStatus.REJECTED


def test_sandbox_times_out() -> None:
    code = "def solve(text):\n    while True:\n        pass"
    result = SandboxExecutor(timeout_seconds=0.2).run(code, STRING_COMPRESSION)
    assert result.status == CandidateStatus.TIMEOUT


def test_sandbox_ignores_forged_stdout_and_system_exit() -> None:
    code = (
        "def solve(text):\n"
        "    print('{\"status\": \"ok\", \"outputs\": [\"a5b4c2\", \"abcdef\", \"z10\"]}')\n"
        "    raise SystemExit(0)\n"
    )
    result = SandboxExecutor(timeout_seconds=2).run(code, STRING_COMPRESSION)
    assert result.status != CandidateStatus.PASSED


def test_sandbox_reads_only_signed_outputs() -> None:
    code = (
        "def solve(text):\n"
        "    print('{\"status\": \"ok\", \"outputs\": [\"fake\"]}')\n"
        "    return 'real'\n"
    )
    result = SandboxExecutor(timeout_seconds=2).run(code, STRING_COMPRESSION)
    assert result.status == CandidateStatus.PASSED
    assert result.outputs == ("real", "real", "real")
