# Data and Provenance

## Principle

Every OI output must be traceable to what changed the model, what governed the
model, and what evidence the model saw. Those are three different lineages.
An optional Web result is inference-time evidence, not corpus membership or a
new data class.

## Required registers

The project will maintain immutable manifests for:

- source artifacts and research evidence;
- each Plithos corpus export;
- training and development datasets;
- the sealed evaluation bank;
- every training run and resulting checkpoint; and
- each integrated application release.

Manifests use SHA-256 content hashes. A filename, branch name, web address, or
latest-version label is not an immutable identity.

## Corpus inclusion

A distributable corpus record requires:

- stable record and segment IDs;
- collection and source type;
- language and script where known;
- title, author, translator, edition, and publication data when applicable;
- source locator and retrieval date where applicable;
- rights status and the basis for that status;
- Plithos version or commit;
- exact content hash;
- transformation history; and
- review status.

Unknown metadata is represented as unknown, not inferred from nearby records.
Content without sufficient redistribution rights may inform private research only
when lawful, and it must not enter a distributable package.

## Source classes

Source classes exist to prevent accidental conflation, not to automate a final
theological hierarchy:

- Scripture;
- liturgical text;
- council or canonical source;
- patristic work;
- hagiography or synaxarion;
- calendar and jurisdictional data;
- historical or scholarly reference;
- Plithos editorial explanation;
- glossary or interface metadata; and
- product policy.

Reviewers may add authority scope and qualifications. Retrieval similarity alone
never supplies them.

## Request-scoped Web evidence

When explicitly enabled, the provisional Web provider may return source chunks
for a single question after local retrieval is found insufficient. Each admitted
chunk carries a request-local ID, content hash, source URL, title, provider
identity, and retrieval time, with publication time when supplied. These fields
make the evidence shown for that answer inspectable; they do not grant the page a
Plithos review status or establish that its claims are true.

Web evidence follows a separate lifecycle from the governed corpus:

- the provider response bundle remains in memory only for the request that
  retrieved it and is not server-cached;
- it is not installed as a corpus or merged into a Plithos manifest;
- it is not admitted to training, development, evaluation, or research archives;
- live results are not used to train, grade, benchmark, or compare models; and
- tests use fixed, handcrafted provider responses rather than live search data.

The browser prototype is a separate persistence boundary: before a Web-backed
answer is saved to a local chat, Web-origin source cards are filtered from the
serialized assistant message. A reopened chat can retain the answer text and a
note that its Web sources were transient, but not the Web result bodies or source
metadata. This filtering is a persistence constraint, not corpus provenance or a
provider cache. Deleting the chat removes it from the stored session state, but
cannot guarantee removal from browser backups, exports, screenshots, extensions,
or other copies outside that state.

This separation is required both for experimental integrity and because the
current provider terms restrict persistent caching, redistribution, and use in
model training or evaluation. A later governed import of material first found on
the Web would be a separate acquisition and review process with its own identity,
rights basis, hashes, transformations, and approvals.

The search query itself leaves the device. Uvaha bounds its length and does not
request location context by default, but it does not make a sensitive question
anonymous. Under the standard Brave Search API service, queries may be retained
for up to 90 days for billing and troubleshooting. The API key is read by the
local server from its environment, is never part of the evidence record, and must
not appear in the repository, browser payloads, logs, screenshots, or support
bundles. Account, cost, retention, and provider-policy acceptance are product
decisions rather than corpus provenance.

## Transformations

Every transformation from source to segment must be reproducible. The log records
normalization, extraction, de-duplication, language handling, segmentation, and
indexing code versions. Display text remains distinct from search-normalized text.
No normalization may silently change sacred wording, diacritics, punctuation, or
translator choices in what the user sees.

## Dataset separation

Training, development, and locked evaluation records use disjoint IDs and
near-duplicate screening. Semantic similarity review supplements exact hashes.
Once a locked item or its answer is exposed to a training-data generator, prompt
designer, or tuning process, it is retired from confirmatory evaluation.

Synthetic records identify:

- source evidence;
- generating model and prompt hash;
- critic or filtering process;
- human review status; and
- every accepted revision.

An evaluator model may flag or rank examples, but may not be the sole basis for
claiming theological correctness.

## User data

User conversations are not project training data. The server does not retain
conversation history, while the current accountless browser prototype stores
switchable, archivable, and deletable sessions in browser `localStorage` by
default. That storage is not encrypted by Uvaha and may be visible to software
or users with access to the browser profile. Archiving a local conversation must
not turn it into project data, and deletion must not silently leave a training,
evaluation, analytics, provider-cache, or other server-side copy behind. If the
product later offers voluntary data contribution, it requires separate,
plain-language consent and privacy design; it is not authorized by this
document.

For continuity, the browser sends at most six bounded prior turns to the
loopback server with the next question. The server and local model may use that
history as non-citable conversational context and do not retain it. The Web
provider receives only a bounded form of the current question; chat history,
prior answers, and local evidence are excluded from its request.
For local follow-up continuity, the browser may also return bounded segment-ID
and content-hash pairs from the most recent locally grounded answer. The engine
re-resolves them against the installed corpus and ignores missing, changed, or
Web-origin records; saved source prose is never promoted to factual evidence.

No repository artifact may contain private pastoral conversations, participant
identifiers, credentials, signing material, or device-specific personal data.

## Research evidence register

The following evidence families should be registered with immutable hashes before
formal claims are published:

1. the final dissertation and its embedded Appendix A artifacts;
2. the original and normalized Christian ELF instruments;
3. the forced-choice item banks and execution code;
4. the base/instruct raw run logs;
5. the combined result tables and analysis code; and
6. the text reporting the second experiment's findings.

Experimental files labeled not for dissertation use remain visibly excluded. A
later file with a similar title does not supersede an earlier instrument without
an explicit lineage record.

