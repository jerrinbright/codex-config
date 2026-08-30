# Input Schema

The builder accepts one JSON object with a `rows` array.

```json
{
  "title": "Optional title",
  "client": "optional project name",
  "delivery_date": "2026-08-12",
  "provenance": ["Optional private-safe note shown in the footer."],
  "rows": [
    {
      "source_episode_id": "episode-123",
      "variant": "production-map",
      "user_task_id": "task-group-7",
      "task_id": "make coffee",
      "description": "kitchen task",
      "video_url": "https://signed.example/video.mp4",
      "video_uri": "r2://bucket/video.mp4",
      "duration": 42.5,
      "segments": [
        {
          "index": 0,
          "start": 1.2,
          "end": 4.8,
          "label": "pick up mug with right hand",
          "confidence": 0.91
        }
      ]
    }
  ]
}
```

## Required Fields

Per row:

- `source_episode_id`: Stable source identity.
- `video_url`: Browser-reachable MP4 URL. Signed URLs are accepted.
- `segments`: Nonempty list.

Per segment:

- `index`: Integer unique within the row.
- `start`: Finite seconds, greater than or equal to zero.
- `end`: Finite seconds strictly greater than `start`.
- `label`: Nonempty candidate label shown to the auditor.

## Optional Fields

- `variant`: Model or experimental arm. It is written only to the private decoder when blinding is enabled.
- `audit_id`: Explicit audit identity. Otherwise the builder generates a deterministic ID.
- `user_task_id`, `task_id`, `description`, `video_uri`, `duration`.
- Segment `confidence`: Number or null. Never fabricate it.
- Row `private_metadata`: Any JSON object to preserve only in the private decoder.

## Multiple Variants

Add one row per `(source_episode_id, variant)`. Reuse the same video and segment boundaries while changing candidate labels. The default blinded build randomizes all rows and exposes only generated audit IDs.

## Video Requirements

Use H.264 MP4 where possible. The host should support byte ranges:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' \
  -H 'Range: bytes=0-1023' 'https://signed.example/video.mp4'
```

Expected status: `206`.
