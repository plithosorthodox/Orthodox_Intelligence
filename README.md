# Orthodox Intelligence

Orthodox Intelligence (OI) is a research and engineering project for a private,
offline-capable assistant whose behavior is deliberately shaped, whose governing
framework is inspectable, and whose substantive Orthodox answers are grounded in
the curated texts and provenance published by Plithos.

This repository begins with the research program. It does **not** yet contain a
trained model, a production Ethical Learning Framework (ELF), or an application
ready for pastoral or public use.

## The design in one sentence

OI separates four things that must not be allowed to blur together:

1. a trained behavioral substrate;
2. a short, explicit, versioned Orthodox ELF;
3. an on-device Plithos evidence store; and
4. deterministic verification and product boundaries.

```mermaid
flowchart TD
    Q["User question"] --> B["Boundary and intent checks"]
    B --> R["Local Plithos retrieval"]
    R --> M["Local model: substrate + ELF"]
    M --> V["Quote, citation, and identity verification"]
    V --> A["Answer with sources or an explicit abstention"]
```

The model is not presented as a Christian, a member of the Church, clergy, a
spiritual father, or a substitute for sacramental and pastoral life. It is an
artificial system that reasons under a documented Orthodox-informed framework
and identifies the sources on which its answers rely.

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
- `schemas/` - machine-readable records for corpus, training, evaluation, and
  release manifests.
- `config/acceptance_criteria.v0.1.json` - provisional measurable gates.
- `tools/check_repository.py` and `tests/` - dependency-free repository checks.

## Validate the scaffold

Python 3.10 or later is sufficient; the validation path has no third-party
dependencies.

```bash
python tools/check_repository.py
python -m unittest discover -s tests -v
```

## Current status

Version `0.1` is a design baseline derived from the OEDMF/substrate distinction
in Samuel Sheffield's dissertation and the subsequent forced-choice experiment.
Experimental ELFs are evidence, not production doctrine. Numerical thresholds
in this first version are proposed engineering gates and must be ratified against
a pilot benchmark before they become release requirements.

