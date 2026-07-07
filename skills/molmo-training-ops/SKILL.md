---
name: molmo-training-ops
description: Use when working on Mecka Molmo labeler, crop/precompute, Modal HSDP training, checkpoint merge, verifier/corrector, or heldout-20 evaluation workflows in the molmo-label repo.
---

# Molmo Training Ops

Use this skill for operational Molmo work in `molmo-label`: data movement,
episode splitting, crop/frame precompute, single-node training, 2x8 H200 HSDP
training, checkpoint repair, and heldout-20 eval/viewer work.

## Workflow

1. Identify the task stage: data transfer, segment split, precompute, training,
   checkpoint/merge, inference, or viewer.
2. Read the relevant repo docs before editing or launching:
   - `docs/repo-map.md`
   - `docs/run-catalog.md`
   - `docs/data-training-flow.md`
   - `docs/run-presets.md`
   - `docs/contracts/`
   - `docs/hsdp-troubleshooting-faq.md`
   - `docs/heldout20-eval.md`
   - `docs/run-cards/`
3. Prefer the reviewed wrappers in `runs/` and `precompute/` over ad hoc
   command construction.
4. For smoke tests, prefer `python runs/smoke_tests.py`; it launches the
   Modal-backed Docker smoke runtime instead of workstation Python or local
   Docker.
5. Before launching any Modal job, show the command and confirm the user wants
   the job started unless the current user request explicitly asks to start it.
6. For HSDP, verify compile-off args, precomputed data paths, perf gates, and
   local checkpoint/export settings before launch.
7. For HSDP or preset launches, preserve `run_metadata.json`; it is the bridge
   from training crop policy to heldout-20 eval/viewer.
8. For heldout-20 inference, read `references/eval.md`, use
   `MOLMO_RUN_METADATA_PATH` when available, and prefer
   `runs/infer_holdout20.py` / `eval.holdout20_inference` so inference consumes
   metadata-provided annotation/cache env vars and precomputed tar/member
   fields.

## References

- `references/hsdp.md`: HSDP launch and troubleshooting checklist.
- `references/precompute.md`: crop policy and precompute checklist.
- `references/eval.md`: metadata-driven heldout-20 eval/viewer checklist.
