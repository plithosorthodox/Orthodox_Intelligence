# Repository instructions for AI agents

Read this file and the controlling research specification before changing the
repository. The specification is
`docs/OI_RESEARCH_AND_TRAINING_SPECIFICATION_v0.1.md`.

## Non-negotiable boundaries

- Keep the trained substrate, explicit ELF, retrieved evidence, and deterministic
  safeguards separately versioned and separately testable.
- Do not describe the model as Orthodox, Christian, conscious, spiritually
  discerning, clergy, or a substitute for a priest or spiritual father.
- Do not invent, paraphrase, modernize, silently correct, or fabricate Scripture,
  liturgical text, patristic text, hagiography, conciliar teaching, provenance,
  ecclesial consensus, or source metadata.
- Do not convert an experimental ELF into the production ELF without completing
  `docs/ELF_REVIEW_PROTOCOL.md`.
- Do not put evaluation-bank items, close paraphrases, labels, rationales, or
  expected answers into training or development data.
- Do not import Plithos content until an immutable export manifest records its
  version, file hashes, source type, language, and rights status.
- Do not add a model, dataset, library, runtime, telemetry service, or network
  dependency without recording the decision and its license/privacy impact.
- On-device and offline operation is the default. A network feature requires an
  explicit architectural decision and must not be silently introduced.
- A generated answer may summarize a source only when it distinguishes summary
  from quotation and preserves a resolvable citation.

## Working practice

- Make the smallest coherent change and update the documents, schemas, and tests
  that the change affects.
- Run `python tools/check_repository.py` and
  `python -m unittest discover -s tests -v` before committing.
- Record durable project decisions in `docs/DECISION_LOG.md`; record unresolved
  matters in `docs/OPEN_QUESTIONS.md` rather than guessing.
- Keep transient Claude/Codex status, token availability, handoffs, and check-in
  conversation in `plithosorthodox/plithos-agent-coordination`, not this corpus.
- Never commit credentials, private pastoral conversations, unredacted research
  participant data, model-provider tokens, signing keys, or device identifiers.
- Do not release, publish, deploy, or claim ecclesial review without explicit
  authorization from the project owner.

The project owner is the final product authority. Assertions presented as
Orthodox teaching additionally require the review path defined in the ELF and
data-governance documents; an AI agent cannot confer that status.

