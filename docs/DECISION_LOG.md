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
- **Status:** Superseded in part by OI-012; runtime and device-fit requirements remain
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

## OI-012 - OLMo 2 7B Instruct is the reference substrate

- **Date:** 2026-09-04
- **Status:** Accepted for v0.1 development; supersedes OI-006 only as to model family
- **Decision:** Use `allenai/OLMo-2-1124-7B-Instruct` as OI's reference stock
  substrate (S0) and starting model family for subsequent OI-specific experiments.
  Do not bundle weights in this repository. Freeze the exact upstream revision,
  converted/quantized artifact hash, tokenizer, and decoding settings before any
  measured run. Production runtime and quantization remain unselected until
  representative-device testing.
- **Reason:** The project owner's completed forced-choice experiment placed OLMo 2
  7B Instruct among the strongest instruction-tuned local models tested. Ai2 also
  publishes the model's training data, code, recipes, checkpoints, and evaluation
  artifacts, making the substrate unusually inspectable for OI's research goals.
- **License and privacy:** The selected OLMo 2 checkpoint is Apache-2.0 licensed.
  The first development adapter targets the MIT-licensed llama.cpp runtime because
  current upstream llama.cpp supports OLMo 2 and can run an OpenAI-compatible
  server locally. The adapter accepts loopback HTTP only and provides no remote
  inference fallback. This development choice does not select llama.cpp as the
  eventual mobile production runtime.

## OI-013 - Uvaha is the app and Sofiia v0.1 is the first integrated model configuration

- **Date:** 2026-09-04
- **Status:** Accepted for v0.1 development
- **Decision:** Use **Uvaha** as the application/product name. Use **Sofiia v0.1**
  for the first integrated model configuration: OLMo 2 7B Instruct as the local
  language/reasoning substrate with the versioned Plithos evidence system
  supplied through retrieval. Keep **Orthodox Intelligence** as the research and
  engineering lineage and **Plithos** as the evidence/corpus system.
- **Boundary:** In Sofiia v0.1, Plithos is not silently merged into the OLMo
  weights. The substrate, evidence package, future ELF, verifier, and application
  remain independently versioned even though the user-facing model has one name.
- **Reason:** The product name needs to be broader than the Orthodox research
  program while retaining a precise technical identity for the first model and
  preserving the provenance architecture already established.

## OI-014 - First Sofiia generation is evidence-packed and verifier-gated

- **Date:** 2026-09-04
- **Status:** Accepted for v0.1 development
- **Decision:** When a local OLMo runtime is explicitly connected, the prototype
  retrieves Plithos evidence first, supplies only that evidence as the Orthodox
  factual context for Sofiia, requires a structured JSON generation contract,
  and verifies cited segment membership and exact direct quotations before a
  generated answer is displayed. One bounded correction is allowed after a
  verification failure; a second failure becomes an abstention.
- **Limit:** This deterministic verifier does not yet prove semantic entailment of
  every generated claim. Unsupported-claim/entailment detection remains a
  separate engineering and evaluation problem and must not be overstated.
- **Privacy:** The development model adapter accepts loopback HTTP only and has no
  remote fallback. A generated prompt may be sent to the local model process on
  the same device, but not to a remote inference service.

## OI-015 - Reject vacuous answers before treating them as verified

- **Date:** 2026-09-05
- **Status:** Accepted for v0.1 development
- **Decision:** A non-abstaining Sofiia draft must clear a deterministic
  non-vacuity floor in addition to the existing citation and quotation checks.
  The verifier rejects bare literals and punctuation fragments, one-word
  fragments, and answers that merely repeat a cited segment identifier. A
  failure uses the existing single bounded correction; a repeated failure
  becomes an abstention.
- **Reason:** A live OLMo 2 1B run produced outputs such as `true` and `{` that
  carried genuine segment identifiers and exact registered quotes, so the
  structural verifier accepted them even though they conveyed no usable answer.
  Citation integrity is necessary but does not establish that an answer says
  anything.
- **Limit:** This floor detects obvious vacuity only. It does **not** prove
  semantic entailment, factual completeness, or claim-level support. OI-014's
  entailment limitation remains in force and requires separate engineering and
  evaluation work.

## OI-016 - Keep grounded answers bounded enough to finish

- **Date:** 2026-09-05
- **Status:** Accepted for v0.1 development
- **Decision:** A non-abstaining Sofiia answer is capped at 120 words. The model
  prompt asks for normally 1-3 concise sentences and for the JSON object to close
  well before the generation ceiling. The verifier rejects a longer completed
  answer. A failed draft is excerpted to at most 1,200 characters before being
  placed into the one allowed correction request.
- **Reason:** Live constrained decoding showed that a grammar can keep every
  generated token syntactically legal and still end with invalid JSON when the
  model reaches `max_tokens` mid-string. Simply increasing the output ceiling
  increases latency and does not create a completion guarantee. Concision gives
  the object room to close, while capping the rejected draft prevents a failed
  first attempt from inflating the correction prompt.
- **Limit:** The 120-word cap is a v0.1 operational bound, not a claim that every
  Orthodox question can be answered completely in that space. The answer may
  abstain when the available evidence or bounded format is insufficient.

## OI-017 - Fit evidence to the reference substrate's trained context

- **Date:** 2026-09-05
- **Status:** Accepted for v0.1 development
- **Decision:** Grounded generation retains an 8,000-character upper bound for
  complete evidence records and also fits the entire serialized request under
  a 9,000-byte prompt proxy. That full-request budget includes instructions,
  question, evidence text and metadata, source locators, and enough room for a
  bounded correction. It is intended to leave room for 700 output tokens plus
  396 safety tokens in OLMo 2's 4,096-token context. A complete record that does not fit is
  skipped rather than silently truncated under its full-record provenance hash.
  The correction excerpt is reduced further when necessary. JSON failures that
  end in an incomplete object or string receive a distinct truncation result;
  other invalid JSON receives a malformed-output result.
- **Reason:** OLMo 2 7B has a 4,096-token trained context. The former 18,000-
  character evidence ceiling could consume roughly 4,500 tokens before system
  instructions, the question, correction material, or the 700-token output
  allowance. Preserving whole evidence records also avoids presenting a partial
  source under the full record's provenance hash.
- **Limit:** UTF-8 byte count at three bytes per estimated prompt token is a
  deterministic engineering proxy, not a conservative proof and not
  tokenizer-exact accounting. Token-dense ASCII/adversarial inputs and the
  runtime's chat template can exceed that estimate. Exact accounting with the
  pinned OLMo tokenizer (or a demonstrably safe smaller bound) remains required
  before this may be described as a guaranteed 4,096-token fit. Apparent
  truncation is inferred from an incomplete JSON prefix because the current
  runtime seam does not expose a completion finish reason.

## OI-018 - Require concept coverage and claim-linked sources

- **Date:** 2026-09-05
- **Status:** Accepted for v0.1 development
- **Decision:** Plan compound questions as deterministic concept lanes, retrieve
  each lane independently, and treat a local result as sufficient only when the
  requested concepts are covered by an appropriately diverse evidence set.
  Sofiia's generation contract represents the answer as one to three claims,
  each with its own retrieved source references; Uvaha renders those claims as
  prose with compact numbered citations.
- **Reason:** Whole-question lexical search returned several records for one
  Nicholas and none for Mary in a two-person comparison. It also matched
  unrelated patristic passages for ordinary questions about leaves and
  inflation. A nonempty result list is therefore not evidence that the corpus
  supports the question. Claim-level source links make the support relationship
  inspectable instead of presenting an undifferentiated citation list.
- **Limit:** Concept coverage and claim-to-source linkage are not semantic
  entailment proof. A labeled claim-support bank and a separately reviewed
  verifier remain necessary before claiming that every paraphrase or inference
  is entailed.

## OI-019 - Optional request-scoped Web evidence

- **Date:** 2026-09-05
- **Status:** Provisional development integration; legal/privacy review required
- **Decision:** Preserve the offline core and add a separately versioned Web
  evidence provider that is disabled unless explicitly configured. When the
  user selects Automatic sources and local retrieval is insufficient, Uvaha may
  send only a bounded search query to Brave Search's LLM Context endpoint, then
  perform answer generation locally. Returned chunks remain request-scoped,
  source-attributed, untrusted evidence and never enter Plithos, training data,
  evaluation archives, or ordinary logs. Brave Answers is not used.
- **Privacy and license impact:** Standard Brave Search API service may retain
  search queries for up to 90 days for billing and troubleshooting. An API key
  and account are required; credentials stay server-side and are not committed
  or exposed to the browser. Current terms restrict persistent result storage,
  redistribution, and use for model training or evaluation. Public distribution
  therefore requires owner/legal acceptance, an end-user privacy notice, and a
  decision between bring-your-own credentials and a managed relay.
- **Failure behavior:** Provider failure never changes the local corpus or model
  path. Uvaha returns a short unavailable response, and Local library only mode
  performs no outbound search request.

## OI-020 - Browser-local chat sessions

- **Date:** 2026-09-05
- **Status:** Accepted for v0.1 development
- **Decision:** Give the browser prototype separate accountless chat sessions
  stored in browser `localStorage`. Users may create and switch chats, archive
  and restore them, or confirm deletion. Session context is isolated by session
  ID; archive is reversible organization and deletion removes the session from
  the stored state. At most six bounded recent turns may return over loopback as
  non-citable context for local retrieval and generation. Only the current
  question is eligible for optional Web search; conversation history is never
  sent to the provider. A saved assistant answer whose Web sources expired is
  also excluded from later model context so it cannot become substitute
  evidence without a fresh search.
- **Continuity integrity:** A saved local source contributes only its segment ID
  and content hash. The loopback engine resolves that pair again through the
  currently installed corpus before using the corpus-owned title to clarify a
  referential retrieval query. Saved excerpts and titles are never promoted to
  evidence, mismatched hashes are ignored, and Web-origin sources are ineligible.
- **Privacy boundary:** Uvaha does not encrypt this storage. Anyone or any
  software with access to the browser profile may be able to read it, and
  browser clearing, quota limits, private browsing, backups, or extensions may
  affect retention. Deletion cannot guarantee removal from copies outside the
  stored session state. Sessions are not project training, evaluation,
  analytics, or server history.
- **Web-result constraint:** The Brave response bundle remains request-scoped
  and is not server-cached or imported into Plithos. Before a Web-backed answer
  is saved, Web-origin source cards are filtered from the assistant message. A
  reopened chat may retain the answer text and a note that the Web sources were
  transient, but not their result bodies or source metadata. This filtering is
  the required persistence constraint and must remain tested and disclosed.
