# Decision Log

This file records durable decisions. Reversals append a new decision and mark the
earlier one superseded; history is not rewritten.

## OI-001 - Separate disposition, constitution, and knowledge

- **Date:** 2026-09-04
- **Status:** Accepted for v0.1
- **Decision:** Keep substrate weights, ELF text, and Plithos evidence as distinct,
  independently versioned layers, with deterministic verification as a fourth
  boundary.
- **Reason:** The OEDMF theory and forced-choice findings indicate that upstream
  training and runtime frameworks have different effects. Retrieval answers a
  third question: what evidence is available.

## OI-002 - Local-first core

- **Date:** 2026-09-04
- **Status:** Accepted for v0.1
- **Decision:** Core inference, retrieval, citation, verification, and settings
  work without a network connection; user content is not sent to a remote model.
- **Reason:** This is the defining privacy and availability property of OI.

## OI-003 - Truthful artificial identity

- **Date:** 2026-09-04
- **Status:** Accepted for v0.1
- **Decision:** OI may reason under an Orthodox-informed framework but never claims
  personal faith, spiritual faculties, sacramental membership, or clerical and
  pastoral authority.
- **Reason:** A useful Orthodox tool does not need a false human or ecclesial
  persona.

## OI-004 - Plithos remains evidence, not model memory

- **Date:** 2026-09-04
- **Status:** Accepted for v0.1
- **Decision:** Exact texts and substantive Orthodox factual support resolve to a
  versioned Plithos-derived corpus even if some corpus material is used during
  training.
- **Reason:** Weights do not provide stable quotation, provenance, correction, or
  citation.

## OI-005 - Full S/E/R ablation

- **Date:** 2026-09-04
- **Status:** Accepted for v0.1
- **Decision:** Evaluate all eight combinations of substrate, ELF, and retrieval.
- **Reason:** The design isolates contribution and interaction instead of crediting
  the integrated system as a black box.

## OI-006 - No model or runtime selected in v0.1

- **Date:** 2026-09-04
- **Status:** Accepted for v0.1
- **Decision:** Select a model only after license screening and measurement on
  representative target devices.
- **Reason:** Current popularity and desktop benchmark rank do not establish
  mobile fit, redistributability, or quantized behavior.

## OI-007 - Historical ELFs are research instruments

- **Date:** 2026-09-04
- **Status:** Accepted for v0.1
- **Decision:** Preserve original, normalized, and special-test ELFs with lineage,
  but create the production candidate through proposition-level source and human
  review.
- **Reason:** Experimental utility does not itself confer doctrinal or production
  authority.

## OI-008 - Local-first product with an optional control plane

- **Date:** 2026-09-04
- **Status:** Accepted direction; implementation details open
- **Decision:** Preserve a fully offline core while allowing separately disclosed
  network services for identity, entitlements, signed-update discovery,
  user-authorized connectors, verified roles, and parish administration. A
  network service does not receive questions or perform model inference by
  default.
- **Reason:** Accounts, updates, subscriptions, and external applications require
  connectivity, but they do not require surrendering local inference or private
  conversation content.

## OI-009 - Product tiers do not alter integrity boundaries

- **Date:** 2026-09-04
- **Status:** Accepted direction
- **Decision:** Citations, quotation fidelity, truthful identity, uncertainty,
  and pastoral limitations apply to every tier. Paid and verified tiers may add
  capability, depth, workflow, integration, and organization controls, but do not
  purchase greater truth or spiritual authority.
- **Reason:** Safety and evidentiary integrity are properties of the product, not
  premium benefits.

## OI-010 - Start with an executable retrieval-only slice

- **Date:** 2026-09-04
- **Status:** Accepted for the first prototype
- **Decision:** Implement the visible question, boundary, retrieval, citation,
  verification, and evaluation path before selecting a model or importing
  Plithos. The demonstration corpus contains only hashed project-policy excerpts,
  and the interface reports that no model or ELF is loaded.
- **Reason:** This produces something testable now without merging the four
  independently measured layers or bypassing device, license, provenance, and
  review decisions.

## OI-011 - The offline bundle is a generated artifact, never edited by hand

- **Date:** 2026-09-04
- **Status:** Accepted for v0.1
- **Decision:** `prototype/oi-offline.html` is produced only by
  `tools/build_offline_bundle.py` from the same corpus, boundary policy, and
  development suite the reference server reads. The build is deterministic,
  the tests fail when the committed file is stale, and the page verifies every
  record against its content hash before showing it. Its retrieval ranking is
  a simpler scorer than the reference SQLite path and the page says so.
- **Reason:** A file people copy to phones will drift from the repository
  unless the repository refuses to let it. Generating it from the governing
  inputs keeps one policy and one corpus, however many copies of the page
  exist.
- **Limit:** The bundle is a transparent development artifact: everything in
  it is meant to be read, and its embedded hashes detect corruption, not
  authorship. Production ELF material, locked evaluation data, model weights,
  and protected corpus material must never be packaged this way; a protected
  distribution requires a publisher signature anchored outside the file and a
  separate packaging decision.
