# Executable Prototype

## What exists now

The executable research prototype is the first user-facing **Uvaha** shell. It
uses **Sofiia v0.1** as the selected integrated model identity: OLMo 2 7B Instruct
is the language/reasoning substrate and the installed Plithos package supplies
retrieved Orthodox evidence.

The local path now exercises:

- deterministic boundary and intent checks;
- verified Plithos SQLite full-text retrieval and citation resolution;
- deterministic concept-lane retrieval with relevance and concept-coverage gates;
- deterministic Old/New Calendar support;
- content-hash verification;
- an optional loopback-only OLMo generation adapter;
- evidence packing with stable segment IDs;
- structured Sofiia output;
- claim-linked numbered source display;
- deterministic citation-membership and exact-quotation checks;
- one bounded correction after a verification failure; and
- either a verified generated answer, verified evidence, or explicit abstention.

The prototype remains intentionally incomplete:

- model weights are not bundled or downloaded by this repository;
- the exact quantized artifact and tokenizer hashes have not yet been frozen for
  a measured run;
- no production ELF has been approved or loaded;
- semantic entailment of every generated claim is not yet deterministically
  verified;
- the loopback HTTP model adapter is development packaging, not the selected
  mobile production runtime; and
- no account, subscription, update, telemetry, or connector service is required
  for the core prototype.

## Run evidence-only Uvaha

Python 3.10 or later is the only requirement for the retrieval path.

```bash
python tools/serve_prototype.py
```

Open `http://127.0.0.1:8765` in a browser. The server binds only to the loopback
interface. The browser shell provides separate accountless chats: open the
**Chats** drawer to create a chat, switch between recent chats, archive or
restore a chat, and confirm deletion. Messages and displayed local-corpus source
excerpts are saved in that browser's `localStorage`, not on the server. This storage is
not encrypted by Uvaha and can be exposed to software or users with access to
the browser profile; clearing site data, storage quotas, or private browsing can
remove or prevent saved chats. Questions are not written to ordinary server
request logs.

Within a chat, up to six bounded recent turns are sent over loopback as local
conversation context. They may help deterministic local retrieval resolve an
explicitly referential follow-up and help the local model maintain continuity,
but they are labeled as context rather than evidence and cannot be cited. The
most recent local answer may also return saved segment IDs and content hashes;
the engine re-resolves them through the current corpus and uses only matching
corpus-owned titles to clarify retrieval. Saved title/excerpt text is not
trusted as evidence. The server does not persist those turns. Optional Web search receives only the
current bounded question, never this history. An assistant answer whose Web
sources were transient is excluded from later model context; the user's own
earlier turn may still help resolve the subject.

Without a model process, the interface can:

- retrieve Plithos evidence and display resolvable citations;
- search saints, prayers, Scripture, glossary material, and Library texts;
- use the deterministic Revised Julian/Julian calendar;
- return eligible exact text directly rather than reconstruct it;
- abstain when Plithos lacks evidence;
- enforce identity/pastoral boundaries; and
- run the development behavioral suite.

## Run Sofiia v0.1 generation

Start a compatible local llama.cpp model process separately with the selected
OLMo weights, then point Uvaha only at that loopback origin:

```bash
python tools/serve_prototype.py --model-endpoint http://127.0.0.1:8080
```

The adapter rejects non-loopback model endpoints. There is no remote inference
fallback. Uvaha sends the question, bounded recent local-chat context, and the
bounded retrieved evidence package to the local model process, then treats the
returned draft as untrusted until the verifier succeeds. Conversation context
is not factual evidence and cannot satisfy a citation.

The current Sofiia generation contract requires strict JSON containing an answer,
retrieved segment IDs, registered direct quotations, and an abstention flag. A
non-abstaining answer must cite at least one retrieved segment. A registered quote
must be an exact substring of the identified evidence segment. If verification
fails, one correction is attempted. A second failure produces an abstention and
does not expose the rejected model draft.

This gate is deliberately described narrowly: it verifies citation membership
and quote provenance, not full semantic entailment of every sentence. Semantic
entailment remains an open question pending a labeled claim-support evaluation
and a separately reviewed verifier.

## Optional Web evidence

Web evidence is disabled unless the server is started with `--web-search` and a
`UVAHA_BRAVE_API_KEY`. In the UI, **Automatic** first runs the deterministic
local retrieval and coverage checks. Only when local evidence is insufficient
does it send a bounded query to Brave Search's LLM Context endpoint. **Local
library only** performs no Web request, and the provider never generates the
answer: Sofiia generation and verification remain local. Provider failure leads
to an unavailable/abstention response rather than a changed local corpus or
remote generation fallback.

The Web response is untrusted, request-scoped evidence with source metadata; it
does not receive Plithos review status and is not imported into Plithos, model
training, development/evaluation banks, or ordinary server logs. Before an
Automatic-mode answer is saved in a chat, Web-origin source cards are filtered
from the browser `localStorage` payload. A reopened chat may show the answer
and a note that its Web sources were not stored, but not their result bodies or
metadata. This persistence constraint, plus provider account/key requirements,
possible usage charges, and provider retention/terms, is a user-visible privacy
boundary rather than an offline feature.

## Exact-text requests

Exact Scripture or other eligible exact-text requests remain outside ordinary
free-form generation. The evidence store resolves the requested text and returns
the verified source bytes; Sofiia does not reconstruct unavailable sacred text
from model memory.

## Run the single-file demonstration

`prototype/oi-offline.html` remains the original transparent demonstration bundle.
It is **not** the Sofiia runtime and does not package Plithos protected material,
model weights, production ELF material, or locked evaluation content. It is
generated from its governing demonstration inputs by:

```bash
python tools/build_offline_bundle.py
```

The generated bundle remains useful for deterministic boundary/retrieval parity
tests, but it must not be mistaken for the Uvaha/Sofiia product packaging model.

## Run the automated checks

```bash
python tools/run_evaluation.py --fail-on-any
python tools/check_repository.py
python -m unittest discover -s tests -v
```

To retain a local JSON report without committing it:

```bash
python tools/run_evaluation.py --fail-on-any --output results/prototype.json
```

## Next executable increment

Freeze and run an actual local OLMo artifact behind the adapter, recording the
exact upstream revision, conversion/quantization, tokenizer, weight hash,
decoding settings, hardware, memory use, and latency. Once a reproducible local
artifact is running, evaluate Sofiia v0.1 on the existing development banks and
add claim-support/entailment checks before treating generated Orthodox prose as a
candidate product behavior.
