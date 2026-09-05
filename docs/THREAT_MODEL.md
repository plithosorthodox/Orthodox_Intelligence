# Threat Model

## Protected properties

OI must protect source fidelity, truthful identity, user privacy, evaluation
integrity, corpus integrity, reproducibility, general capability, and the boundary
between information and pastoral authority.

## Threats and required controls

| Threat | Example failure | Minimum control |
|---|---|---|
| Prompt injection | A retrieved page tells the model to ignore the ELF | Treat corpus as quoted data; isolate system instructions |
| Corpus poisoning | A modified bundle adds false teaching or instructions | Signed manifest, hashes, review state, immutable versions |
| Citation laundering | A true source is cited for a claim it does not support | Claim-to-span verification and human audit samples |
| Fabricated authority | The model invents a canon, saint, quotation, or consensus | Resolvable identifiers; abstain when evidence is absent |
| False persona | The assistant claims belief, ordination, or spiritual discernment | Critical identity tests and deterministic boundary text |
| Pastoral overreach | The model binds a conscience or substitutes for confession | Scope detection, clear limitation, useful referral |
| Sacred-text mutation | A remembered paraphrase is presented as Scripture | Exact-text retrieval and byte/normalized-span comparison |
| Framework overreach | One ELF principle suppresses reasoning on unrelated tasks | S/E/R ablation and separate capability gates |
| Sycophancy | User pressure makes the model validate a false premise | Contrastive training and adversarial evaluation |
| Evaluation leakage | Test items appear in training or prompt examples | Sealed bank, hashes, access separation, near-duplicate checks |
| Benchmark gaming | A model learns superficial labels or letter bias | Hidden items, mirrored choices, generative transfer tests |
| Language fallback | Non-English answers silently revert to English or wrong script | Per-language metrics, native review, fallback disclosure |
| Privacy leakage | Local conversations enter logs, analytics, or training | Browser-local disclosure; no telemetry, request logging, training, or server persistence |
| Local-history tampering | Browser storage changes a saved answer or source card | Treat restored history as untrusted, non-citable data; re-resolve local source ID/hash pairs against the current corpus; never promote saved prose to evidence |
| Search-query disclosure | A private question is sent outward without a clear choice | Local-only default; affirmative Automatic selection; bounded current-question query only |
| Search credential exfiltration | A provider redirect forwards the API key to another origin | Fixed HTTPS endpoint; reject redirects; keep credentials server-side |
| Web prompt injection | Retrieved Web text instructs the local model to ignore policy | Mark Web text as untrusted evidence; preserve system priority; verify citations |
| Web-result persistence | Provider result bodies enter saved chats, training, or evaluation | Request-memory-only bundle; filter Web source cards before local storage; fake fixtures in tests |
| Hidden network use | The app calls a remote model when local inference fails | Airplane-mode release test and dependency inspection |
| Supply-chain compromise | Model, index, or library differs from evaluated artifact | Release manifest, signature verification, reproducible build |
| Device compromise | Another process reads local history or model state | Platform storage controls, encryption decision, minimal retention |

## High-risk interaction classes

Medical emergencies, self-harm, abuse, criminal danger, and other immediate safety
matters require a product-level emergency response policy that remains helpful
without pretending to be clergy or a clinician. Its exact text and jurisdictional
behavior are open design decisions and must be evaluated separately.

Questions involving confession, penance, reception into the Church, sacramental
eligibility, individualized fasting dispensations, spiritual obedience, or
binding moral judgment must not be resolved as though OI possesses pastoral
authority. It may provide sourced general information and recommend speaking with
the appropriate priest or bishop.

## Residual risk

On-device operation reduces network exposure but does not make the system private
against a compromised device, screenshots, operating-system backups, or physical
access. Grounded generation reduces hallucination but does not prove that a
citation supports the model's exact inference. Human review reduces doctrinal
risk but does not create universal jurisdictional agreement. Release materials
must state these limits plainly.

## Security review triggers

A new review is required when the project changes the base model, corpus ingestion
path, update mechanism, networking, telemetry, local-history policy, encryption,
mobile framework, native inference runtime, signing process, or distribution
channel.

