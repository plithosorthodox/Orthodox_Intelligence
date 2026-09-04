# Data and Provenance

## Principle

Every OI output must be traceable to what changed the model, what governed the
model, and what evidence the model saw. Those are three different lineages.

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

User conversations are not project training data. Local history defaults to off.
If the product later offers voluntary data contribution, it requires a separate,
plain-language consent and privacy design; it is not authorized by this document.

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

