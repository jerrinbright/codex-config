---
name: finetuning-orchestrator
description: "Design and operate supervised fine-tuning workflows for neural models, including LoRA, PEFT, QLoRA, full fine-tuning, Axolotl, LLaMA-Factory, Unsloth, dataset formatting, trainable-module choices, LR groups, eval cadence, and checkpoint lineage."
---

# Finetuning Orchestrator

## Purpose

Choose and document a fine-tuning strategy that matches the model, dataset size, target behavior, compute budget, and evaluation plan.

This differs from `neural-training-optimizer`: that skill improves throughput/cost. This skill decides what and how to fine-tune.

Read `references/peft-frameworks.md` for PEFT/Axolotl/LLaMA-Factory/Unsloth routing.

## Workflow

1. **Define goal**
   - New behavior, correction of failure modes, domain adaptation, style/format control, or bridge/projector adaptation.

2. **Inspect model and data**
   - Base checkpoint, current best checkpoint, trainable modules, dataset count, label quality, noisy/negative examples, heldout/test split.

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

## Safety

- Do not include test campaign data in training or validation.
- Do not mix dataset versions without metadata.
- Do not continue from a checkpoint unless the user or evidence confirms that is intended.

