# Modal Patterns

Use this reference when a Modal workload is slow, expensive, underutilized, or hard to resume.

## Fanout Design

- Separate coordinator work from worker work.
- The coordinator should discover inputs, write a manifest, launch bounded work, and merge results.
- Workers should do large enough chunks to amortize cold start and model load.
- Avoid one remote call per tiny item when the item work is sub-second.
- Prefer shard inputs that match locality:
  - video/frame work: shard by video URI or episode before frame-level repartition.
  - model inference: shard by frames/prompts with enough rows per GPU.
  - metadata: shard by episode/project/campaign and batch DB calls.

## Shard Count Heuristic

Start with:

```text
target_rows_per_gpu_shard = enough work for >= 30-120s compute after model load
num_shards = ceil(total_rows / target_rows_per_gpu_shard)
num_shards = clamp(num_shards, min=1, max=user_gpu_limit)
```

For tiny evals, fewer shards are often faster than many GPUs because model load and cold starts dominate.

## Empty Shards

Every GPU worker should check whether its input rows are empty before loading model weights.

Bad:

```python
model = load_model()
rows = read_rows(path)
if not rows:
    return
```

Good:

```python
rows = read_rows(path)
if not rows:
    write_empty_summary()
    return
model = load_model()
```

## Volumes And Files

- Write JSONL shards, then merge once.
- Avoid committing a volume per row.
- Avoid many tiny image files if a later stage can stream from video or a packed format.
- Record a durable `summary.json` with counts and timings.
- Treat stale skipped markers carefully when upstream data can be recovered later.

## GPU Selection

- T4/A10/L4/L40S are usually cost-effective for batch vision inference if model fits.
- A100/H100 are useful when training, memory bandwidth, large batch, or model size dominates.
- If CPU/video decode dominates, a faster GPU may not improve wall time.
- Benchmark one representative slice before scaling.

## Detached Run Hygiene

Use clear names:

```text
<project>-<stage>-<dataset>-<config>-<date-or-run-name>
```

Always report:

- app id
- command
- input manifest
- output root
- GPU type/count
- latest count
- ETA/cost estimate
- resume command

