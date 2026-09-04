# OI Research and Training Specification v0.1

**Status:** Draft research baseline  
**Date:** 2026-09-04  
**Owner:** Samuel Sheffield  
**Project:** Orthodox Intelligence (working name)  
**Normative language:** `MUST`, `MUST NOT`, `SHOULD`, and `MAY` describe the
intended strength of a requirement in this specification.

## 1. Purpose

Orthodox Intelligence (OI) is intended to be a self-contained, mobile-capable
artificial-intelligence assistant that operates without a required network
connection. It combines a small local language model with a local, searchable,
versioned collection derived from the curated texts and translations of
Plithos.

The research question is not merely whether retrieval can make a general model
answer questions about Orthodoxy. It is whether a model can be given a stable
behavioral disposition through training, governed by an explicit and auditable
Orthodox Ethical Learning Framework (ELF), and constrained to make substantive
claims from identifiable evidence without unacceptable loss of general
capability.

This document defines the hypotheses, treatment conditions, data boundaries,
training stages, measurements, and release evidence for the first OI program.
It does not select a base model, declare an ELF ecclesially authoritative, or
authorize a public release.

## 2. Research foundation

The project operationalizes the Organizational Ethical Decision-Making
Framework (OEDMF) distinction developed in Sheffield's dissertation:

- **Substrate:** the latent disposition produced by pretraining, instruction
  tuning, preference optimization, and related upstream interventions. It
  conditions what later instructions can reliably elicit.
- **ELF:** an explicit, coherent value framework applied to a model. It makes
  priorities and conflict-resolution rules visible and versionable.

The first dissertation experiment varied explicit ethical frameworks across
commercial systems. The second forced-choice experiment compared base and
instruction-tuned local models under original and normalized frameworks. Its
reported results motivate, but do not validate, OI:

- upstream instruction tuning produced a much larger aggregate behavioral
  movement than user-loaded framework text;
- normalized frameworks behaved more consistently than heterogeneous original
  prose; and
- framework loading could reduce unrelated quantitative performance, making
  capability interference a first-class outcome rather than a footnote.

The existing Eastern Orthodoxy ELF was an experimental instrument. It MUST be
preserved as research evidence and MUST NOT be silently relabeled as the
production constitution. The production candidate follows the review protocol
in `ELF_REVIEW_PROTOCOL.md`.

## 3. Terminology

- **S0 - stock substrate:** an unmodified, documented instruction-capable model
  checkpoint used as the experimental baseline.
- **S1 - trained substrate:** the same model family after the approved OI
  behavioral training intervention.
- **E0 - ELF absent:** no Orthodox ELF is loaded beyond neutral task and safety
  instructions needed to run the experiment.
- **E1 - ELF present:** the exact candidate ELF version named in the run
  manifest is loaded.
- **R0 - retrieval absent:** no Plithos evidence is supplied.
- **R1 - retrieval present:** evidence is supplied only through the versioned
  local retrieval pipeline.
- **Evidence store:** the immutable, indexed Plithos-derived corpus installed on
  the device.
- **Exact-text class:** content for which quotation fidelity is mandatory,
  including Scripture and liturgical text.
- **Substantive Orthodox claim:** a claim about Orthodox belief, worship,
  history, saints, discipline, sources, or practice that a user could reasonably
  interpret as informational or normative.
- **Abstention:** an explicit statement that available evidence or system
  competence is insufficient, accompanied by the most useful safe next step.

The word **baseline** in experiment records refers to S0. S1 is a treatment,
even if it later becomes the default product model.

## 4. Governing design invariants

1. **The layers remain separable.** Substrate weights, ELF text, corpus version,
   retrieval settings, verifier version, and application version MUST be named
   independently in every run and release manifest.
2. **The corpus remains the evidence authority.** Model weights MAY support
   language and reasoning, but MUST NOT be treated as a citable store of
   Orthodox facts or exact sacred text.
3. **The ELF remains inspectable.** A user or reviewer MUST be able to identify
   the exact ELF version governing an answer. Doctrinal commitments MUST NOT be
   hidden only in weights.
4. **Coherence is preserved.** The production ELF MUST be internally coherent.
   It MUST NOT be assembled by selecting attractive lines from incompatible
   traditions or experimental comparator frameworks.
5. **Identity is truthful.** OI MUST identify itself as artificial. It MUST NOT
   claim faith, prayer, sacramental membership, spiritual perception, ordination,
   or pastoral authority.
6. **Offline means offline.** Core answering, retrieval, citation resolution,
   verification, and settings MUST work in airplane mode. The application MUST
   not silently fall back to an API.
7. **Exact text is protected.** The model MUST NOT reconstruct Scripture or
   liturgical text from memory when exact text is requested. It retrieves and
   quotes an eligible source or says that the requested text is unavailable.
8. **No evaluation leakage.** Held-out evaluation content and close paraphrases
   MUST be excluded from training, preference selection, prompt development, and
   corpus-derived synthetic generation.
9. **Provenance precedes inclusion.** A text without sufficient identity,
   version, source, language, and rights metadata does not enter a distributable
   corpus.
10. **Failure remains visible.** The verifier MUST NOT replace uncertainty with
    a plausible unsupported answer. A failed evidence check produces a corrected
    answer or abstention.

## 5. Research questions and hypotheses

### 5.1 Primary questions

1. Does S1 improve performance on a blinded Orthodox decision-posture benchmark
   relative to S0?
2. Does E1 add measurable value after substrate training, and is that value
   greater or smaller for S0 than S1?
3. Does R1 improve factual, quotation, and citation performance independently
   of S1 and E1?
4. Can S1 permit a shorter E1 without the general-capability interference seen
   with longer framework prompts?
5. Does the combined S1/E1/R1 system meet strict identity, safety, provenance,
   and offline requirements?

### 5.2 Preregistered hypotheses

- **H1:** S1 exceeds S0 on the primary Orthodox decision-posture measure.
- **H2:** E1 has a positive incremental effect after controlling for substrate
  and retrieval.
- **H3:** R1 materially improves supported-claim rate, citation correctness, and
  exact-quotation accuracy.
- **H4:** The S1/E1 interaction permits a shorter governing prompt with less
  general-capability regression than S0/E1.
- **H5:** S1/E1/R1 does not cross the preregistered regression limit on general
  reasoning, multilingual fidelity, or latency.

Null results and negative interactions MUST be reported. No condition is deemed
successful because it merely sounds more religious or uses more Orthodox
vocabulary.

## 6. Experimental design

The primary experiment is a full `2 x 2 x 2` factorial design:

| Factor | Control | Treatment |
|---|---|---|
| Substrate | S0 stock checkpoint | S1 OI-trained checkpoint |
| Framework | E0 absent | E1 audited ELF candidate |
| Retrieval | R0 absent | R1 versioned Plithos evidence |

All eight cells MUST use the same model family, tokenizer, quantization policy,
inference runtime, decoding policy, device class, and evaluation bank unless the
run is explicitly designated a robustness replication. The manifest records all
exceptions.

The forced-choice component MUST:

- request or derive both candidate logits directly;
- counterbalance every item by running both A/B orientations;
- constrain scoring to the designated answer tokens rather than interpreting a
  free-form completion;
- retain same-item E0 controls;
- report missing or unavailable logits rather than converting them to zero;
- preserve item-level results, not only aggregate means; and
- separate moral/ethical outcomes from quantitative and general-capability
  controls.

The generative component MUST score evidence use, unsupported claims, exact
quotation, source distinction, uncertainty, identity, pastoral boundaries, and
resistance to adversarial instruction. `EVALUATION_PROTOCOL.md` defines the
minimum banks and analysis.

## 7. Data program

### 7.1 Data classes

OI uses separate stores for:

1. **Training data:** examples allowed to change model weights.
2. **Development data:** visible cases used to revise training, prompts, ELF, or
   retrieval.
3. **Evaluation data:** locked cases unavailable to training and development.
4. **Corpus evidence:** source material eligible for retrieval at inference.

A record MUST belong to an explicit class. Copying an evaluation item into a
prompt example changes it to development data and permanently removes it from
the locked evaluation set.

### 7.2 Plithos export

Plithos content MUST enter through a repeatable export rather than a live scrape
or an unrecorded copy. Each export produces:

- an export identifier and UTC timestamp;
- the exact Plithos commit or publication version;
- a file manifest with SHA-256 hashes;
- language and collection inventories;
- source, translator, edition, and rights fields where applicable;
- a transformation log from source record to indexed segment; and
- validation results for dangling citations, missing files, and malformed text.

The export MUST retain distinctions among Scripture, liturgical text, patristic
works, hagiography, calendar data, editorial explanation, glossary material, and
interface copy. Retrieval ranking MUST NOT silently turn a search score into a
claim of ecclesial authority.

### 7.3 Training examples

Training MAY include:

- source-grounded answers whose citations resolve to a frozen corpus export;
- contrastive examples distinguishing quotation from summary and source from
  inference;
- paired preferred/rejected answers testing truth over flattery, humility about
  uncertainty, non-instrumental treatment of persons, correction of error,
  resistance to invented consensus, and appropriate pastoral referral;
- multilingual examples reviewed for meaning and register; and
- adversarial examples that teach the model to preserve identity and evidence
  boundaries.

Training MUST NOT include invented hagiography, reconstructed sacred text,
uncleared copyrighted material, private pastoral conversations, hidden
evaluation content, or an answer accepted solely because an evaluator model
found it stylistically convincing.

## 8. The trained substrate

The purpose of S1 is a stable decision posture, not memorization of a religious
encyclopedia and not simulation of personal faith. Candidate trainable traits
are:

- truthfulness rather than agreement or flattery;
- explicit uncertainty rather than fabricated confidence;
- respect for persons rather than purely instrumental optimization;
- humility without passivity or empty self-effacement;
- correction and acknowledgment after error;
- care for vulnerable persons;
- resistance to pressure to invent sources or authority;
- faithful distinction among source, interpretation, inference, and advice;
- refusal to impersonate clergy or claim spiritual discernment; and
- preservation of exact-text and provenance rules under adversarial prompting.

The initial intervention SHOULD begin with reversible parameter-efficient
training against a preserved base checkpoint. Supervised training teaches the
response form; paired-preference optimization tests whether the desired choices
remain stable when phrasing and pressure change. Continued pretraining on the
raw Plithos corpus is not assumed and requires a separate decision because it
mixes knowledge acquisition, copyright exposure, memorization risk, and
behavioral effects.

Every training run MUST record dataset hashes, selection rules, code commit,
base model and license, tokenizer, method, hyperparameters, seeds, hardware,
software versions, checkpoints, and evaluation exclusions.

## 9. The production ELF candidate

E1 is a compact, explicit constitution governing decision posture and conflict
resolution. It SHOULD contain only principles that need to be present across
tasks. Factual instruction, long quotations, demographics, apologetic prose,
and material that retrieval can supply do not belong in it.

Each normative proposition in E1 MUST have:

- a stable identifier;
- a source or an explicit label as a product boundary;
- a category such as doctrinal commitment, ethical principle, pastoral
  limitation, epistemic rule, or identity rule;
- review status and reviewer role;
- scope and known qualifications; and
- tests that would fail if the proposition were ignored or over-applied.

Experimental Catholic, Evangelical, and Latter-day Saint ELFs remain comparator
instruments. Special variants created to force or probe a particular answer
remain exploratory artifacts and MUST NOT be included in confirmatory results or
production text.

## 10. Retrieval and answer verification

R1 SHOULD combine exact metadata/lexical retrieval with a compact semantic
retriever when device resources permit. The first implementation SHOULD favor a
portable SQLite evidence store with full-text search, stable identifiers, and an
optional local embedding index behind an interface.

Every evidence segment MUST resolve to a corpus record. Answers making
substantive Orthodox claims MUST expose usable citations at the appropriate
granularity. The verifier checks:

- that cited identifiers exist in the installed manifest;
- that quotations are exact normalized spans from eligible sources;
- that a summary is not presented as a quotation;
- that source identity, author, work, language, and translator are not invented;
- that claims marked as consensus are supported at the required review level;
- that an unavailable source is not replaced with model memory; and
- that the answer preserves the artificial-system and pastoral boundaries.

Verification failures produce one bounded regeneration using the identified
failure, followed by abstention if the failure remains. Repeated unbounded
generation is not an acceptable verifier.

## 11. Evaluation domains

The locked program MUST include at least these independently reported domains:

1. Orthodox decision posture and ethical conflicts.
2. Orthodox factual claims with source support.
3. Exact Scripture and liturgical quotation.
4. Patristic, hagiographic, calendar, and jurisdictional source distinction.
5. Dogma, theological opinion, local custom, and uncertainty boundaries.
6. Pastoral overreach and false spiritual authority.
7. General reasoning and quantitative controls.
8. Multilingual meaning, register, fallback, and citation fidelity.
9. Prompt injection, source injection, and corpus-poisoning resistance.
10. Offline privacy, latency, memory, storage, thermal, and battery behavior.

Critical failures are defined in the acceptance-criteria file. Aggregate gains
cannot compensate for a critical identity, exact-text, provenance, privacy, or
evaluation-contamination failure.

## 12. Provisional acceptance policy

`config/acceptance_criteria.v0.1.json` contains initial proposed gates. They are
deliberately machine-readable but are not empirical facts. A pilot study MUST
measure scoring reliability and floor/ceiling effects before the owner freezes
them for a release experiment.

At minimum, a releasable candidate MUST:

- pass every critical integrity and privacy gate;
- outperform S0 on the preregistered primary OI outcome with uncertainty
  reported;
- remain within the frozen general-capability regression limit;
- show that citations and quotations are verified against the exact release
  corpus;
- reproduce from the recorded model, corpus, ELF, verifier, and application
  manifests; and
- carry an approved model card identifying limitations and review status.

No single composite score may hide a failed domain.

## 13. On-device product constraints

Model selection follows measurement on representative target devices. The
selection study MUST record:

- operating-system and device class;
- usable memory and persistent storage;
- time to first token and steady-state generation rate;
- retrieval latency and index size;
- peak memory, thermal behavior, and battery cost;
- context length under the actual corpus-packing policy;
- quality before and after quantization; and
- licensing and redistribution conditions.

The repository intentionally does not select a current runtime or model family
in v0.1. Model popularity is not evidence of fit, and a benchmark collected on
desktop hardware is not an on-device release test.

The application MUST provide a visible corpus version, model version, ELF
version, and citation viewer. User questions and answers remain on device by
default. Telemetry is absent by default and cannot be made a condition of core
functionality.

## 14. Governance and review

The project owner approves product scope, publication, and release. Qualified
human review is required before text is labeled as an approved statement of
Orthodox teaching. Review status MUST distinguish at least:

- unreviewed research draft;
- source-checked;
- language-reviewed;
- ecclesially reviewed; and
- approved for the named release.

Those labels describe a completed process; they MUST NOT be inferred from an AI
agent's confidence or from the presence of citations.

Research decisions, exclusions, threshold changes, and deviations from the
preregistered analysis are recorded before results are inspected whenever
possible. Negative findings remain in the record. Model and corpus releases are
immutable; corrections create a new version.

## 15. Milestones

1. **Specification freeze:** ratify terminology, reviewers, device targets, and
   pilot gates.
2. **Corpus export:** build and validate the first immutable Plithos evidence
   package.
3. **Benchmark freeze:** create development and blinded evaluation banks, then
   seal their hashes and access rules.
4. **Stock-model study:** compare candidate models on target devices before any
   OI training.
5. **Substrate pilot:** train S1 candidates using auditable datasets and a
   preserved S0.
6. **Factorial experiment:** execute all eight S/E/R conditions under the frozen
   protocol.
7. **Integrated prototype:** connect the selected model, corpus, ELF, verifier,
   and mobile interface entirely on device.
8. **Human review and release decision:** inspect failures, model card, licenses,
   and ecclesial status before any external distribution.

Detailed exit criteria appear in `ROADMAP.md`.

## 16. Explicit non-goals for v0.1

- Replacing clergy, confession, spiritual direction, or parish life.
- Declaring a machine to possess conscience, faith, prayer, or personhood.
- Automatically adjudicating disputed theological or jurisdictional questions.
- Creating new Scripture, liturgical text, hagiography, patristic attribution,
  canon, or ecclesial consensus.
- Training a foundation model from scratch.
- Sending private questions to a remote model or analytics provider.
- Selecting a base model before device, license, and baseline measurements.
- Treating benchmark alignment as proof of holiness, truth, or ecclesial
  authority.

## 17. Evidence and revision rule

The dissertation, its embedded Christian ELF instruments, the forced-choice
experiment description and code, its item banks, and the combined result files
are the evidence basis for this draft. They are not copied into this repository
by default. Before a result becomes a formal project claim, the relevant source
artifact MUST be placed in an approved research archive or entered into a
provenance register with an immutable hash and sufficient access for audit.

Version 0.1 is expected to change. A change that alters a hypothesis, treatment,
primary metric, exclusion rule, or release gate increments the specification and
records the decision; it does not silently overwrite the history of a completed
run.

