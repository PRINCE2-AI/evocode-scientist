from __future__ import annotations

from app.schemas import ProblemSpec


def compression_score(output, case: dict) -> float:
    expected = case["expected"]
    if output != expected:
        return 0.0
    original_len = len(case["input"])
    compressed_len = len(str(output))
    return max(0.0, min(1.0, 1.0 - (compressed_len / max(original_len * 2, 1))))


STRING_COMPRESSION_BASELINE = """
def solve(text):
    if not text:
        return ""
    parts = []
    current = text[0]
    count = 1
    for ch in text[1:]:
        if ch == current:
            count += 1
        else:
            parts.append(current + str(count))
            current = ch
            count = 1
    parts.append(current + str(count))
    encoded = "".join(parts)
    return encoded if len(encoded) < len(text) else text
"""


STRING_COMPRESSION = ProblemSpec(
    id="string_compression",
    name="Run-Length String Compression",
    description="Return compact run-length encoding when it is shorter; otherwise return original text.",
    function_name="solve",
    tests=(
        {"input": "aaaaabbbbcc", "expected": "a5b4c2"},
        {"input": "abcdef", "expected": "abcdef"},
        {"input": "zzzzzzzzzz", "expected": "z10"},
    ),
    baseline_code=STRING_COMPRESSION_BASELINE,
    scorer=compression_score,
)
