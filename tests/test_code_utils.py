from app.code_utils import code_hash, extract_code, validate_candidate_code


def test_extract_code_from_markdown_block() -> None:
    text = "```python\ndef solve(x):\n    return x\n```"
    assert extract_code(text).startswith("def solve")


def test_code_hash_is_stable() -> None:
    assert code_hash("abc") == code_hash("abc")
    assert code_hash("abc") != code_hash("abcd")


def test_validator_rejects_unsafe_import() -> None:
    ok, reason = validate_candidate_code("import os\ndef solve(x):\n    return x")
    assert not ok
    assert "forbidden import" in reason


def test_validator_requires_solve_function() -> None:
    ok, reason = validate_candidate_code("def other(x):\n    return x")
    assert not ok
    assert "solve" in reason


def test_validator_allows_allowlisted_imports() -> None:
    code = (
        "import math\n"
        "from collections import deque, namedtuple\n"
        "import statistics\n"
        "def solve(x):\n"
        "    return math.sqrt(x) + len(deque()) + int(statistics.mean([1, 2])) + len(namedtuple('P', 'a'))\n"
    )
    ok, reason = validate_candidate_code(code)
    assert ok, reason


def test_validator_rejects_indirect_dunder_access() -> None:
    payloads = (
        "def solve(x):\n    return getattr(x, '__class__')",
        "import importlib\ndef solve(x):\n    return x",
        "def solve(x):\n    return '{0.__class__}'.format(x)",
        "def solve(x):\n    return ValueError.mro()",
        "def solve(x):\n    return __builtins__",
        "import statistics\ndef solve(x):\n    return statistics.sys",
        "from collections import _sys\ndef solve(x):\n    return x",
        "from math import __loader__\ndef solve(x):\n    return x",
    )
    for code in payloads:
        ok, _ = validate_candidate_code(code)
        assert not ok, code
