#!/usr/bin/env python3
"""Split stereo-hands combined recordings into corrected camera MP4 files."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


PRIMARY_CROPS = (
    ("recording_left_cam.mp4", "recording_primary.mp4", 1920, 1200, 160, 0),
    ("recording_right_cam.mp4", "recording_primary.mp4", 1920, 1200, 2080, 0),
)

SECONDARY_CROPS = (
    ("recording_secondary_cam_2.mp4", "recording_secondary.mp4", 640, 480, 544, 0),
    ("recording_secondary_cam_3.mp4", "recording_secondary.mp4", 640, 480, 1184, 0),
    ("recording_secondary_cam_4.mp4", "recording_secondary.mp4", 640, 480, 1824, 0),
    ("recording_secondary_cam_5.mp4", "recording_secondary.mp4", 640, 480, 2464, 0),
)


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required tool not found on PATH: {name}")


def probe_video(path: Path) -> dict[str, int | float | str | None]:
    result = run([
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,nb_frames,r_frame_rate,duration",
        "-of",
        "json",
        str(path),
    ])
    data = json.loads(result.stdout)
    streams = data.get("streams") or []
    if not streams:
        raise RuntimeError(f"No video stream found: {path}")
    stream = streams[0]
    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "nb_frames": stream.get("nb_frames"),
        "r_frame_rate": stream.get("r_frame_rate"),
        "duration": stream.get("duration"),
    }


def validate_source_dimensions(episode_dir: Path) -> None:
    expected = {
        "recording_primary.mp4": (4000, 1200),
        "recording_secondary.mp4": (3104, 480),
    }
    for filename, (want_w, want_h) in expected.items():
        path = episode_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing required input: {path}")
        info = probe_video(path)
        got = (info["width"], info["height"])
        if got != (want_w, want_h):
            raise RuntimeError(
                f"{filename} has dimensions {got[0]}x{got[1]}, expected {want_w}x{want_h}. "
                "Refusing to apply fixed stereo-hands crop offsets.",
            )


def split_one(
    episode_dir: Path,
    output_name: str,
    source_name: str,
    width: int,
    height: int,
    x: int,
    y: int,
    *,
    overwrite: bool,
    dry_run: bool,
) -> None:
    source = episode_dir / source_name
    output = episode_dir / output_name
    tmp = episode_dir / f".{output_name}.tmp.mp4"

    if output.exists() and not overwrite and not dry_run:
        raise FileExistsError(f"Output exists; pass --overwrite to replace it: {output}")

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if overwrite else "-n",
        "-i",
        str(source),
        "-vf",
        f"crop={width}:{height}:{x}:{y}",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        str(tmp),
    ]
    print(f"{output_name}: {source_name} crop={width}:{height}:{x}:{y}")
    if dry_run:
        print("  dry-run:", " ".join(cmd))
        return

    if tmp.exists():
        tmp.unlink()
    run(cmd)
    info = probe_video(tmp)
    if (info["width"], info["height"]) != (width, height):
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"{tmp} validated as {info['width']}x{info['height']}, expected {width}x{height}")
    tmp.replace(output)
    print(
        f"  wrote {output} ({info['width']}x{info['height']}, "
        f"frames={info['nb_frames']}, fps={info['r_frame_rate']})",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split recording_primary.mp4 and recording_secondary.mp4 into corrected stereo-hands camera files.",
    )
    parser.add_argument("episode_dir", type=Path, help="Directory containing recording_primary.mp4 and recording_secondary.mp4")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing split camera files")
    parser.add_argument("--dry-run", action="store_true", help="Print ffmpeg commands without writing outputs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    episode_dir = args.episode_dir.expanduser().resolve()
    if not episode_dir.is_dir():
        print(f"ERROR: not a directory: {episode_dir}", file=sys.stderr)
        return 2

    try:
        require_tool("ffmpeg")
        require_tool("ffprobe")
        validate_source_dimensions(episode_dir)
        for crop in (*PRIMARY_CROPS, *SECONDARY_CROPS):
            split_one(episode_dir, *crop, overwrite=args.overwrite, dry_run=args.dry_run)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if not args.dry_run:
        print("Done. Corrected six-camera split files are ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
