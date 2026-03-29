from __future__ import annotations

import re
from collections.abc import Iterable


CONTROL_FLOW_PATTERN = re.compile(
    r"\b(if|else|elif|switch|case|try|catch|for|while|except|match|when)\b"
)
IMPORT_PATTERN = re.compile(
    r"^\s*(import\s+\w|from\s+\w+\s+import|#include\s+|using\s+|require\()",
    re.IGNORECASE,
)
FUNCTION_PATTERN = re.compile(
    r"^\s*(def |async def |function |const \w+\s*=\s*\(|class |\w+\s*:\s*$)",
    re.IGNORECASE,
)
NORMALIZE_SPACES = re.compile(r"\s+")
NORMALIZE_DIGITS = re.compile(r"\d+")


def count_lines(text: str) -> int:
    return 0 if not text else text.count("\n") + 1


def estimate_complexity(text: str) -> int:
    return len(CONTROL_FLOW_PATTERN.findall(text))


def count_imports(lines: Iterable[str]) -> int:
    return sum(1 for line in lines if IMPORT_PATTERN.search(line))


def max_nesting_depth(lines: list[str]) -> int:
    depth = 0
    max_depth = 0
    indent_stack = [0]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        opens = stripped.count("{")
        closes = stripped.count("}")
        depth += opens
        depth = max(depth - closes, 0)

        indent = len(line) - len(line.lstrip(" "))
        if stripped.endswith(":"):
            while indent_stack and indent < indent_stack[-1]:
                indent_stack.pop()
            if indent > indent_stack[-1]:
                indent_stack.append(indent)
        else:
            while len(indent_stack) > 1 and indent < indent_stack[-1]:
                indent_stack.pop()

        current_depth = max(depth, len(indent_stack) - 1)
        max_depth = max(max_depth, current_depth)
    return max_depth


def estimate_largest_block(lines: list[str]) -> int:
    largest = 0
    current = 0
    inside = False

    for line in lines:
        if FUNCTION_PATTERN.search(line):
            inside = True
            current = 1
            largest = max(largest, current)
            continue
        if inside:
            if line.strip():
                current += 1
                largest = max(largest, current)
            else:
                inside = False
                current = 0
    return largest


def normalize_line(line: str) -> str:
    trimmed = line.strip().lower()
    if not trimmed or trimmed.startswith(("#", "//")):
        return ""
    trimmed = NORMALIZE_DIGITS.sub("0", trimmed)
    return NORMALIZE_SPACES.sub(" ", trimmed)
