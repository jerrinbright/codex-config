---
name: split-stereo-hands-videos
description: Split stereo-hands episode directories that contain recording_primary.mp4 and recording_secondary.mp4 into the six corrected camera files expected by run_multi_camera_unified_v3.py. Use when the user provides a stereo-hands episode folder and asks to create, prepare, split, crop, or fix left/right/main/secondary camera videos.
---

# Split Stereo Hands Videos

Use this skill to create the six camera MP4s from a stereo-hands episode directory containing:

- `recording_primary.mp4`
- `recording_secondary.mp4`

Run the bundled splitter instead of rewriting ffmpeg crop commands by hand:

```bash
python ~/.codex/skills/split-stereo-hands-videos/scripts/split_stereo_hands_videos.py /path/to/episode
```

Add `--overwrite` only when replacing existing split camera files is intentional.

## Correct Crop Layout

Primary/main video must split as:

```text
recording_left_cam.mp4  = recording_primary.mp4 crop x=160,  y=0, w=1920, h=1200
recording_right_cam.mp4 = recording_primary.mp4 crop x=2080, y=0, w=1920, h=1200
```

This mapping already accounts for the left/right issue found in episode `6a02243c8382b275872d0069`; do not swap these files afterward.

Secondary video must split as:

```text
recording_secondary_cam_2.mp4 = recording_secondary.mp4 crop x=544,  y=0, w=640, h=480
recording_secondary_cam_3.mp4 = recording_secondary.mp4 crop x=1184, y=0, w=640, h=480
recording_secondary_cam_4.mp4 = recording_secondary.mp4 crop x=1824, y=0, w=640, h=480
recording_secondary_cam_5.mp4 = recording_secondary.mp4 crop x=2464, y=0, w=640, h=480
```

## Workflow

1. Confirm the episode directory contains `recording_primary.mp4` and `recording_secondary.mp4`.
2. Run the splitter script. Use `--overwrite` only if existing split outputs should be replaced.
3. Check the validation summary. Expected dimensions:
   - `recording_left_cam.mp4`, `recording_right_cam.mp4`: `1920x1200`
   - `recording_secondary_cam_2.mp4` through `recording_secondary_cam_5.mp4`: `640x480`
4. If the user will run inference next, use the split outputs directly; no manual left/right rename is needed.

## Notes

- The script requires `ffmpeg` and `ffprobe`.
- The script writes temporary files first, then atomically renames them to the final names.
- The script intentionally does not touch calibration files, manifests, previous output folders, or the original combined recordings.
