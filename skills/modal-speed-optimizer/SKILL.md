---
name: modal-speed-optimizer
description: "Optimize Modal-based ML workloads for speed and cost: GPU job fanout, shard sizing, cold starts, detached runs, volume I/O, model caching, queue structure, app naming, retries, and telemetry. Use for Modal training, inference, data prep, or evaluation jobs that are slow, expensive, underutilized, or preempting."
---

# Modal Speed Optimizer

## Purpose

Improve Modal job throughput and cost without changing model semantics.

For deeper Modal patterns, read `references/modal-patterns.md` when the task involves large fanout, detached jobs, multiple GPU classes, volumes, app lifecycle, or cost/speed tradeoffs.

## Checklist

1. **Inventory the run**
   - App id/name, entrypoint, GPU type/count, container count, shard count, batch size, timeout, retry policy, volume mounts, output root.
   - Current wall time, per-stage time, output count, failed/skipped count.

2. **Find Modal-specific waste**
   - Empty shards that still load a model.
   - Too many tiny GPU containers for small inputs.
   - Too few containers for huge independent work.
   - Repeated model downloads or cache misses.
   - Repeated volume commits or many tiny files.
   - Coordinator doing serial work before fanout.
   - GPU workers doing CPU-only I/O or JSON parsing.
   - CPU workers doing GPU-suitable inference.

3. **Tune fanout**
   - Use fewer shards for small runs to reduce cold-start overhead.
   - Use more shards only when each shard has enough work to amortize model load.
   - Separate source shards from detector/training shards when input grouping differs from output parallelism.
   - Bucket by expensive resource locality: video URI, model checkpoint, episode, or file prefix.

4. **Tune containers**
   - Pick GPU based on measured bottleneck, not instinct.
   - For inference, prefer batch size and shard count sweeps before changing GPU class.
   - Avoid preemptible GPUs when user says non-preemptible or when restart cost is high.
   - For detached jobs, use clear app names and output roots.

5. **Telemetry**
   - Record app id, function-level counts, queue wait, cold start/model load, input fetch, compute, output write, total wall.
   - Write a durable `summary.json` per run.

## Common Fixes

- Early-return empty shards before loading model weights.
- Cache HF/model files on Modal Volume or image layer.
- Group frame decode by video so one worker opens a video once.
- Commit volumes once per batch/stage, not per item.
- Write JSONL shards then merge once.
- Use CPU Modal functions for Mongo/R2 metadata hydration and GPU functions only for GPU inference.
- Make shard count configurable by env var/CLI arg.

## Validation

Compare before/after on the same slice:

```text
total_wall_ms
nonempty_shards
empty_shards
model_load_ms
gpu_forward_ms
volume_write_ms
outputs
accuracy/equivalence
estimated_cost
```
