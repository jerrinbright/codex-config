# Episode Query Fields

Use these as starting points, not as universal schema guarantees. Confirm on current data when accuracy matters.

## Collections

- `mecka-ai.projects`: project metadata. Use this to discover project ids.
- `mecka-ai.episodes`: episode docs and pipeline output file keys.

## Known Project Metadata Examples

## Mono Project Discovery

When the user asks for "mono" without a known episode id or exact project id, list matching projects before constructing the final episode query.

Use project metadata:

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

Then ask the user to pick a project id. Mono-like projects may differ by environment, hardware, delivery rules, and pipeline outputs:

- Home / Mono
- Business / Mono
- Studio / Mono + Insta360 WC
- Naruto Mono Wrist Cam
- Mono + EgoExo / CV

### Naruto Multicam UMI

Project id:

```text
69d43e41dd2a631987d8c863
```

Metadata:

```json
{
  "name": "[EXCLUSIVE] Naruto Multicam Umi",
  "description": "Nvidia-delivered multicam umi episodes from Business Multicam Capture",
  "captureEnvironmentType": "MIXED",
  "hardware": {
    "headgear": "MULTICAM",
    "hand": "UMI"
  }
}
```

Practical query:

```js
{
  projectId: ObjectId("69d43e41dd2a631987d8c863"),
  isUmi: true
}
```

UMI video/result file fields:

```js
synced_combined_key
pipeline_results.umi_gripper.storage_urls.umi_camera_cleaned_interpolated
pipeline_results.umi_gripper.storage_urls.triangulated_json
pipeline_results.umi_gripper.storage_urls.left_2d_json
pipeline_results.umi_gripper.storage_urls.right_2d_json
```

### Home / Mono

Project id:

```text
689bd9bed8331067ebca667e
```

Metadata:

```json
{
  "name": "Home / Mono",
  "description": "Home Tasks recorded with iPhones (mobile)",
  "hardware": {
    "headgear": "MONO_IPHONE"
  },
  "captureEnvironmentType": "HOME"
}
```

Example mono episode:

```text
69efc1322d38820e4a3cfa76
```

Common mono video fields:

```js
video_1
video_1_h264_480p_r2
video_1_h264_720p_r2
```

Common HLOC fields:

```js
pipeline_results.hloc.status
pipeline_results.hloc.results_key
pipeline_results.hloc.transformations_key
pipeline_results.hloc.transformations_full_key
pipeline_results.hloc.interpolated_trajectory_key
pipeline_results.hloc.combined_imu_key
pipeline_results.hloc.egomotion_client_key
pipeline_results.hloc.file_keys
```

Common Basalt fields:

```js
pipeline_results.basalt.status
pipeline_results.basalt.storage_keys.interpolated_trajectory
pipeline_results.basalt.storage_keys.trajectory
pipeline_results.basalt.storage_keys.adjusted_trajectory
pipeline_results.basalt.storage_keys.keyframeTrajectory
pipeline_results.basalt.storage_keys.bag_imu_csv
pipeline_results.basalt.post_processing.combined_imu.combined_imu_uri
pipeline_results.basalt.post_processing.height_calibrated_trajectory.output_trajectory_uri
pipeline_results.basalt.post_processing.trajectory_qa.trajectory_s3_key
pipeline_results.basalt.post_processing.trajectory_qa.output_uri
```

Verified Basalt sample key shape:

```text
r2://data/episodes/<episode_id>/basalt/interpolated_trajectory.txt
```

Practical query for a selected mono project with Basalt trajectory:

```js
db.episodes.find(
  {
    projectId: ObjectId("PROJECT_ID"),
    "pipeline_results.basalt.status": "completed",
    "pipeline_results.basalt.storage_keys.interpolated_trajectory": { $exists: true, $nin: [null, ""] }
  },
  {
    video_1_h264_480p_r2: 1,
    "pipeline_results.basalt.storage_keys.interpolated_trajectory": 1,
    "pipeline_results.basalt.storage_keys.trajectory": 1,
    "pipeline_results.basalt.post_processing.combined_imu.combined_imu_uri": 1
  }
)
```

Important: inspect `pipeline_results.<pipeline>` for the selected project before finalizing the exact requested file key. Do not assume every mono project has the same Basalt/HLOC/hands/body outputs.

Practical query for mono HLOC with trajectory:

```js
db.episodes.find(
  {
    projectId: ObjectId("689bd9bed8331067ebca667e"),
    "pipeline_results.hloc.status": "completed",
    "pipeline_results.hloc.interpolated_trajectory_key": { $exists: true, $nin: [null, ""] }
  },
  {
    video_1_h264_480p_r2: 1,
    "pipeline_results.hloc.interpolated_trajectory_key": 1
  }
)
```

Default projections should stay file-focused. Add context fields such as `label`, `task_id`, `task_desc`, or `duration` only when the user asks for them.

If the nested trajectory existence check is slow, add an `_id` lower bound for a known newer batch:

```js
{
  _id: { $gte: ObjectId("69e000000000000000000000") },
  projectId: ObjectId("689bd9bed8331067ebca667e"),
  "pipeline_results.hloc.status": "completed",
  "pipeline_results.hloc.interpolated_trajectory_key": { $exists: true, $nin: [null, ""] }
}
```

## Capture Family Signals

Use project metadata first, then confirm on episodes.

### UMI

Project metadata:

```js
"hardware.hand": "UMI"
```

Episode signals:

```js
isUmi: true
tools: ["umi_grippers"]
reviewMode: "MULTICAM_WRIST_UMI"
pipeline_results.umi_gripper
```

### Mono

Project metadata:

```js
"hardware.headgear": "MONO_IPHONE"
```

Episode signals:

```js
isStereo: { $ne: true }
isMulticam: { $ne: true }
video_1
video_1_h264_480p_r2
```

`{ $ne: true }` matches false, null, and missing fields. Use it when older non-stereo docs may not have explicit booleans.

### Multicam / Stereo

Project metadata:

```js
"hardware.headgear": "MULTICAM"
```

Episode signals:

```js
isStereo: true
isMulticam: true
stereoUploadId
synced_combined_key
synced_secondary_key
left_video_key
right_video_key
cam3_video_key
cam5_video_key
```

## Projection Reminder

The second object in `find(filter, projection)` is not a filter. It only controls returned fields.

Example:

```js
db.episodes.find(
  { projectId: ObjectId("...") },
  { video_1_h264_480p_r2: 1, "pipeline_results.hloc": 1 }
)
```

## R2 Path Reminder

Mongo stores internal object URIs like:

```text
r2://data/episodes/.../video_480p.mp4
```

For `rclone`, convert to:

```text
r2:data/episodes/.../video_480p.mp4
```
