# Mecka Query Performance And Correctness

Use this reference for bulk MongoDB work, aggregates, delivery checks, annotation or embedding coverage, and ClickHouse queries. The performance figures below were measured on the home corpus of roughly 24 million episodes on 2026-08-16; treat them as useful order-of-magnitude evidence, not permanent guarantees.

## Core Rules

1. Inspect `collection.index_information()` before designing a bulk query.
2. Pass an explicit `hint` once the intended index is known. The planner has selected expensive plans silently on this corpus.
3. Prefer covering queries. A field in an index can often be read at hundreds of thousands of episodes per second; opening each document can reduce throughput to roughly 2,000 episodes per second.
4. For index-only queries, project `{ _id: 0 }` unless `_id` is part of the selected index or is required output. An implicit `_id` can force a document fetch and destroy covering performance.
5. Aggregate server-side. Return counts, sums, or grouped results rather than streaming millions of documents to a client loop.
6. Validate on one bounded shard before fanout. Cache expensive id sets and report episodes per second. Investigate bulk throughput below roughly 8,000 episodes per second.
7. Do not estimate a count by sampling when the exact indexed query is practical.

For one known episode, preserve BSON type and force the primary-key index:

```python
episode = db.episodes.find_one(
    {"_id": ObjectId(episode_id)},
    {"projectId": 1, "status": 1, "pipeline_results": 1},
    hint="_id_",
)
```

## Useful Covering Indexes

Confirm these names and key order against current `index_information()` before relying on them.

| Collection | Index | Useful for | Measured throughput |
|---|---|---|---:|
| `episodes` | `idx_project_intermediate_stub_duration` | Hours by project and episode grain | ~662k eps/s |
| `episodes` | `idx_episode_intermediate_parent` | Which parent episodes have intermediate children | ~87k eps/s |
| `episodes` | `qaExplorer_qaBatch_id_desc_full` | Episode ids in a QA batch, already sorted | ~228k eps/s |
| `delivered` | `delivered_to_timestamp_episode_distinct` | All ids shipped to a destination | ~216k eps/s |
| `delivered` | `delivered_episode_destination_idx` | Reverse lookup: destinations for known ids | ~283k eps/s |
| `delivered` | `uniq_exclusive_episode` | Exclusively delivered ids | ~22k eps/s |
| `episode_vlm_segments` | `idx_campaign_sampling_basis` | Delivery-batch membership to episode id | ~757k eps/s |
| `episode_vlm_segments` | `idx_vlm_deliverybatches_labelstatus_created` | Label-status grouping in a delivery batch | ~615k eps/s |
| `episode_annotations` | `idx_annotation_episodeid` | Annotation presence and per-episode counts | ~83k eps/s |
| `episode_embeddings` | `episode_id_lookup` | Embedding coverage for an id roster | ~43k eps/s warm |
| `episode_embeddings` | `episode_model` | Embedding models available per episode | ~66k eps/s |

Example of an index-only server-side aggregate:

```python
rows = db.episodes.aggregate(
    [
        {"$match": {"projectId": project_id, "isIntermediate": True}},
        {
            "$group": {
                "_id": "$isStub",
                "episodes": {"$sum": 1},
                "hours": {"$sum": "$duration"},
            }
        },
    ],
    hint="idx_project_intermediate_stub_duration",
)
```

An index that contains only the filter fields is not necessarily covering. Grouping, projected, and summed fields must also be in the index. Compound indexes used for id exports should include `_id` as a trailing key.

## Known Expensive Shapes

- `episode_vlm_segments` hours per delivery batch needs `videoDuration`, but the known campaign index does not cover it. Fetching full VLM documents can read hundreds of gigabytes.
- `episodes` hours split by QA status is not covered by the project/intermediate/stub/duration index. Prefer the current ClickHouse fact table when its semantics fit.
- Child hours per parent needs both `intermediate_parent_id` and `duration`; the parent-presence index does not cover duration.
- `episode_fake_task` user rollups have lacked a useful `userId` covering index.
- Reading embedding storage bucket/key fields can force full document fetches even when episode/model lookup is indexed.
- Tag-scoped delivery rosters may fetch every `delivered` document if tags are absent from the chosen index.

Do not create a new production index casually. Benchmark the query and account for existing index count and storage first.

## Silent-Zero And Wrong-Answer Traps

### Preserve BSON Types

`episode_fake_task.episodeId` is stored as `ObjectId`. A hex string can return zero rows with no error:

```python
oid = ObjectId(episode_id)
db.episode_fake_task.count_documents({"episodeId": oid})
```

Do not switch blindly to a snake-case mirror; mirrors may be incomplete.

`episode_embeddings.episode_id` has mixed string and `ObjectId` representations. Probe both forms in one indexed `$in`:

```python
keys = [ObjectId(episode_id), episode_id]
db.episode_embeddings.find(
    {"episode_id": {"$in": keys}},
    {"_id": 0, "episode_id": 1, "model.name": 1},
).hint("episode_model")
```

`delivered.episode_id` is also mixed. Reverse delivery checks must probe both forms.

### Avoid Broad Regex Destination Matching

A case-insensitive destination regex can absorb similarly named destinations and collapse index bounds. Use an explicit list whose semantics are visible:

```python
{"delivered_to": {"$in": ["botco", "botco-demo"]}}
```

### `$exists`, `null`, And Covering Queries

- `$exists` on a nested field can force document fetches even when an index contains the field. Prefer an indexed denormalized status/tier field when one represents the same state.
- Matching `null` also tends to require a fetch because it includes missing values. Prefer explicit positive flags such as `{isStub: False}` when the schema supports them.
- `episodes.updatedAt` is not reliably bumped by QA writes. Never use it as the timestamp of a QA decision.
- Fields such as `label_status` or old nested QA paths may be nearly empty after schema migrations. Verify current population before treating a zero as meaningful.

## Grain And Storage Sanity Checks

- `isIntermediate: true` records are pre-split intermediates and should not be counted as deliverable child hours. Keep selection grain and reporting grain explicit.
- Read storage paths from Mongo rather than constructing them. Assets may be nested under parent/child paths, and calibration can be keyed by device rather than episode.
- HEAD-check R2 objects before signing or publishing URLs. A completed pipeline status can coexist with missing declared outputs.

## ClickHouse

### Send SQL In The POST Body

Long SQL in a URL can fail as a bare HTTP 404. POST the statement as `text/plain` with the ClickHouse auth headers.

### Collapse Versioned Rows

Current fact tables can contain multiple versions per episode. Use `argMax(column, version) GROUP BY episode_id_string` or an appropriate `FINAL`; otherwise totals can be inflated.

### Delivery Source Of Truth

Do not use `delivery_fact_current` to decide whether an episode was delivered. Historical measurements found both stale deleted rows and missing delivered rows. Use MongoDB `delivered`, probing both `ObjectId` and string episode ids.

### Signals Missing Or Unreliable In ClickHouse

Use MongoDB for signals such as detailed hands reports, still/pause streaks, fake-task scores, and Molmo labeling state unless the current ClickHouse schema has been explicitly verified. Do not trust an `*_exists` convenience flag without checking it against the populated value field.

## Bulk-Run Telemetry

Every large query should log count, elapsed time, and throughput:

```python
t0 = time.time()
# bounded query or aggregate
elapsed = time.time() - t0
print(f"{count:,} episodes in {elapsed:.1f}s = {count / elapsed:,.0f} eps/s")
```

If performance is unexpectedly low, stop and inspect `explain("executionStats")` for `FETCH`, keys examined, documents examined, and the actual selected index before scaling out.
