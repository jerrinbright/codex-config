---
name: finetuning-orchestrator
description: "Design and operate supervised fine-tuning workflows for neural models, including LoRA, PEFT, QLoRA, full fine-tuning, Axolotl, LLaMA-Factory, Unsloth, dataset formatting, trainable-module choices, LR groups, eval cadence, and checkpoint lineage."
---

# Finetuning Orchestrator

## Purpose

Choose and document a fine-tuning strategy that matches the model, dataset size, target behavior, compute budget, and evaluation plan.

This differs from `neural-training-optimizer`: that skill improves throughput/cost. This skill decides what and how to fine-tune.

Read `references/peft-frameworks.md` for PEFT/Axolotl/LLaMA-Factory/Unsloth routing.
Read `references/data-quality-and-curation.md` when the run depends on filtering, deduplication, noisy labels, pseudo-labels, or curated golden/test sets.

## Workflow

1. **Define goal**
   - New behavior, correction of failure modes, domain adaptation, style/format control, or bridge/projector adaptation.
   - Decide the success metric before launch: heldout accuracy, exact/similar match, top-k, preference win rate, format validity, or qualitative review slice.

2. **Inspect model and data**
   - Base checkpoint, current best checkpoint, trainable modules, dataset count, label quality, noisy/negative examples, heldout/test split.
   - Verify whether labels are human GT, model-derived, auditor-corrected, or synthetic/noisy.
   - Record dataset lineage: source campaigns/files, excluded test sets, dedupe/filter rules, noisy-row generation rules, and final train/val/test counts.

3. **Choose method**
   - LoRA/PEFT for low-cost adaptation and fast iteration.
   - QLoRA when memory is the blocker and supported.
   - Full fine-tune when behavior shift is broad and compute is acceptable.
   - Projector/bridge-only when vision-language alignment is the target.
   - Full non-vision stack when the vision encoder is frozen but language/projector behavior must adapt.

4. **Set config**
   - Trainable modules.
   - LR groups.
   - Batch/global batch/grad accumulation.
   - Max steps/epochs.
   - Save/eval intervals.
   - Resume behavior.
   - Dataset manifest and excluded test set.

5. **Evaluate**
   - Compare to prior checkpoint and base model.
   - Include exact/similar/wrong buckets when labels are natural-language actions/objects.
   - Store metadata in checkpoint folder.

## Method Routing

| Method | Use When | Watch For |
|--------|----------|-----------|
| LoRA/PEFT | Fast low-cost adaptation, limited behavior shift, ablation runs | Adapter target modules, rank/alpha, merge/export path |
| QLoRA | Memory blocks normal PEFT and quantized training is supported | Quantization quality loss, slower kernels, eval parity |
| Full fine-tune | Broad behavior change, enough high-quality data, compute budget is acceptable | Overfitting, catastrophic forgetting, checkpoint size/cost |
| Projector/bridge-only | New vision encoder or embedding-space adaptation | Weak language behavior changes, alignment eval required |
| Projector/bridge + LLM | Vision-language alignment plus label/action wording needs to adapt | LR grouping, language regression risk |
| Frozen vision full non-vision stack | Crops/preprocessing are fixed and object/action reasoning needs adaptation | Confirm training/inference image pipeline matches |

## Must Do

- Verify train/validation/test split before launching, especially campaign-based heldouts.
- Record base checkpoint, initialization checkpoint, dataset manifest, trainable modules, LR groups, max steps, save/eval cadence, and resume policy.
- State why each module is frozen or trainable.
- Keep config and metadata beside the checkpoint, not only in chat history.
- Compare against the prior best checkpoint and at least one base/reference run.
- Preserve evaluation semantics when changing prompt format, crops, frame sampling, or label normalization.

## Must Not Do

- Do not train or validate on a reserved test campaign.
- Do not silently mix dataset versions, pseudo-labels, noisy rows, or auditor-corrected rows.
- Do not continue from a checkpoint unless lineage confirms it is the intended initialization.
- Do not change LR, trainable modules, or dataset composition without logging why.
- Do not accept a run only from training loss; require heldout or qualitative evidence tied to the goal.

## Safety

- Do not include test campaign data in training or validation.
- Do not mix dataset versions without metadata.
- Do not continue from a checkpoint unless the user or evidence confirms that is intended.
