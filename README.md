# Vimarsha

Faithful ASR evaluation for Indian languages with demographic diversity,
in-the-wild audio, and spelling variation.

Vimarsha accompanies the paper **“Vimarsha: Faithful ASR Evaluation for Indian
Languages with Demographic Diversity, In-the-Wild Audio and Spelling
Variations.”** The benchmark studies all 22 scheduled Indian languages and
addresses two common evaluation biases:

1. clean recordings can make ASR performance look unrealistically strong; and
2. a single rigid reference can count valid spellings as recognition errors.

This repository contains the reusable evaluation components:

- OIWER (Orthographically-Informed Word Error Rate);
- candidate lattice construction from multiple ASR hypotheses;
- lattice format and annotation guidance;
- runnable examples and tests.

The Vimarsha benchmark will be released separately on Hugging Face. This
repository contains only the Python evaluation and lattice utilities.

## Installation

Vimarsha requires Python 3.9 or newer.

```bash
git clone https://github.com/AI4Bharat/Vimarsha.git
cd Vimarsha
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

For development:

```bash
python -m pip install -e ".[dev]"
pytest
```

## Quick start

### Score one prediction

The reference is an ordered sequence of variation groups. Any member of a
group is acceptable at that position.

```bash
vimarsha score \
  --language hindi \
  --hypothesis "कम रेट पे मिल सकता है" \
  --reference '[["कम"], ["रेट"], ["पर", "पे"], ["मिल"], ["सकता"], ["है"]]'
```

This prediction receives 0% OIWER because both `पर` and `पे` are accepted.

### Construct candidate lattices

```bash
vimarsha build-lattices \
  examples/model_outputs.jsonl \
  candidate_lattices.jsonl
```

Each input record needs a `language` or `lang` field and at least one
`*_transcription` field. Output records contain both a nested `lattice` and a
human-readable `lattice_string`.

Candidate lattices are annotation scaffolds, **not automatic ground truth**.
They must be reviewed by fluent annotators before evaluation.

### How lattice construction works

`build-lattices` processes every JSONL record independently:

1. It normalizes punctuation and Indic text, tokenizes each transcription, and
   removes duplicate hypotheses.
2. It aligns the first two token sequences using common spans found by
   `SequenceMatcher`. Differing words are grouped as alternatives; similar
   one-to-two and two-to-one word forms are also considered.
3. It progressively aligns each remaining hypothesis to the current consensus
   and merges new alternatives into the existing groups.
4. It writes the groups as both a nested list and a readable lattice string,
   for example `{कम} {रेट} {पर | पे}`.

Because this is a heuristic progressive alignment, hypothesis order can affect
the result. In the paper, fluent makers reviewed, removed, and added variants,
and supercheckers verified the final references. See the
[annotation guidance](docs/annotation_guidelines.md) for that review process.

## Python API

```python
from vimarsha import build_lattice, compute_oiwer

reference = [["कम"], ["रेट"], ["पर", "पे"], ["मिल"], ["सकता"], ["है"]]
result = compute_oiwer("कम रेट पे मिल सकता है", reference, "hi")
print(result.score)       # 0.0
print(result.operations)  # ('c', 'c', 'c', 'c', 'c', 'c')

candidate = build_lattice(
    ["कम रेट पर मिल सकता है", "कम रेट पे मिल सकता है"],
    language="hindi",
)
```

## OIWER

For a hypothesis `H` and an ordered lattice of acceptable reference forms
`L`, OIWER selects the lowest-error alignment permitted by the lattice:

**OIWER = 100 × (I + D + S) / N**

where `I`, `D`, and `S` are insertion, deletion, and substitution counts,
and `N` is the number of reference words in the selected alignment. As with
standard WER, insertions can produce values above 100%.

The implementation retains the preprocessing and phrase-variation behavior
used for the paper's evaluation.

## Lattice input format

Minimal lattice-construction record:

```json
{
  "id": "utterance-001",
  "language": "hindi",
  "model_a_transcription": "कम रेट पर",
  "model_b_transcription": "कम रेट पे"
}
```

See [the lattice format documentation](docs/data_format.md) for details.

## Supported languages

Assamese, Bengali, Bodo, Dogri, Gujarati, Hindi, Kannada, Kashmiri, Konkani,
Maithili, Malayalam, Manipuri, Marathi, Nepali, Odia, Punjabi, Sanskrit,
Santali, Sindhi, Tamil, Telugu, and Urdu. APIs accept either the lowercase
language name or its ISO code.

## Repository layout

```text
src/vimarsha/
  metric.py          OIWER and alignments
  lattice.py         candidate lattice construction
  normalization.py   shared Indic text normalization
  io.py              lattice and JSONL parsing
  cli.py             command-line interface
examples/             synthetic, runnable manifests
tests/                metric and lattice regression tests
docs/                 lattice format and annotation guidance
```
