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
   - `docs/data-training-flow.md`
   - `docs/run-presets.md`
   - `docs/hsdp-troubleshooting-faq.md`
   - `docs/heldout20-eval.md`
3. Prefer the reviewed wrappers in `runs/` and `precompute/` over ad hoc
   command construction.
4. Before launching any Modal job, show the command and confirm the user wants
   the job started unless the current user request explicitly asks to start it.
5. For HSDP, verify compile-off args, precomputed data paths, perf gates, and
   local checkpoint/export settings before launch.
6. For heldout-20 inference, ensure the eval crop policy matches training.

## References

- `references/hsdp.md`: HSDP launch and troubleshooting checklist.
- `references/precompute.md`: crop policy and precompute checklist.
- `references/eval.md`: heldout-20 eval/viewer checklist.
