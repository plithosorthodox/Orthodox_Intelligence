# Roadmap

Progress is gated by evidence, not by calendar dates. Work may proceed in parallel
only when it cannot contaminate a later blinded evaluation.

## Phase 0 - Specification freeze

Deliverables:

- ratified terminology and layer boundaries;
- named human review roles;
- initial target-device classes;
- research-evidence provenance register;
- pilot acceptance criteria; and
- approved rules for handling copyrighted and private material.

Exit: every blocking item marked Phase 0 in `OPEN_QUESTIONS.md` has a recorded
decision, and repository validation passes.

## Phase 1 - Reproducible Plithos export

Deliverables:

- deterministic export tool;
- corpus records matching `corpus-record.schema.json`;
- collection/language/rights inventory;
- transformation and exclusion report;
- SQLite full-text prototype; and
- immutable manifest with file hashes.

Exit: two clean exports from the same Plithos commit produce identical content
hashes, every shipped segment resolves to a source record, and redistribution
eligibility is known.

## Phase 2 - Benchmark construction and sealing

Deliverables:

- repaired forced-choice harness;
- development banks across every required domain;
- expanded general-capability controls;
- human scoring rubrics and reliability pilot;
- blinded bank with access separation; and
- preregistered analysis and exclusion plan.

Exit: development coverage is adequate, pilot scoring is reliable enough for the
chosen claims, and blinded hashes are sealed before training begins.

## Phase 3 - Stock-model device study

Deliverables:

- license-screened candidate list;
- unquantized and candidate-quantization baselines;
- S0 quality, latency, memory, storage, thermal, and battery results;
- context and retrieval-packing limits; and
- documented selection decision.

Exit: one primary and at least one fallback candidate meet the minimum on-device
envelope without OI-specific tuning.

## Phase 4 - Substrate and ELF pilots

Deliverables:

- audited training-data manifest;
- reversible S1 checkpoints;
- production ELF candidates following the proposition protocol;
- S/E ablations on development data; and
- contamination and memorization checks.

Exit: at least one S1 and one E1 candidate justify confirmatory evaluation without
crossing pilot capability or critical-failure limits.

## Phase 5 - Confirmatory factorial experiment

Deliverables:

- all eight S/E/R conditions;
- raw and analyzed results;
- uncertainty and interaction estimates;
- failure taxonomy;
- deviations log; and
- independent reproduction where feasible.

Exit: the owner records whether hypotheses were supported, unsupported, or
indeterminate. A failed hypothesis is a valid research result and is not rewritten
as a product success.

## Phase 6 - Integrated offline prototype

Deliverables:

- local mobile shell;
- corpus installer and citation viewer;
- retrieval, ELF loading, inference, and verification;
- accessibility and multilingual behavior;
- airplane-mode, privacy, and device tests; and
- model card and release manifest draft.

Exit: the exact integrated candidate meets frozen gates on target hardware.

## Phase 7 - Review and release decision

Deliverables:

- source, language, ecclesial, privacy, security, and license review records;
- residual-risk statement;
- reproducible signed artifacts;
- correction and rollback procedure; and
- explicit owner authorization.

Exit: release, limited pilot, further research, or no release is recorded as a
decision. Nothing ships merely because the engineering work is complete.

