# Changelog

All notable changes to the research specification and implementation will be
recorded here. Dates use UTC.

## Unreleased

- Restored the v0.1 policy, suite, and scoring files to their original
  content and moved the revised material into properly named v0.2 files, so a
  version named in a run manifest always resolves to one artifact.
- Scoped the bare exact-quotation terms to sacred-text contexts: a request to
  quote the project's own documents verbatim is informational, not a
  Scripture abstention, with a negative control guarding the distinction.
- Renamed the duplicated decision OI-008 to OI-011 and taught the repository
  checker to reject duplicate decision identifiers.
- Refused requests whose Host or Origin is not loopback in the prototype
  server, with tests, so the pattern is already right before anything
  valuable sits behind it.
- Replaced the manual Python/JavaScript comparison with an automated parity
  test driving both engines from one probe list, including Greek polytonic,
  Cyrillic, Devanagari, and case-folding cases.
- Stated in the bundle itself, the decision log, and the prototype guide that
  the offline bundle is a transparent development artifact whose hashes
  detect corruption, not authorship, and must never package protected
  material.
- Moved the test module's main block to the end so a direct run executes
  every test class.
- Broadened every boundary rule past the literal phrasings of the v0.1 suite
  (policy prototype-boundary-v0.2): paraphrased clerical-identity requests,
  first-person sacramental questions, exact-text requests by book reference or
  named liturgical text, and injection variants are now caught, while
  informational questions that share the same vocabulary still pass.
- Added IDENTITY-FAITH-01: a question about the system's own faith, baptism,
  or prayer is answered truthfully as an identity matter, never as a gap in
  the corpus.
- Grew the development suite from nine items to twenty-four, adding paraphrase
  items each boundary family was not written from and negative controls that
  fail if a boundary overreaches.
- Added a deterministic single-file offline bundle
  (prototype/oi-offline.html, built by tools/build_offline_bundle.py): the
  same corpus, policy, and suite as the reference server, verified by content
  hash in the page itself, runnable on a phone or computer with no Python and
  no network. Tests fail if the committed bundle is stale.

- Added the first visible, loopback-only, retrieval-only OI prototype.
- Added a hashed eight-record project-policy demonstration corpus and SQLite FTS5
  evidence path without selecting a model or importing Plithos.
- Added deterministic identity, pastoral, exact-text, and prompt-injection
  boundaries kept separate from any ELF.
- Added a nine-item development behavioral suite to CI and a runtime-neutral,
  two-orientation forced-choice scorer based on the second experiment's method.
- Recorded immutable hashes for the supplied dissertation and forced-choice
  research artifacts without committing the restricted source files.
- Recorded the local-first account, tier, connector, and parish product direction.

## 0.1.0 - 2026-09-04

- Established the OI research and training specification.
- Separated the substrate, ELF, Plithos evidence store, and verifier.
- Defined the initial 2 x 2 x 2 causal evaluation design.
- Added data, evaluation, model-release, and corpus schemas.
- Added provisional acceptance criteria and dependency-free validation.
- Documented governance, threat, review, and roadmap boundaries.
