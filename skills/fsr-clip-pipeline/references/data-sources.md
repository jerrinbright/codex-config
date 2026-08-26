# Data sources and their traps

## Collections (Mongo `mecka-ai`)

| collection | what it is |
|---|---|
| `audit_episode_object_labels` | approved object labels; an episode lands here only when EVERY segment is approved |
| `audit_episode_first_segment_labels` | first-segment action reviews: `modelLabel`, `correctedLabel`, `changed`, `reasons`, `hasConflictingReview` |
| `audit_first_segment_review_queue` | assigned/completed review items |
| `audit_segment_object_answers` | raw per-annotator answers (pre-resolution) |
| `episodes` | `split_results.left_video_key`, `calibration_key` |

## episodeId is a STRING in the label collections

`audit_episode_first_segment_labels.episodeId` and its siblings store the episode
id as a **string**. Only `episodes._id` is an `ObjectId`. Querying the label
collections with `ObjectId(...)` matches ZERO documents and fails silently -- one
run skipped 29,343/29,343 episodes as "no_valid_span" because of this.

```python
db.episodes.find({"_id": {"$in": [ObjectId(e) for e in eps]}})          # ObjectId
db.audit_episode_first_segment_labels.find({"episodeId": {"$in": eps}}) # strings
```

Verify with `count_documents` on one known id both ways before a bulk query.

## Multicam is `episodes.split_results.left_video_key`

**Not** `delivered.left_video_path` -- that field marks **wrist** cameras and cuts
across mono/stereo. A `stereo_no_wrist` episode had none; a `mono_wrist` delivery
was 100% populated. Using it silently selects the wrong corpus.

## Approved does not mean multi-human agreed

`audit_episode_object_labels` objects carry `votes`, and `votes: 2` means two
different things:

```
60.4%  votes 2-3, no geminiVotes field   -> 2-3 humans independently agreed
38.1%  votes 2, humanVotes 1, geminiVotes 1  -> ONE human + a Gemini tiebreak
 1.5%  votes 0                            -> human override of a prior value
```

`GEMINI_LEXICAL_TIEBREAK` fires only when **no** object got 2+ human votes, i.e.
annotators agreed on nothing. It is a **synonym merger, not a correctness check**,
and its prompt says explicitly: *"Do not infer which reviewer is correct from an
action, scene, or video."* It sees only a word list. Non-synonymous disagreements
are all kept, so `votes = humanVotes + 1` for anything it selects.

Consequences:
- tiebreak segments carry **median 3 objects vs 1** for straight agreement
- long object inventories signal low annotator agreement, not a busy scene
- filtering on `votes >= 2` looks like a consensus filter but admits every
  single-human label. The real consensus signal is **`geminiVotes == null`**.

## Clip sources

`recording_left_cam.mp4` (untrimmed) is the correct source. `frames.csv` vs
`frames.trimmed.csv` differ by exactly 120 frames (2.0s at 60fps), and label
timestamps are on the **untrimmed** timeline -- use them with no offset. The
manifest may name the `.trimmed.mp4` asset; swap to the untrimmed sibling.

R2 requires **SigV4**. boto3 defaults to SigV2 presigned URLs, which return 401
only when ffmpeg fetches them:

```python
boto3.client("s3", endpoint_url=..., config=Config(signature_version="s3v4"))
```

## Calibration

Basalt files wrap everything in a `value0` envelope: `payload.get("value0", payload)`.
Double Sphere intrinsics are `fx, fy, cx, cy, xi, alpha`.

Episodes with no `calibration_key` **cannot be rectified at all**. Exclude them at
manifest time rather than letting a watcher retry them forever.

## Volume layout

Keep one volume per corpus, and one layout:

```
<volume>/clips/<episode_id>/<segment_id>.mp4        rectified output
<volume>/manifests/<name>.jsonl                     one row per segment
<volume>/datasets/<name>/                           trainer manifests + schema
```

Clips from older pipelines may be **content-hash named and flat**
(`audit_multicam_unblurred_undistorted_v1/<sha>.mp4`). Do not try to rename them
into an episode layout -- the hash is the original `source_row_id` and newer clips
have no equivalent. Carry `clip_volume` + `clip_path` per row instead.
