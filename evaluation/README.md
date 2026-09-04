# Evaluation Workspace

This directory holds development evaluation material and public scoring
contracts. Locked evaluation prompts, expected answers, participant data, and
close paraphrases do not belong in the working repository.

## Two different measurements

`tools/run_evaluation.py` evaluates observable behavior of the current executable
prototype: response class, intent classification, boundary rule, verified
citations, and required or forbidden response features. It is deterministic and
runs in continuous integration. Its report deliberately says what it cannot
claim: passing a small development suite does not establish moral agency,
holiness, doctrinal correctness, or ecclesial authority.

`tools/score_forced_choice.py` preserves the core measurement improvement from
the second experiment without selecting a model runtime. It accepts a capture of
direct A/B probabilities, requires both `aligned_is_A` and `aligned_is_B`
orientations for every item, normalizes only over A and B, and averages the two
orientations. Missing logits or orientations remain missing rather than becoming
zero.

An input capture has this shape:

```json
{
  "run_id": "opaque-run-id",
  "model": "exact-model-and-quantization",
  "condition": {"substrate": "S0", "elf": "E0", "retrieval": "R0"},
  "items": [
    {
      "item_id": "opaque-item-id",
      "orientations": [
        {"orientation": "aligned_is_A", "p_a": 0.7, "p_b": 0.3, "used_logprobs": true},
        {"orientation": "aligned_is_B", "p_a": 0.2, "p_b": 0.8, "used_logprobs": true}
      ]
    }
  ]
}
```

Run it with:

```bash
python tools/score_forced_choice.py evaluation/examples/forced-choice-capture.example.json
python tools/score_forced_choice.py capture.json --output results/scored.json
```

The collector that produces those direct probabilities is intentionally deferred
until a model and runtime are selected through the device study.

## Historical experiment separation

None of the nine current development prompts is copied or paraphrased from the
historical 30- or 34-item banks. The historical scripts and banks are recorded by
hash in `research/evidence/provenance.v0.1.json` but are not committed here. They
remain research evidence and cannot serve as a hidden confirmatory bank after
being exposed during OI development.

## The revision loop

For every policy, ELF, retrieval, verifier, or model change:

1. version the changed component;
2. run the development suite and applicable domain banks;
3. retain item-level failures, not only the aggregate;
4. inspect capability regressions separately from ethical outcomes;
5. make only a traceable change grounded in the failure; and
6. rerun unchanged controls before deciding that the change helped.

Development results guide revision. Only the preregistered, access-separated
locked program can support a confirmatory claim.
