---
name: mongo-episode-query-discovery
description: Discover and construct correct, efficient MongoDB and ClickHouse queries for Mecka episode data. Use when the user asks how to find/query episodes, projects, UMI, mono, multicam, Basalt, HLOC, hands, body, video, trajectory, delivery, annotations, embeddings, or other outputs; when BSON type or index choice may cause slow or silently empty results; or when a known episode id must be resolved to reusable query fields.
---

# Mongo Episode Query Discovery

## Core Rule

Anchor broad `episodes` queries with an indexed selector before adding semantic or file-existence filters. Pass an explicit index `hint` for bulk queries after checking `index_information()`. Prefer:

```js
{ projectId: ObjectId("..."), ...requested_field_filters }
```

Avoid starting with unindexed fields such as `isUmi`, nested `pipeline_results.*`, or `$exists` across all episodes.

For a known episode id, cast the hex string to `ObjectId`, query by `_id`, and explicitly hint `_id_`. Do not pass a string where the stored field is an `ObjectId`; MongoDB can return a confident zero rather than an error.

For aggregates, aggregate on the server and return only the result. Do not stream documents to the client to count or sum them.

## Workflow

1. Identify whether the user has a known episode id.
   - If yes, fetch that single `episodes` doc by `_id` and inspect `projectId`, hardware flags, pipeline keys, and requested file fields.
   - If no, start with `projects` metadata and search by `name`, `description`, `tags`, `hardware`, `captureEnvironmentType`, and `status`.

2. If the user asks for a broad capture family such as "mono", do not silently choose one project.
   - List matching candidate projects first.
   - Include `_id`, `name`, `status`, `hardware`, `captureEnvironmentType`, and a short distinguishing description.
   - Ask the user which project to use, unless the user explicitly says to query all matching projects.
   - If querying all matching projects, use `projectId: { $in: [...] }` and say that this trades clarity for coverage.

3. Confirm the selected project metadata.
   - Query `db.projects.findOne({ _id: ObjectId(projectId) })`.
   - Use `hardware.headgear`, `hardware.wrist`, `hardware.hand`, `captureEnvironmentType`, `name`, and `description` to infer the intended capture family.

4. Inspect upstream-written fields on representative episodes.
   - For one known or sampled episode, inspect top-level flags and `pipeline_results` keys.
   - Treat upstream pipeline fields as the source of truth for available files: sync/split/HLOC/hands/body/QA services write these fields.
   - When the user asks for a specific pipeline such as Basalt, HLOC, hands, or body, inspect `pipeline_results.<pipeline>` for that selected project before writing the final query.
   - Prefer fetching a few samples with a narrow projection over scanning/counting nested fields globally.

5. Build the final filter.
   - Always include `projectId` when possible.
   - Add semantic flags only after the project anchor, for example `isUmi: true`, `isStereo: { $ne: true }`, or `status: "VALIDATED"`.
   - Add requested file-existence filters only for files the user actually needs.

6. Return both filter and projection.
   - Explain that the filter selects documents.
   - Explain that the projection only controls returned fields and keeps output small.

7. Validate performance shape.
   - Mention whether the query is anchored by indexed `projectId` or `_id`, and state the chosen hint for bulk work.
   - Use a covering index when the requested filter, grouping, and aggregate fields permit it.
   - For index-only queries, explicitly project `{ _id: 0 }` unless `_id` is part of the selected index or is the requested output.
   - If the user needs repeated large queries, recommend a compound index on the project and requested pipeline status/file key.
   - Validate a representative shard before fanout, cache expensive id rosters, and report rows or episodes per second. If a bulk run is unexpectedly below roughly 8,000 episodes/s, stop and inspect the plan rather than waiting blindly.

## Mono Pipeline Discovery

For requests like "get me mono Basalt", "mono HLOC", "mono hands", or "mono body":

1. List mono-like projects first:

```js
db.projects.find(
  {
    $or: [
      { "hardware.headgear": "MONO_IPHONE" },
      { name: /mono/i },
      { description: /mono|iphone/i },
      { tags: /mono|iphone/i }
    ]
  },
  { name: 1, description: 1, hardware: 1, captureEnvironmentType: 1, status: 1, tags: 1 }
)
```

2. Ask the user to choose a project id. Do not default to `Home / Mono` unless the user chooses it or provided a known episode from that project.

3. After the user chooses, sample that project's pipeline subdocument. Replace `basalt` with the requested pipeline:

```js
db.episodes.find(
  {
    projectId: ObjectId("PROJECT_ID"),
    "pipeline_results.basalt": { $exists: true }
  },
  {
    video_1_h264_480p_r2: 1,
    "pipeline_results.basalt": 1
  }
).limit(3)
```

If the nested `$exists` sample is slow, ask for a known episode or sample project docs by indexed `_id`/`projectId` and inspect `pipeline_results` client-side. Once the exact output key is known, write the final query with that key.

## Query Patterns

Use this shape for one known episode. `find()` is intentional because it exposes `hint()` in a reusable shell example:

```js
db.episodes.find(
  { _id: ObjectId("EPISODE_ID") },
  {
    projectId: 1,
    isUmi: 1,
    isStereo: 1,
    isMulticam: 1,
    isIntermediate: 1,
    status: 1,
    video_1: 1,
    video_1_h264_480p_r2: 1,
    pipeline_results: 1
  }
).hint("_id_").limit(1)
```

Use this shape to discover project ids:

```js
db.projects.find(
  {
    $or: [
      { name: /mono|umi|multicam|wrist|hloc/i },
      { description: /mono|umi|multicam|wrist|hloc/i },
      { tags: /mono|umi|multicam|wrist|hloc/i },
      { "hardware.headgear": /MONO|MULTICAM/i },
      { "hardware.hand": /UMI/i }
    ]
  },
  { name: 1, description: 1, hardware: 1, captureEnvironmentType: 1, status: 1, tags: 1 }
)
```

Use this shape for file-ready output queries:

```js
db.episodes.find(
  {
    projectId: ObjectId("PROJECT_ID"),
    "pipeline_results.some_pipeline.status": "completed",
    "pipeline_results.some_pipeline.file_key": { $exists: true, $nin: [null, ""] }
  },
  {
    video_1_h264_480p_r2: 1,
    "pipeline_results.some_pipeline.file_key": 1
  }
)
```

Default file-ready projections should include only `_id`, the requested video/file fields, and the requested pipeline output keys. Add context fields such as `label`, `task_id`, `task_desc`, or `duration` only when the user explicitly asks for them.

## Field Heuristics

Read [episode-query-fields.md](references/episode-query-fields.md) when the user asks about known Mecka project ids, UMI, mono/HLOC, common video fields, or output file keys.

Read [query-performance.md](references/query-performance.md) before bulk exports, aggregates, delivery checks, annotation/embedding coverage queries, ClickHouse work, or any query where BSON type, covering-index behavior, or a silent zero could affect correctness.

## Communication

- Be precise about what is known from metadata versus inferred from episode fields.
- Do not claim a field is indexed unless you checked indexes or the conversation provides that fact.
- If a query may be expensive, say why and give a safer indexed version.
- If downloading files, convert `r2://bucket/key` to `rclone` form `r2:bucket/key`.
