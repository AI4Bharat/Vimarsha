"""Orthographically-Informed Word Error Rate (OIWER)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .normalization import normalize_text

Lattice = Sequence[Sequence[str]]


@dataclass(frozen=True)
class OIWERResult:
    """Alignment and error counts for one utterance."""

    score: float
    insertions: int
    deletions: int
    substitutions: int
    reference_words: int
    hypothesis_alignment: tuple[str, ...]
    reference_alignment: tuple[str, ...]
    operations: tuple[str, ...]

    @property
    def errors(self) -> int:
        return self.insertions + self.deletions + self.substitutions


def _normalize_lattice(reference: Lattice, language: str) -> list[list[str]]:
    if isinstance(reference, (str, bytes)) or not isinstance(reference, Sequence):
        raise TypeError("reference must be a sequence of variation groups")

    normalized: list[list[str]] = []
    for index, group in enumerate(reference):
        if isinstance(group, (str, bytes)) or not isinstance(group, Sequence):
            raise TypeError(f"reference group {index} must be a sequence of strings")
        variants = []
        for value in group:
            if not isinstance(value, str):
                raise TypeError(f"reference variant in group {index} must be a string")
            clean = normalize_text(value, language)
            if clean and clean not in variants:
                variants.append(clean)
        if variants:
            normalized.append(variants)
    if not normalized:
        raise ValueError("reference lattice has no non-empty variants")
    return normalized


def _expand_phrases(
    lattice: list[list[str]], hypothesis: list[str]
) -> tuple[list[list[str]], list[int]]:
    """Match the released metric's phrase-selection behavior."""
    expanded: list[list[str]] = []
    source_groups: list[int] = []
    for group_index, variants in enumerate(lattice):
        if any(len(variant.split()) > 1 for variant in variants):
            best = max(
                variants,
                key=lambda variant: sum(word in variant.split() for word in hypothesis),
            )
            for word in best.split():
                expanded.append([word])
                source_groups.append(group_index)
        else:
            expanded.append(variants)
            source_groups.append(group_index)
    return expanded, source_groups


def compute_oiwer(hypothesis: str, reference: Lattice, language: str) -> OIWERResult:
    """Compute utterance-level OIWER using the Vimarsha evaluation protocol.

    ``reference`` is an ordered list of variation groups. Each group contains
    one or more acceptable surface forms, including multi-word forms.
    """
    hypothesis_words = normalize_text(hypothesis, language).split()
    normalized_lattice = _normalize_lattice(reference, language)
    expanded, source_groups = _expand_phrases(normalized_lattice, hypothesis_words)

    rows, columns = len(expanded) + 1, len(hypothesis_words) + 1
    costs = [[0] * columns for _ in range(rows)]
    back: list[list[tuple[str, int] | None]] = [[None] * columns for _ in range(rows)]
    for row in range(1, rows):
        costs[row][0] = row
        back[row][0] = ("d", 0)
    for column in range(1, columns):
        costs[0][column] = column
        back[0][column] = ("i", 0)

    for row, variants in enumerate(expanded, start=1):
        for column, word in enumerate(hypothesis_words, start=1):
            variant_index = min(
                range(len(variants)),
                key=lambda index: costs[row - 1][column - 1]
                + (variants[index] != word),
            )
            diagonal = costs[row - 1][column - 1] + (
                variants[variant_index] != word
            )
            deletion = costs[row - 1][column] + 1
            insertion = costs[row][column - 1] + 1
            best = min(diagonal, deletion, insertion)
            costs[row][column] = best
            # Match the original traceback preference: diagonal, insertion, deletion.
            if diagonal == best:
                back[row][column] = ("c" if variants[variant_index] == word else "s", variant_index)
            elif insertion == best:
                back[row][column] = ("i", 0)
            else:
                back[row][column] = ("d", 0)

    aligned_hypothesis: list[str] = []
    aligned_reference: list[str] = []
    operations: list[str] = []
    aligned_groups: list[int | None] = []
    row, column = rows - 1, columns - 1
    while row or column:
        operation, variant_index = back[row][column]  # type: ignore[misc]
        operations.append(operation)
        if operation in {"c", "s"}:
            aligned_hypothesis.append(hypothesis_words[column - 1])
            aligned_reference.append(expanded[row - 1][variant_index])
            aligned_groups.append(source_groups[row - 1])
            row -= 1
            column -= 1
        elif operation == "i":
            aligned_hypothesis.append(hypothesis_words[column - 1])
            aligned_reference.append("")
            aligned_groups.append(None)
            column -= 1
        else:
            aligned_hypothesis.append("")
            aligned_reference.append(expanded[row - 1][0])
            aligned_groups.append(source_groups[row - 1])
            row -= 1

    aligned_hypothesis.reverse()
    aligned_reference.reverse()
    operations.reverse()
    aligned_groups.reverse()

    # Recover exact multi-word alternatives after word-level alignment.
    position = 0
    while position < len(operations):
        if operations[position] == "c":
            position += 1
            continue
        end = position + 1
        while end < len(operations) and operations[end] != "c":
            end += 1
        groups = {group for group in aligned_groups[position:end] if group is not None}
        hypothesis_span = " ".join(
            word for word in aligned_hypothesis[position:end] if word
        )
        if len(groups) == 1:
            group = groups.pop()
            if hypothesis_span in normalized_lattice[group]:
                for index in range(position, end):
                    operations[index] = "c" if aligned_hypothesis[index] else "ignore"
                    if aligned_hypothesis[index]:
                        aligned_reference[index] = aligned_hypothesis[index]
        position = end

    kept = [index for index, operation in enumerate(operations) if operation != "ignore"]
    operations = [operations[index] for index in kept]
    aligned_hypothesis = [aligned_hypothesis[index] for index in kept]
    aligned_reference = [aligned_reference[index] for index in kept]

    insertions = operations.count("i")
    deletions = operations.count("d")
    substitutions = operations.count("s")
    reference_words = len(expanded)
    score = ((insertions + deletions + substitutions) / reference_words) * 100
    return OIWERResult(
        score=score,
        insertions=insertions,
        deletions=deletions,
        substitutions=substitutions,
        reference_words=reference_words,
        hypothesis_alignment=tuple(aligned_hypothesis),
        reference_alignment=tuple(aligned_reference),
        operations=tuple(operations),
    )
