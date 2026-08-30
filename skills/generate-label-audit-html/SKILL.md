---
name: generate-label-audit-html
description: Build portable, shareable HTML video-label audit viewers from JSON manifests. Use when Codex needs to create blinded or unblinded model-output audits, compare multiple model variants without revealing identities, collect per-segment approve/reject judgments with structured rejection reasons and notes, export audit CSVs, or package timestamped episode videos for human review.
---

# Generate Label Audit HTML

Create a self-contained audit HTML with exact segment playback, local progress persistence, structured rejection reasons, and CSV export.

## Workflow

1. Read `references/input-schema.md` when preparing a new input manifest.
2. Ensure every row has a browser-reachable video URL. Prefer signed HTTPS URLs with byte-range support.
3. Normalize model outputs into the canonical JSON schema. Represent each model/condition as a separate row with the same `source_episode_id` and a private `variant` value.
4. Build the viewer:

```bash
python3 "$HOME/.codex/skills/generate-label-audit-html/scripts/build_label_audit.py" \
  --input /path/to/audit_manifest.json \
  --output /path/to/audit.html \
  --title "Label audit"
```

The builder blinds and shuffles by default. It writes a sibling `*.private_decoder.json` mapping audit IDs back to source episodes and variants. Use `--no-blind` only when reviewers should see source IDs; use `--no-shuffle` only when order is meaningful.
The viewer has no provenance footer by default. Add a nonempty top-level `provenance` list only when the audit explicitly needs one.

5. Run the same command with `--verify` after generation, or run `scripts/verify_label_audit.py --html ...` independently.
6. For remote videos, verify representative origins return `206 Partial Content` for range requests. Do not claim seeking works if this check fails.
7. Share only the HTML. Keep the private decoder separate from auditors.

## Audit Semantics

- Approve completes a segment immediately.
- Reject requires one or more reasons selected from visible checkboxes: missing action, wrong action, wrong object, wrong hand, added action, wrong order, plural, unclear video, or other.
- A rejected segment without a reason remains pending and prevents episode completion.
- Notes are optional.
- Browser state persists in `localStorage`; CSV export includes `verdict`, `rejection_reason`, and `notes`. Multiple reasons are serialized in deterministic display order with `; ` separators.
- Clicking a timestamp seeks, autoplays, and stops at the exact segment end.

### Episode video, timing, and captions

- Treat `duration` as the **episode/source-video duration** unless the manifest explicitly documents a different meaning. Do not compare it to a segment end or use it as a segment duration.
- For a timed segment, the segment duration is `end - start`. Display the row's `start` and `end` against the same full-episode signed video URL used by the row. Do not silently substitute a different recording, camera, or local Modal path.
- Validate timing before delivery: representative timed rows must use the expected episode video, have `0 <= start < end`, and have no unexplained overlaps or gaps within an ordered timed episode. If the source has partial timing, preserve that fact rather than inventing boundaries.
- Rows with missing `start` or `end` must be marked as having unavailable segment timing. The viewer may still show the full episode video and episode duration, but must not claim that playback is positioned on the exact segment. Never fabricate timestamps from segment indices or episode duration.
- The on-video caption must be keyed by the selected segment row, not by a fixed first row. Render candidate labels on separate stacked lines as `A - ...` and `B - ...`.
- Selecting a segment must immediately update the caption. For timed rows it should also seek to `start`, autoplay, and use that row as the loop target. While playback is seeking, keep the manually selected caption pinned until the selected row becomes active; an early `timeupdate` at `0` must not revert the caption to segment 0. For untimed rows, keep the selected caption visible and do not pretend the video time identifies that row.
- Playback-driven caption updates may resume after the selected timed row becomes active. Seeking through the timebar must clear the pinned selection and loop target so playback captions follow the newly selected time.
- If a segment has no timestamp, do not create a misleading seek button. Show an explicit `segment timestamps unavailable` state and retain the selected row's caption during playback.

### A/B comparison audits

For audits comparing two candidate labels, use four mutually exclusive decisions:

- `A`: candidate A is more correct; this is a complete decision and does not require a rejection reason.
- `B`: candidate B is more correct; this is a complete decision and does not require a rejection reason.
- `=`: both candidates are correct; this is a complete decision and does not require a rejection reason.
- `X`: both candidates are incorrect; show the rejection-reason checklist and require at least one reason before considering the row complete.

Never show a rejection-reason prompt for `B`: choosing B means B was accepted, not rejected. If a reviewer changes an `X` decision to `A`, `B`, or `=`, clear any previously saved rejection reasons. The audit instructions and CSV export must use the same semantics.

## Output Checks

Require all of the following before delivery:

- Expected run and segment counts match.
- Audit IDs are unique.
- Every label is nonempty and every time range is valid.
- Every video URL is nonempty.
- Model variant names do not appear in blinded HTML.
- JavaScript syntax passes when Node.js is available.
- The private decoder has one entry per audit run.

Use `assets/audit_viewer.html` as the stable UI template. Modify the builder or template only when the audit behavior itself changes.
