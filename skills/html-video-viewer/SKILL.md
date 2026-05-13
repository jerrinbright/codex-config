---
name: html-video-viewer
description: "Create polished local HTML viewers for model/eval results with videos, segments, predictions, labels, confidence/top-k details, CSV/JSON data, and browser-pasteable local/tunnel links. Use when the user asks for an HTML viewer, result viewer, comparison viewer, video inspection page, full HTML link, local viewing link, Cloudflare tunnel link, or wants Codex to serve generated viewer artifacts."
---

# HTML Video Viewer

## Purpose

Build result-inspection viewers that are immediately usable in a browser, especially for video segment evals. Avoid past mistakes: wrong video seek encoding, non-pasteable paths, missing tunnel URL, stale cached HTML, broken symlink paths, and hidden confidence/top-k data.

## Required Workflow

1. Identify the data and media:
   - Locate `results.json`, `samples.json`, `episodes.json`, `summary.json`, `viewer_data.json`, CSVs, and media directories.
   - Preserve symlink-relative media paths when they are intentionally served through the viewer directory.
   - Check whether confidence/top-k data exists before claiming it is in the viewer.

2. Generate the viewer:
   - Prefer the bundled script: `scripts/build_video_viewer.py`.
   - Embed a compact `viewer_data.json` payload in `index.html` for easy static serving.
   - Also write standalone `viewer_data.json` and `scores.csv` next to the HTML.
   - Include segment seek/play controls, prediction, ground-truth/review notes when present, previous-context fields when present, and confidence/top-k fields when present.
   - If top-k data is missing, display `not captured`; do not invent confidences.

3. Validate the artifact:
   - Confirm `index.html` exists and contains expected rows/fields.
   - Confirm video URLs in `viewer_data.json` are browser-served paths, not accidental absolute `/tmp/...` paths unless intentionally using `file://`.
   - For video viewers, serve with byte-range support. Do not use plain `python -m http.server` for MP4 seeking.

4. Provide pasteable links:
   - Always give a full `file://.../index.html` link for local browser use.
   - If the user asks for a tunnel or a website-pasteable URL, start a range-aware local server and a Cloudflare tunnel, then provide the full `https://...trycloudflare.com/index.html` URL.
   - Verify:
     - `curl -I <tunnel>/index.html` returns `200`.
     - `curl -I -H 'Range: bytes=0-1023' <tunnel>/<video>` returns `206 Partial Content`.
   - If verification fails, fix it before responding.

## Script Usage

From the skill directory or by absolute path:

```bash
python3 skills/html-video-viewer/scripts/build_video_viewer.py \
  --input-dir /path/to/eval_output \
  --output-dir /path/to/viewer_dir \
  --title "Eval Results"
```

To generate and start a range-aware server plus Cloudflare tunnel:

```bash
python3 skills/html-video-viewer/scripts/build_video_viewer.py \
  --input-dir /path/to/eval_output \
  --output-dir /path/to/viewer_dir \
  --title "Eval Results" \
  --serve \
  --tunnel
```

The script prints:
- `HTML_FILE_URL=...`
- `LOCAL_HTTP_URL=...`
- `TUNNEL_URL=...` when tunnel startup succeeds
- PID/log paths for cleanup and debugging

## Viewer Quality Bar

- Use responsive two-pane layout: video left/top, segment list right/below.
- Clicking a segment seeks to `startSeconds` and pauses at `endSeconds`.
- Add a cache-busting query string after viewer regeneration.
- Render text with HTML escaping.
- Keep all file paths configurable; never hardcode project-local paths inside generated artifacts.
- Do not delete old media or outputs unless the user explicitly requests cleanup.

## Tunnel Notes

- Use `cloudflared tunnel --url http://127.0.0.1:<port> --no-autoupdate`.
- If `cloudflared` is missing, say so and still provide the `file://` and local HTTP links.
- Store logs/PIDs in `/tmp/codex_html_video_viewer/<viewer_slug>/`.
- If a port is busy, pick another port.

