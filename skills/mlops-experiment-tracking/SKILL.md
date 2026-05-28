---
name: mlops-experiment-tracking
description: "Organize machine learning experiment tracking, lineage, and reproducibility using run metadata, checkpoint manifests, W&B, MLflow, TensorBoard, SwanLab, local summaries, config snapshots, and comparison tables."
---

# MLOps Experiment Tracking

## Purpose

Make model runs reproducible and comparable across training, inference, data prep, and evaluation.

This differs from `training-progress`: that skill answers current progress/ETA. This skill designs durable tracking and lineage.

Read `references/tracking-systems.md` for W&B/MLflow/TensorBoard/local routing.

## Workflow

1. **Define run identity**
   - run name, date, git commit, command, app id/job id, user, repo, branch.

2. **Capture config**
   - model/checkpoint, dataset manifests, exclusions, hyperparams, trainable modules, inference settings, eval settings.

3. **Capture outputs**
   - checkpoint path, metrics path, predictions path, viewer path, logs path, summary JSON.

4. **Track lineage**
   - source checkpoint -> new checkpoint -> eval outputs.
   - dataset version -> training run -> inference run -> evaluation report.

5. **Compare**
   - use stable eval slices,
   - record metric definitions,
   - preserve denominators and skipped counts.

## Minimal Local Manifest

```json
{
  "run_name": "",
  "git_commit": "",
  "command": "",
  "input_paths": [],
  "output_paths": [],
  "model": "",
  "dataset": "",
  "metrics": {},
  "notes": ""
}
```

