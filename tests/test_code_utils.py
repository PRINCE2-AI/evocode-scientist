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
