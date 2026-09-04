# Architecture

## Scope

This document fixes component boundaries for the first OI/Uvaha prototype.
OLMo 2 7B Instruct is selected as the reference language/reasoning substrate and
Sofiia v0.1 names the first integrated model configuration. This document still
does not select a mobile framework, production mobile inference engine, final
quantization, or embedding model.

## Executable vertical slice

The runnable increment implements the boundary engine, the verified Plithos
SQLite FTS5 evidence store, lexical retriever, calendar package, citation
resolver, content-hash checks, loopback browser interface, optional local OLMo
runtime adapter, evidence packing, and deterministic citation/quotation
verification.

The same executable remains useful with no model process connected. In that
state it acts as an evidence navigator. When an explicitly configured loopback
model process is connected, Sofiia v0.1 may generate from the retrieved evidence
and the result is not displayed until the deterministic verifier passes it.

The local HTTP process is development packaging, not the selected mobile shell.
It binds to `127.0.0.1`, does not persist questions, and never accepts a remote
model endpoint. With Sofiia enabled, the Uvaha process may send the packed prompt
to a separately running model process on loopback only.

## Components

| Component | Owns | Must not own |
|---|---|---|
| Uvaha/mobile shell | Interaction, accessibility, settings, local lifecycle | Hidden network fallback or doctrinal logic |
| Boundary engine | Identity, pastoral limits, exact-text mode, request classification | Open-ended theological generation |
| Evidence store | Versioned Plithos records, segments, metadata, full-text index | Model weights or user conversations |
| Retriever | Candidate selection, filtering, ranking, context assembly | Claims of ecclesial authority based on rank score |
| Sofiia model runtime | Tokenization and local OLMo inference for selected substrate variants | Source-of-truth status for facts or quotations |
| ELF loader | Exact future ELF text and hash | Factual corpus payloads or experimental variants |
| Verifier | Citation resolution, quote matching, identity and boundary checks | Unbounded self-repair loops or claims of semantic proof not implemented |
| Release manifest | Exact versions, hashes, licenses, review state | Mutable aliases without resolved versions |

## Answer path

1. Normalize the question locally without discarding its original form.
2. Classify exact-text, informational, interpretive, pastoral, and unsafe scopes.
3. Select eligible collections and languages.
4. Retrieve and rerank evidence locally.
5. Pack evidence with stable IDs and explicit source boundaries.
6. Load the exact generation policy and, when approved later, the exact ELF.
7. Generate locally through the Sofiia runtime.
8. Verify cited segment membership, direct quotation spans, source identity, and
   product boundaries.
9. Return a verified answer or an explicit abstention.

The verifier may request one bounded correction. A second failure returns an
abstention. The current v0.1 verifier proves citation membership and exact quote
provenance; it does not yet prove that every prose claim is semantically entailed
by the cited evidence.

Exact-text requests remain a special path. Eligible Scripture or liturgical text
is retrieved directly from the evidence package rather than reconstructed by the
model.

## Evidence-store design

The first implementation uses SQLite with full-text search because it is
portable, inspectable, transactional, and widely available on mobile platforms.
A semantic index may be added behind the retriever interface after measuring its
size, multilingual behavior, and incremental recall. Lexical results remain
available for exact names, quotations, dates, references, and uncommon scripts.

Every returned segment includes a stable record ID, segment ID, language,
collection, source class, citation label, content hash, and source locator.
Exact-text collections additionally preserve source text and a normalization
policy that is never used to alter displayed wording.

## Model identities

The layers remain technically separate even though the user-facing model has a
single name:

- **Uvaha** is the application/product.
- **Sofiia v0.1** is the first integrated model configuration.
- **OLMo 2 7B Instruct** is Sofiia v0.1's selected substrate.
- **Plithos** is the versioned evidence package and retrieval system.
- **Orthodox Intelligence** is the research/program lineage and Orthodox system
  architecture.

`config/model_sofiia.v0.1.json` records that integration without claiming that
Plithos content has been baked into the OLMo weights.

## Trust boundaries

- Corpus text is untrusted input to the model even when its source is approved;
  instructions embedded inside sources never become system instructions.
- Retrieved relevance is not doctrinal rank.
- Model output is untrusted until verification completes.
- Citation membership is not itself proof that every generated claim is
  supported; semantic support remains an explicit open verification problem.
- Application metadata is not allowed to assert human review unless that status
  exists in the signed release manifest.
- Imported packages are verified before activation and never modify an existing
  installed version in place.

## Offline and privacy contract

The release build must complete its full core test suite with networking disabled.
No remote API, crash-reporting service, analytics SDK, font, web view, or content
URL may be required for core operation. Optional update checks, if later approved,
must be isolated, disclosed, user-controlled, integrity-checked, and unnecessary
for use of the installed model and corpus.

A loopback HTTP connection between the Uvaha development process and a local
model process is considered local inter-process transport, not a remote inference
service. The development adapter rejects non-loopback endpoints and has no remote
fallback.

Conversation history defaults to off. If enabled, it is local, deletable, and
excluded from training. Sensitive content is not written to ordinary diagnostic
logs. Backups and operating-system cloud synchronization require an explicit
product decision.

## Optional future control plane

The approved product direction permits a separately implemented control plane for
identity, entitlements, signed-update discovery, connector authorization,
verified organization roles, and parish administration. It never owns core model
inference or becomes a hidden fallback. Account identity, product entitlement,
resource permission, and verified role remain separate records. Detailed data
flows and provider selections require new decisions before implementation; see
`PRODUCT_ACCESS_PLAN.md`.

## Release unit

A runnable release resolves, at minimum:

```text
application version and product name
Sofiia model-configuration manifest
OLMo substrate manifest and weights hash
tokenizer hash
substrate training manifest
ELF text and hash when an ELF is active
corpus manifest and index hash
retriever and verifier versions
acceptance-criteria version
evaluation report hash
```

Changing any element creates a distinct evaluated candidate.
