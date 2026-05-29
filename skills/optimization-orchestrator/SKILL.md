---
name: optimization-orchestrator
description: "Orchestrate speed and cost optimization work for machine learning repos, especially neural network training, inference, Modal GPU jobs, video/frame pipelines, dataset preparation, and evaluation loops. Use when the user asks to optimize a repo, speed up training/inference, reduce GPU cost, compare configurations, profile bottlenecks, coordinate multiple optimization skills, or run a structured optimization sweep."
---

# Optimization Orchestrator

## Purpose

Run a disciplined optimization loop: measure first, identify blockers, choose specialist skills, implement the smallest high-confidence change, benchmark against a baseline, and report speed, cost, accuracy, and risk. A candidate is not successful until it passes a fresh end-to-end no-regression gate on the same workload.

This skill is a coordinator. It should route to focused local skills when relevant:

- `modal-speed-optimizer`: Modal apps, GPU fanout, shard sizing, cold starts, volumes, detached runs.
- `neural-inference-optimizer`: model loading, batching, tokenizer/processor overhead, Qwen/OWLv2/HF inference, empty-shard behavior.
- `neural-training-optimizer`: training throughput, dataloaders, checkpoint cadence, frozen modules, LR schedules, distributed training.
- `data-pipeline-speed-optimizer`: frame sampling, video decode, manifests, R2/Mongo/file I/O, crop prep, ETL.
- `training-progress`: active training status, ETA, curve health.
- `html-video-viewer`: result viewers after optimization/eval runs.
- `mongo-episode-query-discovery`: Mecka episode, WES, label, campaign, and pipeline-result lookup.

Read `references/skill-map.md` if you need a compact map of upstream inspiration from the two GitHub skill repos.

The orchestration style is a lightweight version of a research loop: inner loop for fast controlled experiments, outer loop for synthesis and deciding the next optimization direction. Do not create a big research workspace unless the user asks; keep optimization state in the repo's normal logs/results folders or a small local summary file.

## Core Rules

- Measure before changing code unless telemetry already exists.
- Start from telemetry, not hunches. Break down the full pipeline into timed components, rank blockers by wall time/cost, then optimize the largest safe blocker first.
- Preserve correctness and eval semantics. Speedups that change sampling, crops, prompts, labels, checkpoints, ranking, heuristics, batching, sharding, or output formats need an explicit accuracy/regression check.
- Treat output-count mismatches as correctness failures. A candidate that returns fewer rows/segments/predictions than baseline is failed until explained and intentionally accepted.
- Do not call a change "faster" from a partial stage win. It must improve or preserve total end-to-end wall time and pass quality/equivalence gates on the same input slice.
- Do not commit or push optimization code until a fresh end-to-end candidate benchmark has passed the no-regression gate, unless the user explicitly asks to save a known-broken experiment.
- Prefer one controlled benchmark episode/slice before launching broad jobs.
- Track cost as GPU type x GPU count x wall time, plus avoidable cold starts or duplicate work.
- Fail loudly when required config, credentials, model paths, videos, WES bboxes, or labels are missing.
- Do not launch long jobs, training, deployments, or destructive cleanup unless the user explicitly asked for that action.
- Use subagents only when the user explicitly asks for agents, delegation, or parallel agent work. Give each agent a non-overlapping scope.

## Default Workflow

1. **Scope**
   - Identify repo, command, workload, model/checkpoint, dataset slice, target metric, and what "faster" means.
   - Capture constraints: max cost, max GPUs, GPU type, target accuracy, target ETA, whether detached jobs are allowed.
   - Define the performance gate before running experiments: minimum acceptable speedup, maximum tolerated cost, maximum allowed quality regression, and what slice proves the change.

2. **Baseline**
   - Find the current single-entry command or script.
   - Run or inspect a small baseline with telemetry.
   - Record wall time, per-stage time, GPU type/count, shard count, batch size, input count, output count, accuracy/proxy metric, and cost estimate.
   - Save the exact baseline command, git commit, run id/path/app id, inputs, output counts, and metric files.
   - Store the baseline in a comparable form so later runs can detect regressions mechanically.

3. **Classify Bottleneck**
   - Build a ranked component table before proposing fixes:
     - stage name
     - wall time and percent of total
     - max shard/container time when parallelized
     - cost driver
     - correctness risk if changed
     - likely specialist skill
   - Modal/fanout/cold-start/volume issue: load `modal-speed-optimizer`.
   - Model inference/HF/Qwen/OWLv2 issue: load `neural-inference-optimizer`.
   - Training/dataloader/checkpoint/distributed issue: load `neural-training-optimizer`.
   - Video decode/frame sampling/Mongo/R2/manifest/ETL issue: load `data-pipeline-speed-optimizer`.
   - If the largest blocker is a heuristic/postprocess stage, inspect algorithmic complexity, file I/O volume, serialization, repeated JSON scans, and shard-local merge opportunities before changing model code.

4. **Plan Experiments**
   - Propose 2-5 configurations max.
   - Include expected impact, correctness risk, cost risk, and validation method.
   - Prefer orthogonal experiments: e.g. batch size, shard count, cache strategy, early-empty exit, grouped decode.
   - For neural workloads, include at least one low-risk systems experiment before model-changing experiments.

5. **Implement**
   - Make the smallest code/config changes needed.
   - Add telemetry around changed stages.
   - Keep output paths/config names explicit and reproducible.

6. **Benchmark**
   - Re-run the same slice as baseline.
   - Compare stage timings, total wall time, throughput, cost estimate, and output equivalence/accuracy.
   - Verify output cardinality before looking at speed: same expected episodes, segments, frames, predictions, detections/selections, and final scored rows unless the experiment intentionally changes those counts.
   - Verify output quality before accepting speed: exact/equivalent outputs for pure systems changes, or accuracy/top-k/overlap metrics for model or heuristic changes.
   - Apply the performance gate: pass/fail each target, not just the headline wall-time number.
   - Flag regressions when any primary metric worsens by more than 5% unless the user set a different threshold.
   - If a change hurts correctness or cost, revert or disable it behind config.
   - Keep a short keep/discard decision for each experiment so later agents do not rediscover rejected configs.

7. **Commit Gate**
   - Only commit when the candidate has a passing fresh end-to-end run, not just unit tests, smoke tests, or comparison against stale artifacts.
   - The commit summary must include:
     - baseline run id and candidate run id
     - e2e wall-time delta
     - stage-level telemetry delta
     - output-count check
     - accuracy/equivalence check
     - remaining risk
   - If a candidate fails any gate, leave it uncommitted or revert/amend it before committing. If the user explicitly asks to commit a failed experiment, label it as failed/experimental in the commit message and docs.

8. **Report**
   - State the winning config and measured delta.
   - Include exact command(s), paths, app ids, checkpoint/results paths, and remaining bottlenecks.
   - Recommend the next single optimization only if it is clearly supported by telemetry.

## Telemetry Contract

Every optimization run should try to capture:

```text
run_name
git_commit
command
input_count
output_count
gpu_type
gpu_count
shard_count
batch_size
total_wall_ms
stage_wall_ms
model_load_ms
data_fetch_ms
decode_ms
preprocess_ms
forward_ms
postprocess_ms
merge_ms
eval_ms
accuracy_or_equivalence
cost_estimate
expected_output_count
actual_output_count
output_count_match
accuracy_baseline
accuracy_candidate
equivalence_check
regression_notes
```

Use JSON/JSONL/CSV when possible so later runs can be compared mechanically.

## Target Gates

Every optimization run should have explicit gates:

```text
speed_target
cost_target
quality_target
regression_threshold
baseline_run_id
candidate_run_id
gate_status
```

Use a compact benchmark matrix for comparisons:

```md
| Config | Wall time | Throughput | Cost est. | Accuracy/equivalence | Gate |
|--------|----------:|-----------:|----------:|---------------------:|------|
| baseline | | | | | |
| candidate | | | | | |
```

Do not accept a candidate only because one stage got faster. The accepted config should improve the bottleneck while passing quality/equivalence and cost gates.

## Component Optimization Loop

For every major stage, use this sequence:

1. **Measure**
   - Capture wall time, max shard time, sum of worker time if available, bytes/files read and written, output count, and failure count.
   - For Modal, separate parent orchestration time from child worker time.
   - For neural inference, separate load, preprocessing, forward, postprocess, and serialization.
   - For data/video work, separate fetch, decode, frame sampling, crop construction, and JSON/file writes.

2. **Explain**
   - Name why the stage is slow: GPU compute, CPU decode, tokenizer/processor overhead, volume I/O, Mongo/R2 latency, serialization, shard imbalance, cold start, or algorithmic complexity.
   - Confirm the explanation with telemetry or a targeted micro-benchmark.

3. **Change**
   - Make one focused change for that stage.
   - Keep a feature flag or config fallback when risk is non-trivial.
   - Preserve the same inputs and outputs unless the experiment explicitly tests a semantic change.

4. **Validate**
   - Run the same benchmark slice.
   - Compare stage time, total time, cost, output counts, and accuracy/equivalence.
   - Mark the change accepted, rejected, or inconclusive.

5. **Promote**
   - Only combine accepted changes after they pass individually.
   - Run one final combined e2e benchmark before committing or calling the work done.

## Regression Detection

- Compare each candidate against the saved baseline for total wall time, key stage timings, throughput, cost, and accuracy/equivalence.
- Treat >5% slowdown, >5% cost increase, or any unexplained accuracy drop as a regression unless the user explicitly chose that tradeoff.
- Treat missing or zero final outputs as an immediate failed run, even if earlier stages succeeded.
- Treat mismatched filenames, missing shards, skipped merges, empty selections, or stale artifacts as failed correctness checks until fixed and rerun.
- For noisy cloud jobs, repeat a small benchmark or compare medians before rejecting a near-tie.
- Keep rejected configs and reasons in the run summary so future optimization passes do not retry them blindly.

## Freshness Rules

- Do not validate a new code path using old outputs unless the task is explicitly an offline equivalence check.
- A "fresh e2e" run means the candidate code generated the final artifact from the original inputs in one pipeline execution.
- If a run status file is overwritten, stale, partial, or from a different commit/config, mark that metric as unavailable instead of filling it in from memory.
- If a launcher only starts a parent job and exits before child fanout finishes, do not count that launcher as a successful e2e run. Use the orchestrator/app telemetry that covers all children.

## Parallel Agent Pattern

Only when the user explicitly permits agents/parallelism:

- Agent A: inspect telemetry and summarize bottlenecks.
- Agent B: inspect data/frame/Mongo/R2 pipeline.
- Agent C: inspect model inference/training code.
- Agent D: prepare viewer/eval/report artifacts.

Give each agent read-only or disjoint write ownership. The main agent integrates, benchmarks, and decides.

## Output Shape

```md
**Optimization Status**
- Baseline:
- Bottleneck:
- Changes made:
- Benchmark:
- Cost impact:
- Correctness/eval:
- Next best move:
```
