---
name: training-progress
description: "Analyze machine learning training progress from logs, metrics files, tracker exports, Modal output, TensorBoard-style scalars, CSV/JSONL histories, or pasted training text. Use when the user asks for elapsed time, consumed time/cost clues, ETA, epoch/step progress, train and validation curve trends, overfitting/underfitting signals, stalled runs, or concise status updates for active or completed training jobs."
---

# Training Progress

## Purpose

Give a factual training status update: where the run is, how much time has been consumed, expected ETA, and how train/validation metrics are evolving. Prefer measured values from logs over assumptions.

## Workflow

1. Identify the evidence source:
   - Pasted logs, terminal output, Modal logs, tracker export, CSV, JSON, JSONL, TensorBoard event-derived files, or repo-local output files.
   - If multiple runs exist, name the run, path, or job id being analyzed.

2. Extract progress signals:
   - Current epoch/step and total epoch/step target.
   - First and latest timestamps, elapsed wall time, and average time per epoch/step.
   - Train metrics and validation metrics with names and units exactly as reported.
   - Best validation checkpoint/epoch when available.
   - Learning rate, batch size, GPU type/count, and worker/runtime hints if present.

3. Compute ETA conservatively:
   - Use recent completed epoch/step durations when available.
   - Fall back to whole-run average only when recent timing is unavailable.
   - Say when ETA is unreliable due to warmup, variable validation duration, dataloader stalls, preemption, restarts, or missing total steps.

4. Interpret curves:
   - Describe direction, smoothness, plateauing, divergence, validation lag, train/val gap, and best-so-far behavior.
   - Compare from run start to latest, and from the previous reported checkpoint/epoch/step to latest when available.
   - Use epoch/step-level metric tables when history has more than one point.
   - Keep tables numeric and compact; put prose interpretation in a `Curve Read` subsection below the table.
   - Distinguish loss metrics from accuracy/PCK/AP-style metrics.
   - Do not infer success from train loss alone.

5. Report blockers and actions:
   - Surface missing validation, NaNs, exploding loss, stuck timestamps, repeated retries, checkpoint failures, data loading errors, or no recent log activity.
   - Recommend the smallest useful next check.

## Default Output

Use this shape unless the user asks for another format:

```md
## Training Progress

- Status: running/completed/stalled/unknown
- Progress: epoch/step X of Y, or percent if known
- Consumed time: elapsed wall time from first to latest evidence
- ETA: estimate and confidence
- Best checkpoint/metric: if available

## Curves

| Metric | Start | Prev | Latest | Best | Overall | Recent |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| train/<metric> | ... @ s/e | ... @ s/e | ... @ s/e | ... @ s/e | +/-...% | +/-...% |
| val/<metric> | ... @ s/e | ... @ s/e | ... @ s/e | ... @ s/e | +/-...% | +/-...% |

### Curve Read

- Train: start-to-latest trend, previous-to-latest change, smoothness/noise, and latest value.
- Validation: start-to-latest trend, previous-to-latest change, best-so-far, latest value, and whether latest is near or past best.
- Train vs validation: current gap, gap change since start, gap change since previous point, and overfit/underfit/plateau signal.
- Metric reliability: call out sparse validation, noisy recent train points, missing comparable metrics, or changed eval protocol.

## Findings

- Key observations from logs/metrics

## Issues/Risks

- Anything missing, stale, unstable, or suspicious

## Commands/Files Used

- `command or file`: why it was used and important result

## Next Checks

- Concrete follow-up checks in priority order
```

## Command Guidance

- Prefer read-only commands first: `ls`, `find`, `rg`, `sed`, `tail`, `head`, `wc`, and small parser commands.
- For large logs, inspect the head, tail, and metric lines before parsing the whole file.
- Do not launch training, servers, Modal jobs, long-running monitor loops, or GPU jobs unless the user explicitly asks.
- If using live cloud/tracker commands, explain what will be queried and avoid changing remote state.

## Calculation Rules

- Elapsed time: latest timestamp minus earliest relevant timestamp, or command-reported runtime if explicit.
- Average time per unit: elapsed completed training time divided by completed epochs/steps.
- ETA: remaining epochs/steps multiplied by average recent time per unit.
- If validation/checkpointing adds periodic overhead, include it in the observed average when possible.
- If timestamps are absent, do not invent elapsed time; report that timing cannot be computed from the evidence.
- Start value: first valid metric point for the same run/config.
- Previous value: immediately prior logged point for the same metric, unless the user gave an earlier progress report to compare against.
- Latest value: newest valid metric point, not just the newest line if that line lacks the metric.
- Best value: minimum for loss/error metrics; maximum for accuracy/AP/PCK/score metrics.
- Delta Start->Latest and Delta Previous->Latest: compute absolute change; include percent change when useful and denominators are nonzero.
- For epoch/step metrics, preserve the metric's reported epoch/step ids so the user can see where each value came from.

## Curve Interpretation Rules

- Improving loss usually means decreasing; improving accuracy/PCK/AP usually means increasing.
- A widening train/validation gap may indicate overfitting.
- Flat train and validation curves may indicate plateauing, learning-rate limits, data issues, or convergence; state which evidence supports the claim.
- Train improving while validation worsens is a stronger overfitting signal than train improving alone.
- Validation noise is normal for small validation sets; avoid strong claims from one point.
- Do not summarize curve evolution only from the last point. Always mention the start-to-latest change when at least two points exist.
- When enough points exist, mention whether recent progress is faster/slower than early progress.
- If train and validation metrics use different scales or names, do not compute a direct numeric gap; compare direction and relative behavior instead.
- If validation is sparse, identify the exact validation epochs/steps used for the comparison.
- Put qualitative labels such as "much improved overall", "noisy recently", or "slightly worse" in `Curve Read`, not in table cells.

## Safety

- Do not expose secrets, API keys, or private URLs from logs.
- Do not paste huge logs into the answer; summarize key lines.
- Mark assumptions clearly.
- Say when metrics are not comparable across runs due to changed data, checkpoint, config, batch size, or evaluation protocol.
