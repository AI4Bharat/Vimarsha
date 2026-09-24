"""Command-line interface for Vimarsha utilities."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .io import parse_lattice, read_jsonl, write_jsonl
from .lattice import build_lattice, format_lattice
from .metric import compute_oiwer


def _result_dict(result: Any) -> dict[str, Any]:
    return {
        "oiwer_percent": result.score,
        "insertions": result.insertions,
        "deletions": result.deletions,
        "substitutions": result.substitutions,
        "reference_words": result.reference_words,
        "hypothesis_alignment": result.hypothesis_alignment,
        "reference_alignment": result.reference_alignment,
        "operations": result.operations,
    }


def _hypotheses(record: dict[str, Any]) -> dict[str, str]:
    containers = [record]
    if isinstance(record.get("metadata_json"), dict):
        containers.append(record["metadata_json"])
    result: dict[str, str] = {}
    excluded = {"reference_transcription", "ground_truth_transcription"}
    for container in containers:
        for key, value in container.items():
            if (
                key.endswith("_transcription")
                and key not in excluded
                and isinstance(value, str)
                and value.strip()
            ):
                result.setdefault(key.removesuffix("_transcription"), value)
    return result


def _score(args: argparse.Namespace) -> None:
    try:
        reference_value = json.loads(args.reference)
    except json.JSONDecodeError:
        reference_value = args.reference
    result = compute_oiwer(args.hypothesis, parse_lattice(reference_value), args.language)
    print(json.dumps(_result_dict(result), ensure_ascii=False, indent=2))


def _lattice_records(
    input_path: Path, fallback_language: str | None
) -> Iterable[dict[str, Any]]:
    for line_number, record in read_jsonl(input_path):
        language = record.get("language") or record.get("lang") or fallback_language
        if not isinstance(language, str) or not language:
            raise ValueError(f"{input_path}:{line_number}: missing language/lang")
        hypotheses = _hypotheses(record)
        if not hypotheses:
            raise ValueError(f"{input_path}:{line_number}: no *_transcription fields")
        lattice = build_lattice(hypotheses.values(), language)
        output = dict(record)
        output["lattice"] = lattice
        output["lattice_string"] = format_lattice(lattice)
        output["lattice_models_used"] = list(hypotheses)
        yield output


def _build_lattices(args: argparse.Namespace) -> None:
    write_jsonl(args.output, iter(_lattice_records(args.input, args.language)))
    print(f"Wrote candidate lattices to {args.output}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vimarsha")
    commands = parser.add_subparsers(dest="command", required=True)

    score = commands.add_parser("score", help="score one hypothesis")
    score.add_argument("--hypothesis", required=True)
    score.add_argument("--reference", required=True, help="Nested JSON or brace/pipe lattice")
    score.add_argument("--language", required=True, help="Language name or ISO code")
    score.set_defaults(function=_score)

    lattice = commands.add_parser(
        "build-lattices", help="construct candidate lattices from *_transcription fields"
    )
    lattice.add_argument("input", type=Path)
    lattice.add_argument("output", type=Path)
    lattice.add_argument("--language", help="Fallback language for records without one")
    lattice.set_defaults(function=_build_lattices)
    return parser


def main() -> None:
    args = _parser().parse_args()
    args.function(args)


if __name__ == "__main__":
    main()
