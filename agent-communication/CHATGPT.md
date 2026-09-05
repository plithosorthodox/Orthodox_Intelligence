# CHATGPT

Newest at the top. Only ChatGPT writes in this file.

---

## 2026-09-05 — PAUSED; Vulkan speed pass handed to Claude

Samuel asked me to stop because Claude Code is available again. **I am holding no files and making no further code changes.** I made no implementation changes during this pass. The only repository-side action before the stop request was creating the dormant branch `perf/windows-vulkan-owner-bundle` from then-current `main`; it has no commits of its own and can be ignored or deleted.

### What I confirmed before stopping

- The current owner-only Windows package manifest `config/windows_package_olmo2_q4km.v0.1.json` pins llama.cpp `b10819` to `llama-b10819-bin-win-cpu-x64.zip` with backend `cpu` and SHA-256 `4599e502b374196d24600ea9b03c842a448c853116a15b55e8ba502bdc727b3f`.
- The exact same official llama.cpp release `b10819` also publishes `llama-b10819-bin-win-vulkan-x64.zip`. GitHub reports its SHA-256 as `4c5ff97b5440024906fc90f67809d84b92d9b77847c7d1a800701a36499e565e`.
- The pinned llama.cpp source commit behind `b10819` supports `-ngl` / `--gpu-layers` / `--n-gpu-layers` with an exact number, `auto`, or `all`. For a deliberate acceleration test, `--n-gpu-layers all` is the clearest way to request full model-layer offload rather than merely swapping in a Vulkan-capable binary and hoping it chooses the desired placement.
- The current portable launcher obtains model-server flags from the package manifest, so this speed experiment should not require changes to `oi_prototype/model_runtime.py`, retrieval, verifier, UI, or corpus logic unless the hardware test exposes a separate issue.

### Recommended implementation

Preserve the known-working CPU manifest as a rollback baseline. Prefer adding a **distinct Vulkan package manifest** rather than overwriting the CPU one. The Vulkan variant should keep the same model, corpus, Python, loopback-only networking, `--ctx-size 4096`, `--parallel 1`, and `--temp 0`, while changing the llama.cpp component to:

- backend: `vulkan`
- asset: `llama-b10819-bin-win-vulkan-x64.zip`
- URL: the official `b10819` Windows x64 Vulkan asset
- SHA-256: `4c5ff97b5440024906fc90f67809d84b92d9b77847c7d1a800701a36499e565e`
- server flag: `--n-gpu-layers all`

Do **not** treat the Vulkan ZIP swap by itself as proof of GPU inference. On Samuel's Radeon 890M, verify the actual `llama-server` startup output. It should identify a Vulkan device and report model layers being offloaded to the GPU. If it reports zero offloaded layers, or Vulkan initialization fails, the speed pass is not complete even if Uvaha opens.

A clean rollback path is more valuable than clever automatic fallback for this first hardware measurement: keep the existing CPU manifest intact and let the builder's existing `--manifest` option select the Vulkan variant. If Vulkan fails on this laptop, rebuild with the CPU manifest and the already-verified CPU asset rather than adding hidden runtime behavior before we understand the failure.

### Tests I recommend for the Vulkan pass

Extend the Windows packaging tests so the Vulkan manifest proves: official pinned `b10819` Vulkan asset; recorded hash above; `backend == "vulkan"`; `--n-gpu-layers all` is present; `--ctx-size 4096`, `--parallel 1`, and `--temp 0` remain present; and the bundle still promises no runtime downloads / no bundled Web credential. Leave the CPU-asset resolver regression in place because the CPU package remains the known-good fallback.

Then run the normal gates before integration:

- `python tools/check_repository.py`
- `python tools/run_evaluation.py --fail-on-any`
- `python -m unittest discover -s tests -v`

The final acceptance test is hardware, not CI: rebuild `C:\Uvaha` using the existing OLMo 2 7B Q4_K_M model and installed corpus, launch it, confirm Vulkan device + layer offload in the server log, ask the same representative question, and compare elapsed response time with the CPU run. Record both the success/failure and observed timing; do not claim a speedup from configuration alone.

### Current release state I observed

Claude's merged `main` was at `b9b9de99b5ffab23a85efcd69c2302e62cc7cb27` when I inspected it, with the simplified chat UI/session work and the reported 149-test / 25-of-25 green baseline. `plithos_corpus` New Testament repair is already merged at `5bd9bf4ca959642ee23dab9808722506ea9b4bce`, so the Gospels issue is no longer the blocker. The remaining user-visible problem Samuel raised in this handoff is response latency from the CPU-pinned portable bundle.

**Released:** everything. Claude may take the Vulkan speed lane immediately.
