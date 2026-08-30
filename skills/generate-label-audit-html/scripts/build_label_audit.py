#!/usr/bin/env python3
"""Build a portable, optionally blinded segment-label audit viewer."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def required_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} must be nonempty")
    return text


def finite_number(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def normalize_segment(raw: dict[str, Any], row_number: int) -> dict[str, Any]:
    try:
        index = int(raw["index"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"rows[{row_number}].segments[].index must be an integer") from exc
    start = finite_number(raw.get("start"), f"rows[{row_number}].segments[{index}].start")
    end = finite_number(raw.get("end"), f"rows[{row_number}].segments[{index}].end")
    if start < 0 or end <= start:
        raise ValueError(f"rows[{row_number}].segments[{index}] has invalid range {start}..{end}")
    confidence = raw.get("confidence")
    if confidence is not None:
        confidence = finite_number(confidence, f"rows[{row_number}].segments[{index}].confidence")
    return {
        "i": index,
        "start": start,
        "end": end,
        "label": required_text(raw.get("label"), f"rows[{row_number}].segments[{index}].label"),
        "conf": confidence,
    }


def make_audit_id(seed: int, source_id: str, variant: str, ordinal: int) -> str:
    digest = hashlib.sha256(f"{seed}:{source_id}:{variant}:{ordinal}".encode()).hexdigest()[:16]
    return f"run-{digest}"


def normalize_rows(
    rows: list[dict[str, Any]], *, blind: bool, shuffle: bool, seed: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not rows:
        raise ValueError("rows must be a nonempty list")
    output: list[dict[str, Any]] = []
    decoder: list[dict[str, Any]] = []
    seen_audit_ids: set[str] = set()

    for ordinal, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise ValueError(f"rows[{ordinal}] must be an object")
        source_id = required_text(raw.get("source_episode_id"), f"rows[{ordinal}].source_episode_id")
        variant = str(raw.get("variant") or "candidate").strip()
        video_url = required_text(raw.get("video_url"), f"rows[{ordinal}].video_url")
        raw_segments = raw.get("segments")
        if not isinstance(raw_segments, list) or not raw_segments:
            raise ValueError(f"rows[{ordinal}].segments must be a nonempty list")
        segments = [normalize_segment(segment, ordinal) for segment in raw_segments]
        indices = [segment["i"] for segment in segments]
        if len(indices) != len(set(indices)):
            raise ValueError(f"rows[{ordinal}] has duplicate segment indices")
        segments.sort(key=lambda segment: (segment["start"], segment["i"]))

        explicit_id = str(raw.get("audit_id") or "").strip()
        audit_id = make_audit_id(seed, source_id, variant, ordinal) if blind else (explicit_id or source_id)
        if audit_id in seen_audit_ids:
            raise ValueError(f"Duplicate audit ID {audit_id!r}; provide unique audit_id values or use --blind")
        seen_audit_ids.add(audit_id)

        duration = raw.get("duration")
        duration = max(segment["end"] for segment in segments) if duration is None else finite_number(duration, f"rows[{ordinal}].duration")
        if duration < max(segment["end"] for segment in segments):
            raise ValueError(f"rows[{ordinal}].duration ends before its final segment")

        output.append(
            {
                "episodeId": audit_id,
                "sourceEpisodeId": source_id,
                "userTaskId": raw.get("user_task_id"),
                "taskId": raw.get("task_id"),
                "description": raw.get("description"),
                "videoUrl": video_url,
                "videoUri": raw.get("video_uri"),
                "duration": duration,
                "segments": segments,
            }
        )
        decoder.append(
            {
                "audit_run_id": audit_id,
                "source_episode_id": source_id,
                "variant": variant,
                "segments": len(segments),
                "private_metadata": raw.get("private_metadata") or {},
            }
        )

    if shuffle:
        random.Random(seed).shuffle(output)
    return output, decoder


def verify_output(html_path: Path, expected_runs: int, expected_segments: int) -> None:
    html = html_path.read_text()
    required = (
        "rejection_reason",
        'class="reason-grid',
        'type="checkbox"',
        "missing action",
        "wrong action",
        "wrong object",
        "wrong hand",
        "added action",
        "wrong order",
        "plural",
        "unclear video",
        "other",
        "rejections needing reason",
    )
    missing = [token for token in required if token not in html]
    if missing:
        raise RuntimeError(f"Generated HTML is missing required audit controls: {missing}")
    if '<select class="reason-in' in html:
        raise RuntimeError("Generated HTML still uses the legacy single-reason dropdown")
    if f'"size":{expected_runs}' not in html or f'"totalSegments":{expected_segments}' not in html:
        raise RuntimeError("Generated HTML count verification failed")

    try:
        node = subprocess.run(
            ["node", "--check", "-"],
            input=html.split("<script>", 1)[1].rsplit("</script>", 1)[0],
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        node = None
    if node is not None and node.returncode:
        raise RuntimeError(f"Generated JavaScript failed syntax validation: {node.stderr.strip()}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--decoder-output", type=Path)
    parser.add_argument("--title")
    parser.add_argument("--seed", type=int, default=20260812)
    parser.add_argument("--blind", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--shuffle", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--verify", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    manifest = json.loads(args.input.read_text())
    if not isinstance(manifest, dict) or not isinstance(manifest.get("rows"), list):
        raise ValueError("Input must be a JSON object containing a rows array")
    rows, decoder = normalize_rows(
        manifest["rows"], blind=args.blind, shuffle=args.shuffle, seed=args.seed
    )
    segment_count = sum(len(row["segments"]) for row in rows)
    source_count = len({row["sourceEpisodeId"] for row in rows})
    payload = {
        "title": args.title or manifest.get("title") or "Label audit",
        "client": manifest.get("client") or "human-review",
        "deliveryDate": manifest.get("delivery_date") or datetime.now(timezone.utc).date().isoformat(),
        "size": len(rows),
        "poolSize": source_count,
        "totalSegments": segment_count,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "rows": rows,
        "provenance": manifest.get("provenance") or [],
    }

    skill_root = Path(__file__).resolve().parents[1]
    template_path = skill_root / "assets" / "audit_viewer.html"
    template = template_path.read_text()
    if template.count("__PAYLOAD__") != 1:
        raise RuntimeError("Audit template must contain exactly one __PAYLOAD__ marker")
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).replace("</", "<\\/")
    html = template.replace("__PAYLOAD__", encoded)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html)
    decoder_path = args.decoder_output or args.output.with_suffix(".private_decoder.json")
    decoder_path.parent.mkdir(parents=True, exist_ok=True)
    decoder_payload = {
        "blinded": args.blind,
        "seed": args.seed,
        "source_manifest": str(args.input.resolve()),
        "rows": decoder,
    }
    decoder_path.write_text(json.dumps(decoder_payload, indent=2, sort_keys=True) + "\n")

    if args.verify:
        verify_output(args.output, len(rows), segment_count)
    print(
        json.dumps(
            {
                "status": "pass",
                "blinded": args.blind,
                "source_episodes": source_count,
                "audit_runs": len(rows),
                "segments": segment_count,
                "html": str(args.output),
                "html_sha256": sha256(args.output),
                "private_decoder": str(decoder_path),
                "private_decoder_sha256": sha256(decoder_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
