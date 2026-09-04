# Executable Prototype

## What exists now

The first OI vertical slice is a dependency-free local application that can be
opened in a browser. It exercises the complete path from a question through a
deterministic boundary check, SQLite full-text retrieval, citation resolution,
content-hash verification, and either evidence or an explicit abstention.

It is intentionally not presented as a finished AI assistant:

- no language model or trained substrate has been selected or loaded;
- no production ELF has been approved or loaded;
- the eight-record demonstration corpus contains only exact excerpts from the OI
  research specification;
- no Plithos theological content has been imported; and
- no account, subscription, update, telemetry, or connector service exists.

That limit lets the interface, trust boundaries, retrieval contract, verifier,
and evaluation plumbing be tested without quietly deciding the model, runtime,
rights analysis, or production theology first.

## Run it

Python 3.10 or later is the only requirement.

```bash
python tools/serve_prototype.py
```

Open `http://127.0.0.1:8765` in a browser. The server binds only to the loopback
interface. Questions are held by the browser page for the current view and are
not written to disk or ordinary request logs.

The interface can:

- retrieve project-policy evidence and display resolvable citations;
- abstain when the demonstration corpus lacks evidence;
- refuse a false clerical identity or personal sacramental judgment;
- refuse to reconstruct unavailable Scripture or liturgical text;
- reject instructions that try to replace governing rules; and
- run the development behavioral suite and show every item's result.

## Run it without Python

`prototype/oi-offline.html` is the same demonstration as a single file. Copy
it to a phone or a computer and open it in a browser; it needs no server, no
installation, and no network, and it verifies every corpus record against its
published hash before answering. It is generated from the corpus, boundary
policy, and development suite by:

```bash
python tools/build_offline_bundle.py
```

Regenerate it in the same commit whenever any of those inputs change; the
tests fail if the committed file is stale, and a parity test drives the
bundle's JavaScript engine and the Python engine with one probe list and
requires identical answers. Its retrieval ranking uses a simpler scorer than
the reference SQLite path, which the page discloses.

The bundle is a transparent development artifact. Everything in it, the
corpus, the policy, the suite, and the engine, is meant to be read, and its
embedded hashes detect corruption, not authorship. It must never package a
production ELF, locked evaluation material, model weights, or protected
corpus material; a protected distribution is a separate decision with a
publisher signature anchored outside the file.

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

The next source-navigator increment is the reproducible Plithos export and a
real SQLite evidence package. It must begin with an immutable manifest, rights
inventory, transformation log, and repeatability test. A model adapter follows
device and license measurements; the current interface must continue to work in
retrieval-only mode so model behavior and retrieval behavior remain separable.

