"""Candidate lattice construction from multiple ASR hypotheses."""

from __future__ import annotations

from collections.abc import Iterable
from difflib import SequenceMatcher

from .normalization import normalize_text


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left.casefold(), right.casefold()).ratio()


def _align_pair(left: list[str], right: list[str]) -> list[list[str]]:
    """Align two token sequences using the released heuristic."""
    result: list[list[str]] = []
    left_index = right_index = 0
    for match in SequenceMatcher(None, left, right).get_matching_blocks():
        while left_index < match.a or right_index < match.b:
            if left_index >= match.a:
                result.append([right[right_index]])
                right_index += 1
                continue
            if right_index >= match.b:
                result.append([left[left_index]])
                left_index += 1
                continue

            left_word, right_word = left[left_index], right[right_index]
            if _similarity(left_word, right_word) >= 0.5:
                result.append(list(dict.fromkeys([left_word, right_word])))
                left_index += 1
                right_index += 1
                continue

            left_to_two = (
                " ".join(right[right_index : right_index + 2])
                if right_index + 1 < match.b
                else ""
            )
            two_to_right = (
                " ".join(left[left_index : left_index + 2])
                if left_index + 1 < match.a
                else ""
            )
            score_left_to_two = _similarity(left_word, left_to_two) if left_to_two else 0
            score_two_to_right = _similarity(two_to_right, right_word) if two_to_right else 0
            if max(score_left_to_two, score_two_to_right) > 0.5:
                if score_left_to_two >= score_two_to_right:
                    result.append([left_word, left_to_two])
                    left_index += 1
                    right_index += 2
                else:
                    result.append([two_to_right, right_word])
                    left_index += 2
                    right_index += 1
            else:
                result.append([left_word, right_word])
                left_index += 1
                right_index += 1

        for _ in range(match.size):
            result.append([left[left_index]])
            left_index += 1
            right_index += 1
    return result


def _merge(alignment: list[list[str]], sequence: list[str]) -> list[list[str]]:
    consensus = [group[0] for group in alignment]
    pair_alignment = _align_pair(consensus, sequence)
    result: list[list[str]] = []
    alignment_index = 0

    for group in pair_alignment:
        try:
            position = consensus.index(group[0], alignment_index)
        except ValueError:
            result.append(group)
            continue
        result.extend(alignment[alignment_index:position])
        merged = list(alignment[position])
        merged.extend(value for value in group[1:] if value not in merged)
        result.append(merged)
        alignment_index = position + 1

    result.extend(alignment[alignment_index:])
    return result


def build_lattice(transcriptions: Iterable[str], language: str) -> list[list[str]]:
    """Build a candidate lattice from two or more model transcriptions.

    The output is intended as an annotation scaffold. Model-derived alternatives
    must be validated by fluent annotators before they are used as ground truth.
    """
    unique: list[str] = []
    for transcription in transcriptions:
        clean = normalize_text(transcription, language)
        if clean and clean not in unique:
            unique.append(clean)
    if not unique:
        raise ValueError("at least one non-empty transcription is required")

    sequences = [text.split() for text in unique]
    if len(sequences) == 1:
        return [[word] for word in sequences[0]]

    alignment = _align_pair(sequences[0], sequences[1])
    for sequence in sequences[2:]:
        alignment = _merge(alignment, sequence)
    return [list(dict.fromkeys(value for value in group if value)) for group in alignment]


def format_lattice(lattice: Iterable[Iterable[str]]) -> str:
    """Serialize nested variation groups as ``{a | b} {c}``."""
    return " ".join("{" + " | ".join(group) + "}" for group in lattice)
