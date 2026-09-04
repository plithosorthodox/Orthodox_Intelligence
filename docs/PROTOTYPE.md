# Executable Prototype

## What exists now

The executable research prototype is the first user-facing **Uvaha** shell. It
uses **Sofiia v0.1** as the selected integrated model identity: OLMo 2 7B Instruct
is the language/reasoning substrate and the installed Plithos package supplies
retrieved Orthodox evidence.

The local path now exercises:

- deterministic boundary and intent checks;
- verified Plithos SQLite full-text retrieval and citation resolution;
- deterministic Old/New Calendar support;
- content-hash verification;
- an optional loopback-only OLMo generation adapter;
- evidence packing with stable segment IDs;
- structured Sofiia output;
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
interface. Questions are held by the browser page for the current view and are
not written to disk or ordinary request logs.

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
fallback. Uvaha sends the question plus the bounded retrieved evidence package to
the local model process, then treats the returned draft as untrusted until the
verifier succeeds.

The current Sofiia generation contract requires strict JSON containing an answer,
retrieved segment IDs, registered direct quotations, and an abstention flag. A
non-abstaining answer must cite at least one retrieved segment. A registered quote
must be an exact substring of the identified evidence segment. If verification
fails, one correction is attempted. A second failure produces an abstention and
does not expose the rejected model draft.

This gate is deliberately described narrowly: it verifies citation membership
and quote provenance, not full semantic entailment of every sentence.

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
