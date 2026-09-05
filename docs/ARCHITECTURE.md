# Architecture

## Scope

This document fixes component boundaries for the first OI/Uvaha prototype.
OLMo 2 7B Instruct is selected as the reference language/reasoning substrate and
Sofiia v0.1 names the first integrated model configuration. This document still
does not select a mobile framework, production mobile inference engine, final
quantization, or embedding model.

## Executable vertical slice

The runnable increment implements the boundary engine, the verified Plithos
SQLite FTS5 evidence store, deterministic multi-concept query planning and
retrieval, relevance/coverage gating, citation resolution, content-hash checks,
a chat-first loopback browser interface, an optional local OLMo runtime adapter,
evidence packing, and deterministic claim/citation/quotation verification.

The same executable remains useful with no model process connected. In that
state it acts as an evidence navigator. When an explicitly configured loopback
model process is connected, Sofiia v0.1 may generate from the retrieved evidence
and the result is not displayed until the deterministic verifier passes it.

A separately configured Brave LLM Context provider may supply Web evidence. It
is disabled by default and is considered only when the user selects Automatic
sources and local retrieval is insufficient. The provider does not generate an
answer. Returned chunks are untrusted, request-scoped evidence passed to the same
local Sofiia generation and verification path.

The local HTTP process is development packaging, not the selected mobile shell.
It binds to `127.0.0.1` and never accepts a remote model endpoint. With Sofiia
enabled, the Uvaha process may send the packed prompt to a separately running
model process on loopback only. The optional search provider is the sole
non-loopback request in this increment and is visibly separated from model
inference. The browser shell stores its accountless chat sessions separately in
browser `localStorage`; this is client-side application state, not server-side
conversation storage.

## Components

| Component | Owns | Must not own |
|---|---|---|
| Uvaha/mobile shell | Interaction, accessibility, settings, local lifecycle | Hidden network fallback or doctrinal logic |
| Boundary engine | Identity, pastoral limits, exact-text mode, request classification | Open-ended theological generation |
| Evidence store | Versioned Plithos records, segments, metadata, full-text index | Model weights or user conversations |
| Query planner and retriever | Deterministic concept lanes, candidate selection, relevance/coverage checks, ranking, context assembly | Claims of ecclesial authority based on rank score or model-written query planning |
| Optional Web evidence provider | Bounded search request, source metadata, request-scoped evidence bundle | Answer generation, server-side result caching, corpus import, training/evaluation ingestion, or silent fallback |
| Sofiia model runtime | Tokenization and local OLMo inference for selected substrate variants | Source-of-truth status for facts or quotations |
| ELF loader | Exact future ELF text and hash | Factual corpus payloads or experimental variants |
| Verifier | Citation resolution, quote matching, identity and boundary checks | Unbounded self-repair loops or claims of semantic proof not implemented |
| Release manifest | Exact versions, hashes, licenses, review state | Mutable aliases without resolved versions |

## Answer path

1. Normalize the question locally without discarding its original form.
2. Classify exact-text, informational, interpretive, pastoral, and unsafe scopes.
3. Preserve exact-text requests on the direct corpus-resolution path.
4. Build deterministic concept lanes for an ordinary question, retrieve each
   lane locally, and test whether the selected set covers the requested concepts.
5. If local coverage is insufficient, stop in Local only mode. In Automatic
   mode, and only when a provider was explicitly configured, send a bounded
   search query to the Web evidence provider.
6. Combine eligible local evidence with request-scoped Web evidence, retaining
   stable IDs, content hashes, origin, provider, time, and source location.
7. Load the exact generation policy and, when approved later, the exact ELF.
8. Generate one to three concise claims locally through the Sofiia runtime,
   requiring each non-abstaining claim to name its supporting evidence refs.
9. Verify claim-to-source reference membership, direct quotation spans, source
   identity, and product boundaries.
10. Return verified prose with numbered sources, or an explicit abstention.

The verifier may request one bounded correction. A second failure returns an
abstention. The current verifier proves citation membership, structural
claim-to-source linkage, and exact quote provenance; it does not yet prove that
every prose claim is semantically entailed by the cited evidence. Semantic
entailment remains an open question pending a labeled claim-support evaluation
and a separately reviewed verifier.

Exact-text requests remain a special path and are unchanged by Web search.
Eligible Scripture or liturgical text is retrieved directly from the installed
evidence package rather than reconstructed by the model or fetched from the Web.

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
- Web text is untrusted input with no Plithos review status. Returned instructions
  remain evidence text and never become system or application instructions.
- Retrieved relevance is not doctrinal rank.
- Model output is untrusted until verification completes.
- Citation membership is not itself proof that every generated claim is
  supported; semantic support remains an explicit open verification problem.
- Application metadata is not allowed to assert human review unless that status
  exists in the signed release manifest.
- Imported packages are verified before activation and never modify an existing
  installed version in place.
- A Web result's URL, title, timestamp, and content hash identify what the request
  received; they do not establish truth, permanence, authorship, or review.

## Offline and privacy contract

The release build must complete its full core test suite with networking disabled.
No remote API, crash-reporting service, analytics SDK, font, web view, or content
URL may be required for core operation. Local only mode performs no outbound
search and the application remains useful when the optional provider is absent
or unavailable. Optional update checks, if later approved, must be isolated,
disclosed, user-controlled, integrity-checked, and unnecessary for use of the
installed model and corpus.

Enabling Web search changes the privacy boundary. Uvaha sends bounded search
terms to Brave Search only after the user selects Automatic and local evidence
is insufficient. No location context is requested by default. The API credential
is supplied to the local server from its environment and is neither committed
nor exposed to browser code. Under the standard provider service, query retention
may extend to 90 days for billing and troubleshooting. Provider terms, account
requirements, pricing, retention, and jurisdiction remain external dependencies
that require review before distribution.

Web results exist in an immutable request-scoped bundle long enough to resolve
and verify that answer. They are not written to the corpus, ordinary server
logs, training datasets, or evaluation archives. Web-origin source cards are
filtered before a chat is serialized; a saved answer may retain only a note that
its Web sources were transient. This is the local-chat persistence constraint
described below. Automated tests use handcrafted provider responses; live search
results must not become benchmark or training material.

A loopback HTTP connection between the Uvaha development process and a local
model process is considered local inter-process transport, not a remote inference
service. The development adapter rejects non-loopback endpoints and has no remote
fallback.

Chat sessions are local by default, switchable, archivable/restorable, and
deletable from the browser drawer. They require no account and are excluded from
training and analytics. The current prototype serializes session messages,
including displayed local-corpus source excerpts and metadata, to browser
`localStorage`. Web-origin source cards are filtered out before persistence; a
saved Web-backed answer retains only its answer text and a note that its Web
sources were not stored. That storage is not encrypted by Uvaha and is
accessible to software or users with access to the browser profile; browser
clearing, quota limits, and private mode can remove or prevent it. Sensitive
content is not written to ordinary server diagnostic logs. Archive is reversible
organization; delete is confirmed and removes the session from the stored state,
but it cannot retroactively erase browser or operating-system backups,
screenshots, exports, or copies outside that state. Cloud synchronization,
encryption, and stronger deletion guarantees remain explicit product decisions.

For a new turn, the browser may send up to six bounded recent turns back to the
loopback server. They are marked as conversation context, not evidence, and the
local model may not cite them. A deterministic referential-follow-up rule may
carry the last user subject into local retrieval. That history is excluded from
the Web-query derivation path, which receives only the current question.
Assistant turns whose Web sources were transient are excluded from subsequent
model context so expired provider material cannot silently become evidence.
For a local grounded answer, the browser may return up to four segment-ID/hash
pairs from the most recent assistant turn. The engine resolves them against the
current evidence store and accepts only hash-matching local records; it uses the
corpus-owned titles for referential retrieval and never trusts saved excerpts or
titles as evidence.

The Web provider's response bundle is request-scoped and is not cached by the
server or installed as corpus data. Web-origin source cards are also excluded
from the browser transcript before it is saved; the UI marks a saved answer when
its Web sources were transient. This filtering is the current Web-result
persistence constraint and must remain covered by tests and user-facing copy.

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
