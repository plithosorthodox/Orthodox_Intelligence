# Open Questions

These questions are unresolved on purpose. An answer is recorded in
`DECISION_LOG.md` and removed here only when it is no longer open.

## Blocking Phase 0

1. Which phones/tablets and operating-system versions define the first supported
   device envelope?
2. Who fills the source-check, native-language, ecclesial, privacy, security, and
   statistical review roles, and what constitutes approval for each?
3. What trademark, domain, app-store, and naming-collision review is required
   before **Uvaha** and **Sofiia** are used in a public release?
4. Which original research artifacts may be stored in this private repository,
   which require a separate restricted archive, and which may be published?
5. What rights analysis governs each Plithos collection when it is redistributed
   inside a mobile application?
6. Which outcomes are primary in the pilot, and what evidence will ratify or
   replace the provisional thresholds?

## Corpus and retrieval

1. What is the minimum useful offline collection and language set for the first
   prototype?
2. Which source classes require exact display bytes, and which permit normalized
   search views?
3. How should conflicting jurisdictional calendars and practices be displayed
   without inventing a universal resolution?
4. Is a local embedding index worth its storage and multilingual cost relative to
   full-text plus metadata retrieval?
5. How will corpus updates be signed, distributed, rolled back, and retained for
   reproducibility?

## Model and training

1. What maximum package size, peak memory, time to first token, token rate, battery
   cost, and sustained thermal behavior are acceptable?
2. Which exact OLMo revision, tokenizer, conversion path, quantization, and local
   artifact hashes define the first reproducible Sofiia v0.1 experiment?
3. Which parameter-efficient method is most stable after mobile quantization?
4. How much Plithos-derived content, if any, belongs in weight training rather
   than retrieval?
5. How will native-language reviewers evaluate languages not read by the core
   engineering team?
6. What deterministic or measured claim-support/entailment gate is sufficient
   before generated Orthodox prose is treated as product-ready rather than a
   research prototype?
7. How will the complete OLMo 2 chat request, correction, chat-template
   overhead, and completion reserve be counted with the pinned tokenizer? The
   current 9,000-byte proxy is tested for deterministic size but is not a proof
   that every input remains inside the 4,096-token context.

## Product

1. How should local, switchable chat sessions be encrypted and indexed; what is
   the exact distinction between reversible archive and permanent deletion; and
   how are deleted sessions excluded from backups, crash reports, and operating-
   system cloud synchronization? The prototype's browser `localStorage` is not
   encrypted. It retains messages and displayed local-corpus excerpts, while
   Web source bodies and metadata are removed before persistence.
2. What emergency-response policy applies across supported jurisdictions and
   languages?
3. Will optional update checks be offered, and can they remain completely
   separated from question content and analytics?
4. What visible language communicates review status, limitations, and the
   distinction between general information and pastoral judgment?
5. Which managed identity provider, sign-in methods, deletion path, and recovery
   policy satisfy the supported platforms without creating a project-owned
   password liability?
6. Does guest mode include the full Uvaha Explorer capability, and what requires
   an account before payment or connector use?
7. Does an expired entitlement retain indefinite use of the last installed local
   version, and which services or updates stop?
8. Which body may verify a clergy or church-worker role, how is the named verifier
   displayed, and when does the verification expire?
9. Which connector is piloted first, with what minimum OAuth scope, confirmation
   rule, token storage, retention, and prompt-injection test?

## Optional Web evidence

1. Does a distributed Uvaha use bring-your-own Brave Search credentials, a
   project-managed relay, or a different provider? Who bears account setup,
   usage cost, abuse controls, and support in each design?
2. Do Brave Search's current retention policy and restrictions on caching,
   redistribution, model training, and evaluation receive legal/privacy approval
   for the intended users and jurisdictions?
3. Is an enterprise zero-data-retention arrangement required before sensitive
   user groups may enable Automatic sourcing, and what must the in-product notice
   say before the first outbound query?
4. What provider-neutral interface and acceptance suite are required so Uvaha
   can change search services without changing local generation, evidence
   identity, or offline behavior?
5. How should freshness, conflicting Web sources, publication dates, source
   quality, and retracted or changed pages be represented without implying that
   search rank is authority?
6. Which indirect-prompt-injection and malicious-content tests are required
   before Web evidence can move beyond provisional development status?
