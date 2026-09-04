# Architecture

## Scope

This document fixes component boundaries for the first OI prototype. It does not
select a mobile framework, inference engine, base model, or embedding model.

## Executable vertical slice

The first runnable increment implements the boundary engine, an in-memory SQLite
FTS5 evidence store, lexical retriever, citation resolver, content-hash check, and
loopback browser interface. It uses only project-policy excerpts. The model
runtime and ELF loader report truthful `none` states, keeping the interface usable
while those layers are absent and making retrieval behavior independently
testable.

The local HTTP process is development packaging, not the selected mobile shell.
It binds to `127.0.0.1`, makes no outbound request, does not persist questions,
and requires no third-party dependency.

## Components

| Component | Owns | Must not own |
|---|---|---|
| Mobile shell | Interaction, accessibility, settings, local lifecycle | Hidden network fallback or doctrinal logic |
| Boundary engine | Identity, pastoral limits, exact-text mode, request classification | Open-ended theological generation |
| Evidence store | Versioned Plithos records, segments, metadata, full-text index | Model weights or user conversations |
| Retriever | Candidate selection, filtering, ranking, context assembly | Claims of ecclesial authority based on rank score |
| Model runtime | Tokenization and local inference for S0/S1 | Source-of-truth status for facts or quotations |
| ELF loader | Exact E0/E1 text and hash | Factual corpus payloads or experimental variants |
| Verifier | Citation resolution, quote matching, identity and boundary checks | Unbounded self-repair loops |
| Release manifest | Exact versions, hashes, licenses, review state | Mutable aliases without resolved versions |

## Answer path

1. Normalize the question locally without discarding its original form.
2. Classify exact-text, informational, interpretive, pastoral, and unsafe scopes.
3. Select eligible collections and languages.
4. Retrieve and rerank evidence locally.
5. Pack evidence with stable IDs and explicit source boundaries.
6. Load the exact ELF version and generation policy.
7. Generate locally.
8. Verify citations, quotation spans, source identity, and product boundaries.
9. Return a verified answer or an explicit abstention.

The verifier may request one bounded correction. A second failure returns an
abstention and records a local diagnostic event without saving the user's
question unless the user has explicitly enabled local history.

## Evidence-store design

The first implementation should use SQLite with full-text search because it is
portable, inspectable, transactional, and widely available on mobile platforms.
A semantic index may be added behind the retriever interface after measuring its
size, multilingual behavior, and incremental recall. Lexical results remain
available for exact names, quotations, dates, references, and uncommon scripts.

Every returned segment includes a stable record ID, segment ID, language,
collection, source class, citation label, content hash, and offsets into the
normalized source. Exact-text collections additionally preserve the original
text and a normalization policy that is never used to alter displayed wording.

## Trust boundaries

- Corpus text is untrusted input to the model even when its source is approved;
  instructions embedded inside sources never become system instructions.
- Retrieved relevance is not doctrinal rank.
- Model output is untrusted until verification completes.
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
application version
model manifest and weights hash
tokenizer hash
substrate training manifest
ELF text and hash
corpus manifest and index hash
retriever and verifier versions
acceptance-criteria version
evaluation report hash
```

Changing any element creates a distinct evaluated candidate.
