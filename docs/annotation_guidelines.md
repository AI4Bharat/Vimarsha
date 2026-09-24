# Lattice annotation guidance

The lattice builder surfaces disagreements between ASR systems. It does not
decide whether a form is linguistically acceptable. Final evaluation lattices
require human review.

## Workflow

1. Start from a verified verbatim transcript.
2. Generate a candidate lattice from several independently trained ASR models.
3. A fluent maker reviews every group:
   - retain variants that faithfully represent the same spoken content;
   - remove recognition errors and hallucinations;
   - add common valid forms missed by the models;
   - preserve multi-word alternatives as one group.
4. A separate fluent superchecker verifies the audio, reference, and variants.
5. Resolve disagreements and freeze a versioned manifest.

Web search may provide evidence that a spelling is used, but frequency alone
does not prove that it matches the audio.

## Variation types

The Vimarsha/OIWER taxonomy includes:

- matra and diacritic variation;
- valid loanword and code-mixed spellings;
- compound splitting or merging;
- phonetically equivalent spellings;
- ligature variants;
- sandhi alternations;
- valid inverse-text-normalization forms.

## Exclude

Do not accept a variant when it:

- changes lexical meaning or grammatical content;
- drops or adds a spoken word without a documented transcription convention;
- is merely a model hallucination;
- normalizes a named entity to a different entity;
- encodes uncertainty that a listener cannot resolve from the audio.

## Quality control

- Annotators should be fluent in the language and familiar with its script.
- Keep written, language-specific decisions for recurring cases.
- Audit inter-annotator disagreements and unusually large variant groups.
- Store annotator decisions separately from model predictions.
- Version the annotation policy and manifest together.
- Never evaluate the same systems using unreviewed variants generated from
  their own outputs; doing so can bias the metric toward those systems.
