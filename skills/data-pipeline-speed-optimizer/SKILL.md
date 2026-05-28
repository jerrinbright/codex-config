---
name: data-pipeline-speed-optimizer
description: "Optimize ML data pipelines for speed and cost: video/frame sampling, FFmpeg/OpenCV decode, WES hand bbox lookup, crop annotation prep, R2/S3/Mongo/file I/O, manifests, JSONL shards, dataset splitting, and preprocessing caches."
---

# Data Pipeline Speed Optimizer

## Purpose

Speed up deterministic data prep so GPU training/inference is not starved or blocked.

Read `references/data-engines.md` when considering Ray Data, Dask, Polars, Vaex, Zarr, or chunked/packed storage.

## Workflow

1. **Map the data path**
   - Source IDs -> Mongo/R2/video paths -> manifests -> frames/crops -> model inputs -> outputs.
   - Identify whether work is per episode, per segment, per frame, or per prompt.

2. **Measure stages**
   - Mongo lookup time.
   - R2/S3 fetch time.
   - Video open/seek/decode time.
   - Resize/crop/image write time.
   - JSON/manifest read/write/merge time.
   - Failed/skipped/retry counts.
   - Keep the baseline in a comparable JSON/CSV/summary table with input count, output count, worker count, wall time, throughput, and failure rate.

3. **Locality first**
   - Group work by video URI before decoding.
   - Open each video as few times as possible.
   - Sort frame requests by timestamp/frame index per video.
   - Repartition after source-local work if detector/model shards need different grouping.

4. **Avoid duplicate work**
   - Fetch WES bboxes from `episodes.pipeline_results.hands.bbox_url` when available; do not rerun WES unless explicitly requested.
   - Cache per-episode WES JSON and per-segment crops.
   - Cache Qwen prompt extraction separately from frame/model work.
   - Make completed markers durable and ignore stale skipped markers when upstream data later appears.

5. **Parallelism**
   - Use enough workers for independent CPU/I/O work, but avoid overwhelming remote storage or creating tiny-task overhead.
   - For Modal, prefer sharded durable batches over one coordinator doing long serial scans.
   - Commit outputs in chunks.
   - Treat worker count, shard size, chunk size, and batch-query size as a single config; increasing one without measuring the others can slow the pipeline.

6. **Correctness checks**
   - Frame sampling changes must preserve timestamp semantics.
   - Crop/interpolation changes need visual samples.
   - Dataset splitting changes need counts, failed IDs, and excluded/test-set confirmation.
   - Fail the optimization if a speedup silently drops rows, changes frame timestamps, leaks test-set data, or loses required bbox/crop metadata.

7. **Regression checks**
   - Compare candidates against the saved baseline for fetch, decode, crop/write, manifest merge, total wall time, throughput, and failure/skipped counts.
   - Treat >5% slower throughput or any unexplained increase in failed/skipped items as a regression unless the user accepts the tradeoff.
   - For remote storage noise, compare medians across repeated small slices before making a final call.

## Common Fixes

- Video-aware frame sampling instead of segment-aware repeated opens.
- Batch Mongo queries by episode IDs.
- Persist normalized manifests and summary counts.
- Use JSONL shards for parallel writes, then deterministic merge.
- Separate train/validation/test exclusion before expensive prep.

## Benchmark Matrix

Use this shape for reporting data-pipeline experiments:

```md
| Config | Workers | Shards | Inputs | Outputs | Failed | Fetch | Decode | Crop/write | Merge | Wall | Gate |
|--------|--------:|-------:|-------:|--------:|-------:|------:|-------:|-----------:|------:|-----:|------|
```
