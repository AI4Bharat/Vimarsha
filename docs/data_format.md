# Lattice data format

The lattice-construction script reads UTF-8 JSON Lines with one JSON object per
line.

## Input

Required fields:

- `language` or `lang`: supported language name or ISO code;
- one or more fields ending in `_transcription`.

Other metadata is preserved. Transcription fields may be top-level or inside
`metadata_json`. `reference_transcription` and `ground_truth_transcription` are
not treated as model hypotheses.

```json
{
  "id": "utterance-001",
  "language": "hindi",
  "model_a_transcription": "कम रेट पर मिल सकता है",
  "model_b_transcription": "कम रेट पे मिल सकता है"
}
```

## Output

The builder preserves the input fields and adds:

- `lattice`: nested variation groups;
- `lattice_string`: a readable `{a | b} {c}` representation;
- `lattice_models_used`: model field prefixes.

```json
{
  "id": "utterance-001",
  "language": "hindi",
  "model_a_transcription": "कम रेट पर मिल सकता है",
  "model_b_transcription": "कम रेट पे मिल सकता है",
  "lattice": [["कम"], ["रेट"], ["पर", "पे"], ["मिल"], ["सकता"], ["है"]],
  "lattice_string": "{कम} {रेट} {पर | पे} {मिल} {सकता} {है}",
  "lattice_models_used": ["model_a", "model_b"]
}
```

The generated lattice is a candidate for human annotation, not evaluation
ground truth.
