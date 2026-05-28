---
name: optimization-orchestrator
description: "Orchestrate speed and cost optimization work for machine learning repos, especially neural network training, inference, Modal GPU jobs, video/frame pipelines, dataset preparation, and evaluation loops. Use when the user asks to optimize a repo, speed up training/inference, reduce GPU cost, compare configurations, profile bottlenecks, coordinate multiple optimization skills, or run a structured optimization sweep."
---

# Optimization Orchestrator

## Purpose

Run a disciplined optimization loop: measure first, identify blockers, choose specialist skills, implement the smallest high-confidence change, benchmark against a baseline, and report speed, cost, accuracy, and risk.

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
- Preserve correctness and eval semantics. Speedups that change sampling, crops, prompts, labels, or checkpoints need an explicit accuracy/regression check.
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
   - Store the baseline in a comparable form so later runs can detect regressions mechanically.

3. **Classify Bottleneck**
   - Modal/fanout/cold-start/volume issue: load `modal-speed-optimizer`.
   - Model inference/HF/Qwen/OWLv2 issue: load `neural-inference-optimizer`.
   - Training/dataloader/checkpoint/distributed issue: load `neural-training-optimizer`.
   - Video decode/frame sampling/Mongo/R2/manifest/ETL issue: load `data-pipeline-speed-optimizer`.

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
   - Apply the performance gate: pass/fail each target, not just the headline wall-time number.
   - Flag regressions when any primary metric worsens by more than 5% unless the user set a different threshold.
   - If a change hurts correctness or cost, revert or disable it behind config.
   - Keep a short keep/discard decision for each experiment so later agents do not rediscover rejected configs.

7. **Report**
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

## Regression Detection

- Compare each candidate against the saved baseline for total wall time, key stage timings, throughput, cost, and accuracy/equivalence.
- Treat >5% slowdown, >5% cost increase, or any unexplained accuracy drop as a regression unless the user explicitly chose that tradeoff.
- For noisy cloud jobs, repeat a small benchmark or compare medians before rejecting a near-tie.
- Keep rejected configs and reasons in the run summary so future optimization passes do not retry them blindly.

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
