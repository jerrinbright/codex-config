---
name: fsr-clip-pipeline
description: Build a multicam clip corpus on Modal end-to-end - query approved labels from Mongo, cut segments from R2, rectify fisheye to pinhole, extract objects, and emit trainer-ready manifests. Use when downloading/undistorting new episode segments, refreshing a training corpus, or when a clip pipeline run has stalled or failed.
---

# FSR clip pipeline

Take approved episode labels to trainer-ready manifests without losing a night to
avoidable failures. Every rule here comes from a run that actually broke.

## The core rule

**One idempotent unit of work per episode. Never a staged pipeline.**

```python
def process(episode_id):
    if manifest_row_exists(episode_id):
        return "skip"
    raw  = cut_from_r2(episode)          # bytes in memory, NOT on the volume
    rect = rectify(raw)                  # in memory
    verify(rect)                         # ffprobe packets >= 2, size > floor
    write(f"{VOL}/clips/{episode_id}/{segment_id}.mp4")
    append_manifest_row(...)             # ONLY after the file is verified
```

A staged pipeline (extract-all, then rectify-all) creates every problem below:
two full copies on disk, stage sequencing, manifests referencing clips that were
never produced, and separate sweep/cleanup/filter passes. Per-episode processing
removes all of them at once.

Resume is then a set difference: DB episodes minus manifest rows. Crash anywhere,
rerun the same command, it continues.

## Non-negotiables

1. **Config travels in function arguments, never env vars.** Local env does NOT
   propagate into Modal containers. A module-level `os.environ.get(...)` silently
   falls back to its default inside the worker. This has produced: an extraction
   run that read the wrong manifest and no-op'd over 153,418 existing clips, and a
   clustered trainer that read `nodes=8` when launched with `nodes=1`.

2. **N pools of 250 workers, never one pool of N.** Modal autoscales per app. One
   app crawled to 400 workers; eight apps reached 1,555 and ran ~6x faster. Shard
   disjointly with `episodes[shard::nshards]` and check the arithmetic -- shards
   `0..3` of `nshards=4` already cover everything, so adding `4..7` of `nshards=8`
   duplicates work rather than extending it.

3. **Jittered commit with backoff in every worker that writes.**
   ```python
   time.sleep(random.uniform(0, 120))
   for attempt in range(5):
       try: vol.commit(); break
       except Exception:
           if attempt == 4: raise
           time.sleep(2 ** attempt * 5)
   ```
   Simultaneous `VolumeCommit` at 250+ workers returns `DataLossError: failed to
   publish commit to server` and kills the run mid-flight.

4. **Never keep both the raw and the processed copy.** Modal V1 volumes cap at
   **500,000 inodes**, not bytes. Keeping fisheye + rectified for 153k clips
   exhausted it and both stages died on `ENOSPC: No space left on device`. Delete
   the source the moment its output is verified, or better, never write it.
   Check `modal.Volume.from_name(..., version=...)`; V2 volumes lift this cap.

5. **Verify decodability, not existence.** `os.path.isfile()` passes on truncated
   files. A single unreadable clip kills a whole distributed training run --
   neither the MAP nor the Marlin trainer tolerates a bad row. Gate on
   `ffprobe -count_packets` (>= 2 packets) and a size floor. Probe the cheap
   header (`format=duration`) FIRST: a truncated file makes a packet count scan
   the whole file, which is what turns one bad clip into a 50-minute straggler.
   **Sweep the ENTIRE training manifest, not just the new pull** -- 873 bad clips
   sat in the pre-existing 194k rows and one of them (`moov atom not found`)
   killed a 64-GPU run at step 0.

6. **Any sharded sweep must persist per-shard results as they finish.** A
   `.map()` that only returns at the end lets one straggler hide 127 finished
   shards: v1 of the decodability sweep ran 53 minutes and produced nothing,
   v2 wrote per-shard files and was usable at 255/256. Progress must be
   countable and partial work must survive.

## Always spawn watchers

Every long-running job gets a supervisor. A job that dies unattended costs the
whole gap until someone asks. See `references/watchdog.md` for the template.

A watcher must:
- poll the **real completion metric** (episodes pending), never a proxy like
  "output count > input count", which can be true while work remains
- relaunch when the app is gone and work remains
- **stop, not retry, on ENOSPC / inode exhaustion** -- that is not transient
- log every check with a timestamp so a stall is visible in the history

## Procedure

1. **Scope the delta — set difference on `segmentKey`, never `episodeId`, never a
   timestamp alone.** An episode now carries MANY labelled segments. An
   episode-keyed delta reports 1 pending when 160,042 segments are waiting,
   because any episode already processed for one segment looks done. Some clips
   are held under an older `episodeId:index` id while the DB keys them by hex64
   `segmentKey` -- join on `(episodeId, index)` to recognise them, or you will
   re-cut 79,586 clips you already have. The manifest on
   the volume is the source of truth for "already done" because rows are appended
   only after a clip is verified. Query the label collection (optionally bounded
   by `createdAt` for speed), resolve multicam via
   `episodes.split_results.left_video_key` (NOT `delivered.left_video_path`,
   which marks WRIST cameras), then subtract manifest episode ids AND the skip
   list. A pure `createdAt > last_run` filter silently misses episodes that failed
   in a prior run, backfills, and episodes whose blocking field was filled in
   later. See `references/incremental-runs.md`. Report the delta and projected
   TB/inode cost before spending.
2. **Estimate.** Measure duration on ~20 clips first; size scales with segment
   length. Report projected TB and inode cost, and check headroom against 500,000.
3. **Run** the per-episode pipeline, sharded into pools of 250, with watchers.
4. **Extract objects for the new pull -- ALWAYS, by default.** Objects come from
   the action-label text (`correctedLabel` or `modelLabel`), not from pixels. A
   pull without objects is only half-usable: it can train a labeler but not MAP.
   FIRST diff the pull's label verbs against `LEADING_VERBS` and extend the list:
   pull6 leaked `sweep floor` (1,286) and `mop floor` (1,081) as its two most
   frequent "objects" because a new label distribution used verbs the parser had
   never seen. Then review, dedup and generalise -- the raw distinct-term count
   is ~4x the real object count. Full procedure in
   `references/object-vocabulary.md`; trainer row schemas in

   The stage-by-stage decision procedure for what IS an object -- reject/strip/
   keep/normalise/merge/back-off, plus the four verification gates -- lives in
   `references/object-candidate-rules.md`. Apply it to VAL GT as well as the
   bank: an unaudited val set measured a 0.49 achievable ceiling that rose to
   0.98 under the same rules, with no model change.
   `references/trainer-schemas.md`.
5. **Merge into the cumulative dataset, writing a NEW file.** Never mutate the
   existing dataset -- a training run may be reading it, and an unreproducible
   corpus is worse than a slightly stale one. Name the output by pull:
   `first_segment_dataset_<pull>.jsonl` plus `first_segment_vocab_<pull>.json`.
   **KEY THE MERGE ON `segment_id`, NEVER `episode_id`**, and pass the base
   dataset as an argument rather than hardcoding it. Episode-keyed merging made
   159,997 new segment rows OVERWRITE 35,600 existing ones (`added: 1,
   replaced: 35,600`) and the corpus did not grow. On collision the NEWER review
   wins. A near-zero `added` on a large pull means the key is wrong.
6. **Emit manifests** for the target trainer. Schemas differ; see
   `references/trainer-schemas.md`.
7. **Verify** before declaring done: manifest rows resolve on disk, train/val
   episode overlap is 0, and the val set's objects all have training support.
8. **Update the watermark** in the manifest header and append any permanently
   unprocessable episodes (e.g. no `calibration_key`) to the skip list with a
   reason, so the next trigger neither reprocesses nor retries them forever.

## Reporting

Report measured rates, never projections from a warmup or degraded window. Rates
taken during container ramp or under write pressure understate steady state by
5-10x; three separate ETAs were wrong tonight for exactly this reason. Sample the
rate between two logged checkpoints and quote that.

State what is NOT done as clearly as what is.
