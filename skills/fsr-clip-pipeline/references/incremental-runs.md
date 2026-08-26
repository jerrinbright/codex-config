# Incremental runs: finding what is actually new

The pipeline must be triggerable repeatedly and pick up only unprocessed
episodes. Get this wrong and you either reprocess 150k episodes or silently skip
work.

## Use a SET DIFFERENCE against the manifest, not a timestamp

The manifest on the volume is the source of truth for "already done", because it
is only appended to **after** a clip is written and verified.

```python
def pending_episodes(db, volume_manifest, since=None):
    q = {}
    if since:                      # optimisation only, never the sole filter
        q["createdAt"] = {"$gte": since}
    reviewed = {str(e) for e in
                db.audit_episode_first_segment_labels.distinct("episodeId", q)}

    done = set()
    if os.path.isfile(volume_manifest):
        with open(volume_manifest) as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    if "_manifest" not in r:
                        done.add(str(r["episodeId"]))

    return sorted(reviewed - done)
```

## Order matters: diff BEFORE resolving multicam

Measured on 263,808 reviewed episodes / 156,452 manifest rows:

```
distinct (all)                8.2s
distinct (7-day window)       0.9s
manifest read                 1.6s
set difference               0.05s
                            ------
delta computation             ~10s

multicam resolve, 5,000 eps  16.5s   <- ~3.3s per 1,000
```

`episodes.split_results.left_video_key` is UNINDEXED (that collection has only an
`_id` index), so multicam resolution is the dominant cost and scales with how
many episodes you feed it. Resolve it LAST, for pending episodes only -- never
for the full reviewed set.

Correct order:

```
bound by watermark  ->  subtract manifest  ->  subtract skip list
                    ->  resolve multicam   ->  report delta
```

A raw diff over-reports badly: `distinct` returns every episode in the
collection including non-multicam ones, while the manifest holds only processed
first-segment episodes. On real data that produced a "pending" count of 107,356
when the true multicam delta was a fraction of it -- the same error that once
reported 156,199 new episodes for a batch that was far smaller. **The number you
report must be the post-multicam count.**

## Why a timestamp watermark alone is wrong

A `createdAt > last_run` filter misses three real cases:

1. **Failed episodes from prior runs.** A run that died mid-flight leaves
   reviewed episodes unprocessed. Their `createdAt` is older than the watermark,
   so they are never retried. One run left 4,943 episodes unrectified this way,
   and a proxy completion check reported "done".
2. **Backfills and re-reviews.** `audit_episode_first_segment_labels` grew from
   203 to 47,286 to 233,099 episodes over weeks, not monotonically by review
   date. A window query returned 80,710 episodes for a 3-day window while the
   true unprocessed delta was different again.
3. **Episodes skipped for a reason that later resolves.** Missing
   `calibration_key`, no `left_video_key`, no valid span. If those fields are
   backfilled later the episode becomes processable, but its `createdAt` never
   changes.

Use the timestamp only to bound an expensive Mongo scan, and **always** subtract
the manifest afterwards.

## Record a watermark for speed, trust the diff for correctness

```json
{"_manifest": {"schema": "first_segment_jsonl_v1",
               "sourceCollection": "audit_episode_first_segment_labels",
               "last_run_utc": "2026-08-21T17:00:00Z",
               "episodes_at_last_run": 156452}}
```

On the next trigger: query with `createdAt >= last_run_utc - 7 days` (a generous
overlap absorbs late-arriving reviews), then subtract the manifest. The overlap
costs a slightly larger Mongo query and guarantees nothing is missed.

## Report the delta before spending

Always print, and stop if it looks wrong:

```
reviewed episodes in window     80,710
  already in manifest            2,008
  not multicam                      47
  no calibration_key                 N
  NEW to process                78,655
projected                    ~350 GB, ~78,655 inodes
inode headroom on volume         ...
```

An unexpectedly large delta usually means the multicam filter or the manifest
path is wrong, not that 150k new episodes appeared. One audit reported 156,199
"new" episodes because it compared against the wrong volume; the true figure was
far smaller.

## Permanently unprocessable episodes

Episodes with no `calibration_key` can never be rectified. Without a record they
reappear as "pending" on every run and a watchdog retries them forever -- one
monitor looped on ~149 such episodes.

Write them to a skip list on the volume with a reason, and exclude them from
`pending_episodes`:

```
<volume>/manifests/<name>.skipped.jsonl
{"episodeId": "...", "reason": "no_calibration_key", "seen_utc": "..."}
```

Revisit the skip list only when the underlying cause could have changed.
