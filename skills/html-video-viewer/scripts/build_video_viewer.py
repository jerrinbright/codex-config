#!/usr/bin/env python3
"""Build and optionally serve a static HTML video-result viewer.

The script accepts either:
- an eval directory containing results.json and optional episodes.json/summary.json
- a prebuilt viewer_data.json

It writes index.html, viewer_data.json, and scores.csv. When --serve is used it
starts this script's range-aware HTTP server in the background. When --tunnel is
also used it starts cloudflared and prints a browser-pasteable tunnel URL.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import mimetypes
import os
import posixpath
import re
import shutil
import socket
import subprocess
import sys
import time
from collections import defaultdict
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit


VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
MODEL_OUTPUT_KEYS = ("pred", "label", "vlmLabel", "rawPrediction")


def load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def relpath_preserve_symlink(path: Path, start: Path) -> str:
    return os.path.relpath(path.absolute(), start.absolute()).replace(os.sep, "/")


def served_media_path(path: Path, input_dir: Path, output_dir: Path) -> str:
    rel_to_output = relpath_preserve_symlink(path, output_dir)
    if not rel_to_output.startswith("../"):
        return rel_to_output
    rel_to_input = relpath_preserve_symlink(path, input_dir)
    if rel_to_input.startswith("../"):
        return rel_to_output
    link = output_dir / "eval_data"
    if not link.exists():
        link.symlink_to(input_dir.absolute(), target_is_directory=True)
    elif not link.is_symlink() and not link.is_dir():
        raise RuntimeError(f"Cannot create media symlink because path exists: {link}")
    return f"eval_data/{rel_to_input}"


def find_model_key(rows: list[dict[str, Any]], explicit: str | None) -> str | None:
    if explicit:
        return explicit
    for row in rows:
        for key, value in row.items():
            if isinstance(value, dict) and any(k in value for k in MODEL_OUTPUT_KEYS):
                return key
    return None


def model_output(row: dict[str, Any], model_key: str | None) -> dict[str, Any]:
    if model_key and isinstance(row.get(model_key), dict):
        return row[model_key]
    return row


def first_present(row: dict[str, Any], names: tuple[str, ...], default: Any = "") -> Any:
    for name in names:
        value = row.get(name)
        if value is not None and value != "":
            return value
    return default


def confidence_payload(out: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    details = row.get("confidenceDetails") if isinstance(row.get("confidenceDetails"), dict) else {}
    conf = row.get("confidence") if isinstance(row.get("confidence"), dict) else {}
    return {
        "avg_conf": first_present(out, ("avg_conf", "avg"), conf.get("avg")),
        "min_conf": first_present(out, ("min_conf", "min"), conf.get("min")),
        "geo_mean_conf": first_present(out, ("geo_mean_conf", "geo_mean"), conf.get("geo_mean")),
        "words": out.get("words") if isinstance(out.get("words"), list) else details.get("words", []),
        "tokens": out.get("tokens") if isinstance(out.get("tokens"), list) else details.get("tokens", []),
    }


def top3_summary(words: list[dict[str, Any]], limit: int = 3) -> str:
    parts: list[str] = []
    for word in words[:limit]:
        top3 = word.get("top3") if isinstance(word.get("top3"), list) else []
        if not top3:
            continue
        choices = []
        for item in top3[:3]:
            token = str(item.get("token") or "").strip() or "<blank>"
            choices.append(f"{token} {as_float(item.get('prob')):.3f}")
        parts.append(f"{word.get('word') or '<blank>'}: {', '.join(choices)}")
    return " | ".join(parts)


def find_video_for_episode(input_dir: Path, episode_id: str, episodes_meta: dict[str, Any]) -> str:
    meta = episodes_meta.get(episode_id) if isinstance(episodes_meta.get(episode_id), dict) else {}
    for key in ("full_video", "fullVideo", "video", "video_path", "videoPath"):
        value = meta.get(key)
        if isinstance(value, str) and value:
            return value
    media_root = input_dir / "viewer_media" / "episodes" / episode_id
    if media_root.exists():
        for path in sorted(media_root.rglob("*")):
            if path.suffix.lower() in VIDEO_EXTS:
                return str(path.relative_to(input_dir))
    return ""


def build_payload(input_dir: Path, output_dir: Path, title: str, model_key: str | None) -> dict[str, Any]:
    viewer_data = input_dir / "viewer_data.json"
    if viewer_data.exists():
        data = load_json(viewer_data)
        data.setdefault("title", title)
        return data

    results = load_json(input_dir / "results.json")
    if not isinstance(results, list):
        raise ValueError("results.json must be a list of rows")
    episodes_meta = load_json(input_dir / "episodes.json") if (input_dir / "episodes.json").exists() else {}
    summary = load_json(input_dir / "summary.json") if (input_dir / "summary.json").exists() else {}
    resolved_model_key = find_model_key(results, model_key or summary.get("model_key"))

    rows_by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for idx, row in enumerate(results):
        if not isinstance(row, dict):
            continue
        episode_id = str(first_present(row, ("episode_id", "episodeId", "video_id", "videoId"), "episode"))
        out = model_output(row, resolved_model_key)
        conf = confidence_payload(out, row)
        start = as_float(first_present(row, ("segment_start_s", "segment_start_seconds", "startSeconds", "start", "start_s"), 0))
        end = as_float(first_present(row, ("segment_end_s", "segment_end_seconds", "endSeconds", "end", "end_s"), start))
        segment = {
            "row_id": str(first_present(row, ("row_id", "review_id", "_id", "id"), idx)),
            "segment_index": as_int(first_present(row, ("segment_index", "index"), idx), idx),
            "start": start,
            "end": end,
            "duration": as_float(first_present(row, ("duration_s", "duration", "durationSeconds"), max(end - start, 0))),
            "pred": str(first_present(out, ("pred", "label", "vlmLabel", "rawPrediction"), "")),
            "gt": str(first_present(row, ("gt", "segment_label", "label", "campaign_label"), "")),
            "review_decision": str(first_present(row, ("review_decision", "decision"), "")),
            "review_notes": str(first_present(row, ("review_notes", "notes"), "")),
            "previous_model_prediction_input": str(first_present(row, ("previous_model_prediction_input", "previousLabelInput"), "")),
            "model_conf": conf,
            "top3_summary": top3_summary(conf["words"] if isinstance(conf["words"], list) else []),
        }
        rows_by_episode[episode_id].append(segment)

    episodes: list[dict[str, Any]] = []
    for episode_id in sorted(rows_by_episode):
        segments = sorted(rows_by_episode[episode_id], key=lambda r: (r["segment_index"], r["start"]))
        video_value = find_video_for_episode(input_dir, episode_id, episodes_meta)
        full_video = ""
        if video_value:
            video_path = Path(video_value)
            full_video_path = video_path if video_path.is_absolute() else input_dir / video_path
            full_video = served_media_path(full_video_path, input_dir, output_dir)
        episodes.append(
            {
                "episode_id": episode_id,
                "full_video": full_video,
                "duration_s": max((as_float(s["end"]) for s in segments), default=0.0),
                "n_segments": len(segments),
                "task_desc": str((episodes_meta.get(episode_id) or {}).get("task_desc", "")) if isinstance(episodes_meta, dict) else "",
                "objects": str((episodes_meta.get(episode_id) or {}).get("objects", "")) if isinstance(episodes_meta, dict) else "",
                "segments": segments,
            }
        )

    return {
        "title": title,
        "summary": summary,
        "model_key": resolved_model_key,
        "n_segments": sum(len(ep["segments"]) for ep in episodes),
        "episodes": episodes,
    }


def render_html(payload: dict[str, Any]) -> str:
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    title = html.escape(str(payload.get("title") or "Video Result Viewer"))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{ --bg:#f6f7f9; --panel:#fff; --line:#d9dee7; --ink:#1f2630; --muted:#667386; --accent:#146c94; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:var(--ink); background:var(--bg); font-size:14px; }}
    header {{ padding:14px 18px; background:var(--panel); border-bottom:1px solid var(--line); }}
    h1 {{ margin:0 0 8px; font-size:20px; }}
    .summary {{ display:flex; gap:8px; flex-wrap:wrap; color:var(--muted); }}
    .pill {{ border:1px solid var(--line); border-radius:999px; padding:4px 9px; background:#fbfcfe; }}
    .tabs {{ display:flex; gap:8px; overflow-x:auto; padding:10px 18px; border-bottom:1px solid var(--line); background:#eef2f6; }}
    .tab {{ min-width:210px; border:1px solid var(--line); background:#fff; border-radius:7px; padding:8px 10px; text-align:left; cursor:pointer; }}
    .tab.active {{ border-color:var(--accent); background:#e8f4f8; outline:2px solid rgba(20,108,148,.16); }}
    .tab strong {{ display:block; font-size:12px; overflow:hidden; text-overflow:ellipsis; }}
    .tab span {{ color:var(--muted); font-size:12px; }}
    main {{ display:grid; grid-template-columns:minmax(420px,1.15fr) minmax(420px,.85fr); gap:16px; padding:16px 18px 24px; align-items:start; }}
    .video-pane {{ position:sticky; top:12px; min-width:0; }}
    .video-wrap {{ background:#101318; border-radius:8px; overflow:hidden; border:1px solid #101318; }}
    video {{ display:block; width:100%; max-height:calc(100vh - 310px); background:#101318; }}
    .now,.segments {{ border:1px solid var(--line); border-radius:8px; background:#fff; overflow:hidden; }}
    .now {{ margin-top:12px; padding:12px; }}
    h2 {{ margin:0 0 8px; font-size:15px; }}
    .label {{ margin-top:8px; color:var(--muted); font-size:12px; text-transform:uppercase; }}
    .value {{ margin-top:2px; overflow-wrap:anywhere; }}
    .segments-head {{ padding:12px; border-bottom:1px solid var(--line); display:flex; justify-content:space-between; gap:10px; align-items:center; }}
    .segment-list {{ max-height:calc(100vh - 190px); overflow:auto; }}
    .segment {{ display:block; width:100%; border:0; border-bottom:1px solid var(--line); background:#fff; color:var(--ink); text-align:left; padding:10px 12px; cursor:pointer; }}
    .segment:hover {{ background:#f5f8fa; }}
    .segment.active {{ background:#e8f4f8; box-shadow:inset 4px 0 0 var(--accent); }}
    .seg-top {{ display:flex; justify-content:space-between; gap:10px; align-items:center; margin-bottom:6px; }}
    .time {{ font-weight:700; font-variant-numeric:tabular-nums; }}
    .badge {{ border:1px solid var(--line); border-radius:999px; padding:2px 7px; font-size:11px; white-space:nowrap; }}
    .pred {{ font-weight:650; overflow-wrap:anywhere; }}
    .gt,.notes,.prev,.score,.conf-row {{ margin-top:4px; color:var(--muted); font-size:12px; overflow-wrap:anywhere; }}
    .conf-grid {{ margin-top:6px; display:grid; gap:6px; }}
    .conf-word {{ border:1px solid var(--line); border-radius:7px; padding:6px 8px; background:#fbfcfe; }}
    .conf-word strong {{ display:block; margin-bottom:3px; font-size:12px; color:var(--ink); }}
    .conf-choice {{ display:inline-block; margin:2px 5px 2px 0; padding:2px 6px; border-radius:999px; background:#eef2f6; color:#3c4858; font-size:12px; }}
    @media (max-width:900px) {{ main {{ grid-template-columns:1fr; padding:12px; }} .video-pane {{ position:static; }} video {{ max-height:none; }} .segment-list {{ max-height:none; }} }}
  </style>
</head>
<body>
  <header><h1>{title}</h1><div class="summary" id="summary"></div></header>
  <nav class="tabs" id="tabs"></nav>
  <main>
    <section class="video-pane">
      <div class="video-wrap"><video id="video" controls preload="metadata"></video></div>
      <div class="now">
        <h2 id="nowTitle">Selected Segment</h2>
        <div class="label">Prediction</div><div class="value" id="nowPred"></div>
        <div class="label">Model Confidence</div><div class="value" id="nowConf"></div>
        <div class="label">Top 3 Confidence</div><div class="value" id="nowTop3"></div>
        <div class="label">Ground Truth / Campaign Label</div><div class="value" id="nowGt"></div>
        <div class="label">Review Notes</div><div class="value" id="nowNotes"></div>
        <div class="label">Previous Prediction Context</div><div class="value" id="nowPrev"></div>
      </div>
    </section>
    <aside class="segments">
      <div class="segments-head"><h2 id="segmentsTitle">Segments</h2><span class="pill">click row: play segment then pause</span></div>
      <div class="segment-list" id="segmentList"></div>
    </aside>
  </main>
  <script id="viewer-data" type="application/json">{data_json}</script>
  <script>
    const payload = JSON.parse(document.getElementById('viewer-data').textContent);
    const video = document.getElementById('video');
    const tabs = document.getElementById('tabs');
    const list = document.getElementById('segmentList');
    let activeSegment = null;
    let stopAtEnd = false;
    let activeEpisode = null;
    let pendingSeek = null;
    const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
    const fmt = s => {{
      s = Math.max(0, Number(s) || 0);
      const whole = Math.floor(s);
      return `${{Math.floor(whole/60)}}:${{String(whole%60).padStart(2,'0')}}.${{Math.floor((s-whole)*10)}}`;
    }};
    const fmtConf = v => Number.isFinite(Number(v)) ? Number(v).toFixed(3) : 'not captured';
    function renderTop3(seg) {{
      const words = (seg.model_conf && Array.isArray(seg.model_conf.words)) ? seg.model_conf.words : [];
      const rows = words.filter(w => Array.isArray(w.top3) && w.top3.length).slice(0, 12).map(w => {{
        const choices = w.top3.slice(0, 3).map(c => `<span class="conf-choice">${{esc(String(c.token || '').trim() || '<blank>')}} ${{fmtConf(c.prob)}}</span>`).join('');
        return `<div class="conf-word"><strong>${{esc(w.word || '<blank>')}} · ${{fmtConf(w.prob)}}</strong>${{choices}}</div>`;
      }});
      if (!rows.length) return '<span class="conf-row">not captured</span>';
      return `<div class="conf-grid">${{rows.join('')}}</div>`;
    }}
    document.getElementById('summary').innerHTML = [
      `${{payload.episodes.length}} episodes`,
      `${{payload.n_segments}} segments`,
      payload.model_key ? `model ${{payload.model_key}}` : 'model auto-detected'
    ].map(v => `<span class="pill">${{esc(v)}}</span>`).join('');
    function setNow(seg) {{
      document.getElementById('nowTitle').textContent = `Segment ${{seg.segment_index}} · ${{fmt(seg.start)}} - ${{fmt(seg.end)}}`;
      document.getElementById('nowPred').textContent = seg.pred || '(empty)';
      document.getElementById('nowConf').textContent = `avg ${{fmtConf(seg.model_conf?.avg_conf)}} · min ${{fmtConf(seg.model_conf?.min_conf)}} · geo ${{fmtConf(seg.model_conf?.geo_mean_conf)}}`;
      document.getElementById('nowTop3').innerHTML = renderTop3(seg);
      document.getElementById('nowGt').textContent = seg.gt || '(empty)';
      document.getElementById('nowNotes').textContent = seg.review_notes || '(none)';
      document.getElementById('nowPrev').textContent = seg.previous_model_prediction_input || '(empty)';
    }}
    function applyPendingSeek() {{
      if (pendingSeek === null) return;
      if (video.readyState < 1) {{ video.load(); return; }}
      const target = pendingSeek;
      pendingSeek = null;
      video.currentTime = target;
      const p = video.play();
      if (p && p.catch) p.catch(() => {{}});
    }}
    function seek(seg, row) {{
      activeSegment = seg;
      stopAtEnd = true;
      document.querySelectorAll('.segment.active').forEach(el => el.classList.remove('active'));
      row.classList.add('active');
      setNow(seg);
      video.pause();
      pendingSeek = Math.max(0, Number(seg.start) || 0);
      applyPendingSeek();
    }}
    function renderEpisode(idx) {{
      const ep = payload.episodes[idx];
      stopAtEnd = false;
      activeEpisode = ep;
      activeSegment = null;
      pendingSeek = null;
      document.querySelectorAll('.tab').forEach((el, i) => el.classList.toggle('active', i === idx));
      video.pause();
      if (ep.full_video) video.src = `${{ep.full_video}}?v=${{Date.now()}}`;
      video.load();
      document.getElementById('segmentsTitle').textContent = `${{ep.episode_id}} · ${{ep.n_segments}} segments`;
      list.innerHTML = '';
      ep.segments.forEach((seg, i) => {{
        const row = document.createElement('button');
        row.type = 'button';
        row.className = 'segment' + (i === 0 ? ' active' : '');
        row.innerHTML = `
          <div class="seg-top"><span class="time">${{fmt(seg.start)}} - ${{fmt(seg.end)}}</span><span class="badge">${{esc(seg.review_decision || 'segment')}}</span></div>
          <div class="pred">${{esc(seg.pred || '(empty prediction)')}}</div>
          <div class="gt">Ground truth: ${{esc(seg.gt || '(empty)')}}</div>
          <div class="conf-row">Conf: avg ${{fmtConf(seg.model_conf?.avg_conf)}} · min ${{fmtConf(seg.model_conf?.min_conf)}} · top3 ${{esc(seg.top3_summary || 'not captured')}}</div>
          <div class="notes">Notes: ${{esc(seg.review_notes || '(none)')}}</div>
          <div class="prev">Prev pred input: ${{esc(seg.previous_model_prediction_input || '(empty)')}}</div>
        `;
        row.addEventListener('click', () => seek(seg, row));
        list.appendChild(row);
      }});
      if (ep.segments[0]) setNow(ep.segments[0]);
    }}
    payload.episodes.forEach((ep, i) => {{
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'tab';
      b.innerHTML = `<strong>${{esc(ep.episode_id)}}</strong><span>${{ep.n_segments}} seg · ${{esc(ep.task_desc || ep.objects || '')}}</span>`;
      b.addEventListener('click', () => renderEpisode(i));
      tabs.appendChild(b);
    }});
    video.addEventListener('timeupdate', () => {{
      if (!stopAtEnd || !activeSegment) return;
      if (video.currentTime >= activeSegment.end) {{
        video.pause();
        video.currentTime = activeSegment.end;
        stopAtEnd = false;
      }}
    }});
    video.addEventListener('loadedmetadata', applyPendingSeek);
    video.addEventListener('canplay', applyPendingSeek);
    if (payload.episodes.length) renderEpisode(0);
  </script>
</body>
</html>
"""


def write_scores_csv(payload: dict[str, Any], path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for ep in payload.get("episodes", []):
        for seg in ep.get("segments", []):
            rows.append(
                {
                    "episode_id": ep.get("episode_id", ""),
                    "segment_index": seg.get("segment_index", ""),
                    "start": seg.get("start", ""),
                    "end": seg.get("end", ""),
                    "pred": seg.get("pred", ""),
                    "gt": seg.get("gt", ""),
                    "avg_conf": (seg.get("model_conf") or {}).get("avg_conf", ""),
                    "min_conf": (seg.get("model_conf") or {}).get("min_conf", ""),
                    "geo_mean_conf": (seg.get("model_conf") or {}).get("geo_mean_conf", ""),
                    "top3_summary": seg.get("top3_summary", ""),
                    "review_notes": seg.get("review_notes", ""),
                }
            )
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class RangeRequestHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        ctype = self.guess_type(path)
        try:
            f = open(path, "rb")
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None
        size = os.fstat(f.fileno()).st_size
        range_header = self.headers.get("Range")
        if not range_header:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", str(size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            return f
        match = re.match(r"bytes=(\d*)-(\d*)", range_header)
        if not match:
            self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            f.close()
            return None
        start_s, end_s = match.groups()
        if start_s:
            start = int(start_s)
            end = int(end_s) if end_s else size - 1
        else:
            suffix = int(end_s)
            start = max(size - suffix, 0)
            end = size - 1
        end = min(end, size - 1)
        if start >= size or end < start:
            self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            f.close()
            return None
        self.send_response(HTTPStatus.PARTIAL_CONTENT)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        f.seek(start)
        self.range = (start, end)
        return f

    def copyfile(self, source, outputfile):
        if hasattr(self, "range"):
            start, end = self.range
            remaining = end - start + 1
            while remaining > 0:
                chunk = source.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
            del self.range
        else:
            super().copyfile(source, outputfile)


def serve_only(directory: Path, host: str, port: int) -> None:
    os.chdir(directory)
    mimetypes.add_type("video/mp4", ".mp4")
    httpd = ThreadingHTTPServer((host, port), RangeRequestHandler)
    print(f"Serving {directory} at http://{host}:{port}/", flush=True)
    httpd.serve_forever()


def free_port(start: int) -> int:
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError(f"No free port found from {start} to {start + 99}")


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_") or "viewer"


def start_detached_server(script: Path, output_dir: Path, port: int) -> tuple[int, Path]:
    run_dir = Path("/tmp/codex_html_video_viewer") / slugify(output_dir.name)
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "http.log"
    pid_path = run_dir / "http.pid"
    cmd = [
        sys.executable,
        str(script),
        "serve-only",
        "--directory",
        str(output_dir),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    with log_path.open("ab") as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=log, stdin=subprocess.DEVNULL, start_new_session=True)
    pid_path.write_text(str(proc.pid), encoding="utf-8")
    time.sleep(0.5)
    return proc.pid, log_path


def start_tunnel(port: int, output_dir: Path) -> tuple[str, int, Path] | None:
    cloudflared = shutil.which("cloudflared")
    if not cloudflared:
        return None
    run_dir = Path("/tmp/codex_html_video_viewer") / slugify(output_dir.name)
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "cloudflared.log"
    pid_path = run_dir / "cloudflared.pid"
    cmd = [cloudflared, "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"]
    with log_path.open("wb") as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=log, stdin=subprocess.DEVNULL, start_new_session=True)
    pid_path.write_text(str(proc.pid), encoding="utf-8")
    deadline = time.time() + 20
    url = ""
    pattern = re.compile(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com")
    while time.time() < deadline:
        text = log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""
        match = pattern.search(text)
        if match:
            url = match.group(0)
            break
        if proc.poll() is not None:
            break
        time.sleep(0.5)
    if not url:
        return None
    return url, proc.pid, log_path


def first_video_url(payload: dict[str, Any]) -> str | None:
    for ep in payload.get("episodes", []):
        video = ep.get("full_video")
        if video:
            return str(video)
    return None


def command_build(args: argparse.Namespace) -> None:
    input_dir = args.input_dir.absolute()
    output_dir = args.output_dir.absolute()
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload(input_dir, output_dir, args.title, args.model_key)
    (output_dir / "viewer_data.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "index.html").write_text(render_html(payload), encoding="utf-8")
    write_scores_csv(payload, output_dir / "scores.csv")
    file_url = (output_dir / "index.html").resolve().as_uri()
    print(f"HTML_PATH={output_dir / 'index.html'}")
    print(f"HTML_FILE_URL={file_url}")
    if args.serve or args.tunnel:
        port = free_port(args.port)
        pid, log_path = start_detached_server(Path(__file__).resolve(), output_dir, port)
        local_url = f"http://127.0.0.1:{port}/index.html"
        print(f"LOCAL_HTTP_URL={local_url}")
        print(f"HTTP_SERVER_PID={pid}")
        print(f"HTTP_SERVER_LOG={log_path}")
        if args.tunnel:
            tunnel = start_tunnel(port, output_dir)
            if tunnel is None:
                print("TUNNEL_URL=")
                print("TUNNEL_ERROR=cloudflared missing or tunnel URL not found")
            else:
                base_url, tunnel_pid, tunnel_log = tunnel
                print(f"TUNNEL_URL={base_url}/index.html")
                print(f"TUNNEL_BASE_URL={base_url}")
                print(f"TUNNEL_PID={tunnel_pid}")
                print(f"TUNNEL_LOG={tunnel_log}")
                video = first_video_url(payload)
                if video:
                    print(f"TUNNEL_FIRST_VIDEO_URL={base_url}/{video.lstrip('/')}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    serve_parser = sub.add_parser("serve-only")
    serve_parser.add_argument("--directory", type=Path, required=True)
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, required=True)

    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--title", default="Video Result Viewer")
    parser.add_argument("--model-key", default=None)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--tunnel", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.cmd == "serve-only":
        serve_only(args.directory.absolute(), args.host, args.port)
        return
    if args.input_dir is None or args.output_dir is None:
        parser.error("--input-dir and --output-dir are required")
    command_build(args)


if __name__ == "__main__":
    main()
