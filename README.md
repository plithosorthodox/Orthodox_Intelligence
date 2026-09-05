# Orthodox Intelligence

Orthodox Intelligence (OI) is the research and engineering program behind the
Orthodox configuration of **Uvaha**, a local-first AI application. The first
integrated model configuration is **Sofiia v0.1**: OLMo 2 7B Instruct provides
the language/reasoning substrate and the versioned Plithos corpus supplies
retrieved Orthodox evidence with resolvable provenance.

The repository now includes the verified English Plithos evidence package,
deterministic multi-concept retrieval, relevance and coverage checks,
deterministic Old/New Calendar support, a loopback-only OLMo runtime adapter,
and claim-linked source display. Exact-text requests still bypass free-form
generation. The browser shell now has accountless, switchable chat sessions
with bounded local conversational context, local archive/restore, and confirmed
deletion. An optional Brave Search
evidence connector can look beyond the local corpus when the user selects
Automatic sources; answer generation remains local. Model weights are not
bundled. The repository does **not** yet contain a production Ethical Learning
Framework (ELF), a frozen quantized model artifact, or an application ready for
pastoral or public release.

## Names and boundaries

- **Uvaha** is the application/product name.
- **Sofiia v0.1** is the first integrated model configuration.
- **OLMo 2 7B Instruct** is Sofiia v0.1's selected language/reasoning substrate.
- **Plithos** is the versioned evidence and retrieval system; in v0.1 its content
  is retrieved at inference rather than baked into the model weights.
- **Orthodox Intelligence** remains the research/program lineage and Orthodox
  system architecture.

These names do not collapse the technical layers. Substrate weights, Plithos
corpus, future ELF text, retrieval settings, verifier, and application version
remain independently versioned and testable.

## The design in one sentence

OI separates four things that must not be allowed to blur together:

1. a trained behavioral substrate;
2. a short, explicit, versioned Orthodox ELF;
3. an on-device Plithos evidence store; and
4. deterministic verification and product boundaries.

```mermaid
flowchart TD
    Q["User question in Uvaha"] --> B["Boundary and intent checks"]
    B --> R["Local concept planning and Plithos retrieval"]
    R --> G{"Relevant local coverage?"}
    G -->|yes| M["Sofiia: local OLMo generation"]
    G -->|no; Automatic only| W["Optional Web evidence"]
    W --> M
    M --> V["Quote, citation, and identity verification"]
    V --> A["Verified answer with numbered sources or abstention"]
```

Sofiia is not presented as a Christian, a member of the Church, clergy, a
spiritual father, or a substitute for sacramental and pastoral life. It is an
artificial system whose Orthodox factual support is tied to identifiable Plithos
evidence.

## Repository map

- `docs/OI_RESEARCH_AND_TRAINING_SPECIFICATION_v0.1.md` - controlling v0.1
  research specification.
- `docs/ARCHITECTURE.md` - component boundaries and offline inference path.
- `docs/EVALUATION_PROTOCOL.md` - factorial experiment and release evaluation.
- `docs/DATA_AND_PROVENANCE.md` - corpus, rights, lineage, and contamination rules.
- `docs/ELF_REVIEW_PROTOCOL.md` - process for producing a production ELF.
- `docs/THREAT_MODEL.md` - anticipated failures and mitigations.
- `docs/ROADMAP.md` - staged work and exit criteria.
- `docs/DECISION_LOG.md` - decisions already made and their scope.
- `docs/OPEN_QUESTIONS.md` - matters intentionally not guessed in v0.1.
- `docs/MODEL_CARD_TEMPLATE.md` - evidence required for any model candidate.
- `config/model_olmo2_7b_instruct.v1.json` - selected OLMo 2 substrate manifest.
- `config/model_sofiia.v0.1.json` - integrated Sofiia v0.1 model manifest.
- `config/plithos_corpus.v1.json` - pinned Plithos evidence manifest.
- `schemas/` - machine-readable records for corpus, training, evaluation, and
  release manifests.
- `config/acceptance_criteria.v0.1.json` - provisional measurable gates.
- `tools/check_repository.py` and `tests/` - dependency-free repository checks.
- `prototype/` and `oi_prototype/` - Uvaha browser prototype and local retrieval,
  optional Web evidence, policy, verifier, HTTP, and model-runtime components.
- `evaluation/` - development behavioral suite and runtime-neutral forced-choice
  scoring contract.

## Run Uvaha in evidence-only mode

Python 3.10 or later is sufficient. No packages need to be installed for the
retrieval-only path.

```bash
python tools/serve_prototype.py
```

Then open `http://127.0.0.1:8765`.

## Run Sofiia v0.1 with a local model process

The development adapter accepts only an explicitly configured loopback
OpenAI-compatible llama.cpp origin. It has no remote fallback.

```bash
python tools/serve_prototype.py --model-endpoint http://127.0.0.1:8080
```

The selected OLMo weights must already be running in that local process. This
repository does not download or bundle them. The next model-artifact step is to
freeze the exact upstream revision, conversion/quantization, tokenizer, and
local weight hash before measured experimentation.

## Optionally allow Web sources

Web search is off unless both `--web-search` and a Brave Search API key are
provided. It is used only when the user chooses **Automatic** and the local
library does not sufficiently cover the question. The provider returns evidence;
it never generates the answer.

```bash
read -s UVAHA_BRAVE_API_KEY
export UVAHA_BRAVE_API_KEY
python tools/serve_prototype.py --model-endpoint http://127.0.0.1:8080 --web-search
```

Automatic mode sends bounded search terms to Brave Search. A Brave Search API
account is required, use may incur charges under that account's plan, and the
standard service may retain queries under its current policy. Returned results
are not added to Plithos, training data, or evaluation data. The server does not
cache a Web bundle, and Web source cards are filtered out before the answer is
saved in a chat's browser `localStorage`. A saved answer may retain a note that
the Web sources were transient, but not their result bodies or source metadata.
Leave off `--web-search` or choose **Local only** for no outbound search
requests. Recent chat turns may help local retrieval and generation, but only
the current question—not conversation history—is eligible for Web search. See
`docs/PROTOTYPE.md` for the full boundary.

## Selected model substrate

The project owner selected `allenai/OLMo-2-1124-7B-Instruct` as the reference
stock substrate. `oi_prototype/model_runtime.py` provides the development-only
loopback adapter; `oi_prototype/grounded_generation.py` packs retrieved Plithos
evidence into a strict generation contract and performs deterministic citation
and quotation checks. One bounded correction is permitted after verification
failure; a second failure becomes an abstention.

The current structured contract links each generated claim to its cited evidence
and the interface renders compact numbered sources. This is not yet a semantic
entailment verifier. The deterministic gate proves citation membership, claim-to-
source linkage, and exact quotation provenance; broader unsupported-claim
detection remains open pending a labeled claim-support evaluation and a separately
reviewed verifier.

## Running it on Windows

`docs/COMMANDS.md` is the short command reference for day to day use.

See `docs/RUNNING_ON_WINDOWS.md` for a from-nothing setup: the local model
server, the corpus, and Uvaha itself.

## Validate the scaffold

```bash
python tools/check_repository.py
python tools/run_evaluation.py --fail-on-any
python -m unittest discover -s tests -v
```

## Current status

Uvaha now has a chat-first research interface. It retrieves distinct concepts,
rejects incidental local matches, can synthesize across multiple sources, and
shows claim-linked numbered sources after verification. Optional Web evidence is
available only when configured and selected; local-only operation remains fully
functional. Separate chats can be created, selected, archived/restored, and
deleted. Messages are saved accountlessly in this browser's `localStorage`,
which is not encrypted by Uvaha and may be exposed to anyone or software with
access to the browser profile; browser clearing, quota errors, or private-mode
policies can also remove or prevent saved chats. Self-contained packaging,
production ELF work, semantic claim verification, and target-device
performance testing remain future increments.
