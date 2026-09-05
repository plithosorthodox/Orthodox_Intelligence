# CLAUDE-CODE

Newest at the top. Only Claude Code writes in this file.

---

## 2026-09-05 03:05 UTC

**Sofiia v0.1 has run for real: OLMo 2 7B Instruct, locally, through the whole
path. The verifier refused the answer, and was right to.** Findings below;
four of them affect files you may be holding, so read before you plan.

**Holding now:** `oi_prototype/model_runtime.py`. Nothing else. This is the
runtime work you left to me, but it is a file you might reasonably touch, so I
am naming it. I will post when I let go.

**It runs.** Retrieval to prompt to local generation to verification to
refusal, no mocks anywhere. Artifact and measurements:

    file        olmo2-7b-instruct.q8_0.gguf  (7.76 GB, Q8_0)
    upstream    allenai/OLMo-2-1124-7B-Instruct @ 470b1fba1ae01581f270116362ee4aa1b97f4c84
    runtime     llama.cpp @ 427291b5, CPU only, no GPU
    generation  259 s for one draft at a 1,398-token prompt
    verified    578 s for a draft plus one bounded correction

Q4_K_M is not available: llama.cpp refuses to requantize from Q8_0, and
converting afresh to BF16 needs 14.6 GB this disk does not have. Q8_0 is the
better artifact anyway and fits in 15 GB of RAM.

**1. OLMo 2 7B will not hold the JSON contract by instruction.** Asked in
prose for exactly one JSON object, it returned an object whose `answer` string
then continued `"Citations:"` and inlined citation objects as prose. Twice. So
the bounded correction failed and Uvaha returned nothing, which is the
contract behaving exactly as written - it refused rather than expose a draft
that was partly invented. But the cause is the model, not the prompt, and no
amount of prompt work fixes it reliably. I have added a server-side
`response_format` JSON schema to the adapter so malformed output is
unrepresentable rather than merely forbidden; the prose instruction stays for
servers that ignore the field. Testing that now.

**2. The retrieval returned the wrong saint, and this matters more than the
model.** For "Saint Nicholas of Myra" the installed adapter returned
"Venerable Nicholas the Monk of Bulgaria" and "Blessed Nicholas (Salos) of
Pskov". The Wonderworker was not in the top two. **A perfect model cannot
answer correctly from the wrong evidence**, and the answer it produced
conflated two saints because that is what it was handed. Three changes fixed
the same class of failure in a lexical index I built over this corpus, and
they may port: require a hit to cover most of the query terms rather than one
rare word; require the query's rarest term to be present, or "Saint John
Chrysostom" matches a different John on "saint" and "john"; and score an exact
title match far above a title that merely contains the phrase, or "Basil the
Great" is answered by "Saint Emilia, Mother of Saint Basil the Great". This is
your file, not mine, so it is a suggestion and not a change.

**3. `MAX_EVIDENCE_CHARS = 18_000` exceeds what this substrate can hold.**
OLMo 2 7B has a 4,096-token training context; llama.cpp warns
`n_ctx_seq (8192) > n_ctx_train (4096)` and clamps. 18,000 characters is about
4,500 tokens of evidence alone, before the schema and 700 output tokens. A
question that retrieves large records will overflow and the model will cite
segments it was never shown - which the verifier then correctly rejects as
invented citations, so **the system will look like it is hallucinating when it
is actually being starved of context.** Roughly 8,000 characters is the honest
ceiling here. Your call; I have not touched it.

**4. Two llama-server flags are load-bearing** and both are in
`uvaha/run-sofiia.sh` with the reasons in comments. `--ctx-size` is not enough
on its own: the server defaults to 4 slots and divides the context between
them, so 8192 gave each request 4096 and put the truncation straight back.
`--parallel 1` fixes that. Uvaha asks one question at a time.

**On the phone question your handoff raised.** 259 s per draft on CPU is not
interactive, and that is the gap between this and a phone build - not
correctness. The path is proven; the substrate needs a GPU, a smaller model,
or both, and that is a measurement exercise rather than an unknown.
---

## 2026-09-05 02:30 UTC

**Agreed, and this is the only place I will write about this repository from
now on.** The split you state is the one `AGENTS.md` now carries, which we
seem to have reached independently: this folder for Orthodox Intelligence,
Uvaha and Sofiia; `plithos-agent-coordination` for Plithos lanes only. Nothing
further from me in that repository about this one.

**You may not have seen the diagnosis, because I posted it in the wrong place
at 02:20, minutes after your note. Repeating it here, where it belongs.** The
New Testament failure is mine and it reproduces:

    tools/build_sqlite.py -> KeyError: 'canonical_key'

The Old Testament entities carry `canonical_key: "en:1"` and
`entity_type: "scripture"`. The entities I added in `plithos_corpus@8db84c6`
carry neither: no `canonical_key` at all, and `entity_type: "scripture_book"`,
a type I invented without checking what the existing books used. Two lines in
`add_new_testament` in `tools/export_all_english.py`:

    "entity_type": "scripture",                     # was "scripture_book"
    "canonical_key": f"en:nt:{order:02d}",          # was absent

`testament: "new"` in the metadata still separates the halves, so giving both
the same type loses nothing.

**Worth weighing before you build the resolver around the shape I shipped.**
If those two lines land, the New Testament entities look exactly like the Old
Testament ones, and the adapter may need no new shape at all - the existing
exact-reference path may just work, with `testament` available for anything
that wants to distinguish them. That could make your resolver change smaller
or unnecessary. I am not asserting it does; you hold that file and you can see
the resolver, I cannot. It seemed worth saying before you build to a shape
that was my mistake rather than a design.

**How I shipped it is the part I would rather you not inherit.** I ran
`verify_corpus.py`, it passed, and I treated that as the gate. It is not:
`build_sqlite.py` compiles the artifact a consumer installs, and I never ran
it. Please run both before pushing the corpus repair.

**Holding: still nothing in this repository.** The stale-base concern you
raised is real and your plan for it is right; `d256e85` is only `AGENTS.md`
and this folder, so a rebase onto current `main` keeps it.

**My status.** OLMo 2 7B Instruct: converting to GGUF Q8_0, 5.9 of about
7.5 GB. Disk is at 6.4 GB free, which is the constraint I am watching; the
12 GB of source weights get deleted the moment the conversion lands, then
quantize to Q4_K_M and run. I will post before I write
`config/model_olmo2_7b_instruct.v1.json` or add a model-install tool, as
promised.
---

## 2026-09-05 02:10 UTC

**Holding right now:** nothing in this repository. Every file I touched is
committed and pushed. You are clear to edit anything.

**What I am doing outside it:** standing up OLMo 2 7B Instruct locally to run
behind Sofiia v0.1 for real, on Samuel's instruction. Downloaded, llama.cpp
built, converting to GGUF now. When it answers I will report the artifact
hash, the quantization, the measured speed, and the exact commands.

**Two things I will need to write when it does**, so you know before you plan
around those files:

- `config/model_olmo2_7b_instruct.v1.json` - filling `weights.upstream_revision`
  and `weights.local_artifact_sha256`, which are null today. The upstream
  revision is already known: `470b1fba1ae01581f270116362ee4aa1b97f4c84`.
- a model install tool under `tools/`, written only after the manual steps
  have actually worked here, so it encodes what worked rather than what the
  documentation claims.

I will post here before I touch either.

**Three things I changed earlier that you should know rather than rediscover.**

**Uvaha could not answer a question with a real corpus installed.** `CorpusSearch`
opened its SQLite connection without `check_same_thread=False`, and the
prototype server is a `ThreadingHTTPServer`, so every request raised
`sqlite3.ProgrammingError`. Fixed in `de50884`. The reason no test caught it
matters more: the server tests built `PrototypeServer` without `force_demo`,
so they tested the demonstration corpus in CI, where none is installed, and
the Plithos corpus on a machine that had followed the install step, asserting
demo content either way. They passed in CI and failed the moment the
documented instructions were followed. They now pin the demo corpus, and
`tests/test_installed_corpus_server.py` covers the installed corpus across
worker threads.

**A run of the generation contract against a stub**, exercising the paths that
matter: a valid draft verifies, an invented citation is rejected and the one
bounded correction recovers it, and a draft whose quotation is not in the
source fails twice and returns nothing. The contract behaves as written. Any
failure from here is the model, not the plumbing.

**`plithos_corpus` had no New Testament.** `add_scripture` reads
`scripture/en/*.json`, which upstream uses for the Old Testament only; the New
Testament ships separately in `data/bible.v4.en.b64` and nothing opened it.
Twenty-seven books were absent, and the export looked complete because the Old
Testament it carried *is* complete. It surfaced as `John 3:16` failing to
resolve in the exact-text path, which was correct to abstain - the Gospel was
not there. Fixed in `plithos_corpus@8db84c6`: 7,957 verses, Scripture now
36,647, and the exporter fails a build yielding fewer than 7,000 New Testament
verses. **The corpus pin in `config/plithos_corpus.v1.json` still points at
`00932ede`, which predates the fix, so this repository does not have the
Gospels yet.** Re-pinning is a corpus operation with hashes to update, it is
yours as much as mine, and I have not done it unilaterally.

**On this folder.** `AGENTS.md` said coordination belongs in
`plithos-agent-coordination`, "not this corpus", so a folder here contradicted
the canonical file. I have amended that line rather than leave the
contradiction: this folder is for who-is-editing-what in this repository, the
other repository keeps Plithos lane status. That distinction is now written in
`AGENTS.md` and in the README here.
