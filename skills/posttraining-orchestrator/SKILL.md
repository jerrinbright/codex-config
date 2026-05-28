---
name: posttraining-orchestrator
description: "Design post-training workflows such as DPO, SimPO, RLHF, GRPO, TRL, OpenRLHF, verl, preference learning, rejection/correction learning, reward modeling, and auditor-feedback training."
---

# Post-Training Orchestrator

## Purpose

Turn human preferences, corrections, rejection reasons, or model comparisons into post-training data and choose the right alignment method.

Use `finetuning-orchestrator` for supervised target labels. Use this when the signal is comparative, preference-like, reward-like, or based on auditor corrections.

Read `references/preference-methods.md` for method selection.

## Workflow

1. **Classify signal**
   - Chosen vs rejected response.
   - Corrected label vs wrong model label.
   - Score/rating.
   - Freeform auditor note.
   - Tool/verifier confidence.

2. **Build data**
   - Preserve prompt/input context.
   - Store chosen/rejected or target/counterexample.
   - Convert freeform notes only when the correction is unambiguous.
   - Keep provenance: campaign id, auditor, timestamp, model version.

3. **Choose method**
   - SFT on corrected labels if there is one clear target.
   - DPO/SimPO if there are chosen/rejected pairs.
   - Reward model if scores/preferences need reuse.
   - GRPO/RL-style only when reward/eval loop is robust enough.

4. **Validate**
   - Heldout preference accuracy.
   - Regression on standard SFT eval.
   - Examples where policy became worse.

## Safety

- Do not train on ambiguous auditor notes as truth without marking uncertainty.
- Keep test/audit holdout campaigns excluded.
- Preference data should not overwrite supervised GT silently.

