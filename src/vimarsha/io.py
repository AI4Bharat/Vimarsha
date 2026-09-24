"""Lattice parsing and JSONL helpers."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any


def parse_lattice(value: Any) -> list[list[str]]:
    """Parse a nested-list lattice or a ``{a | b} {c}`` string."""
    if isinstance(value, list):
        if not all(isinstance(group, list) for group in value):
            raise ValueError("a lattice list must contain lists of variants")
        if not all(isinstance(item, str) for group in value for item in group):
            raise ValueError("every lattice variant must be a string")
        return value
    if not isinstance(value, str):
        raise TypeError("lattice must be a nested list or brace/pipe string")

    groups = re.findall(r"\{([^{}]*)\}", value)
    if not groups and value.strip():
        groups = [value]
    return [[variant.strip() for variant in group.split("|")] for group in groups]


def read_jsonl(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield ``(line_number, object)`` pairs from a UTF-8 JSONL file."""
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {error}") from error
            if not isinstance(value, dict):
                raise TypeError(f"{path}:{line_number}: expected a JSON object")
            yield line_number, value


def write_jsonl(path: Path, records: Iterator[dict[str, Any]]) -> None:
    """Write objects to a UTF-8 JSONL file."""
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
