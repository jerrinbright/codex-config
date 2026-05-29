#!/usr/bin/env python3
"""Audit action-label datasets for training-quality problems.

The script is intentionally dependency-free. It accepts common redelivery shapes:
episode-level JSON with nested preannotations, flat segment rows, or a dict wrapping
one of those lists.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import quantiles
from typing import Any


BOUNDARY_WORDS = [
    "and",
    "or",
    "but",
    "with",
    "from",
    "to",
    "on",
    "in",
    "into",
    "onto",
    "at",
    "by",
    "for",
    "of",
    "over",
    "under",
    "using",
    "while",
    "then",
    "the",
    "a",
    "an",
]

ACTION_VERBS = [
    "pick up",
    "put down",
    "turn on",
    "turn off",
    "place",
    "put",
    "move",
    "adjust",
    "hold",
    "grab",
    "grasp",
    "lift",
    "push",
    "pull",
    "rotate",
    "turn",
    "wipe",
    "clean",
    "scrub",
    "rinse",
    "cut",
    "slice",
    "pour",
    "scoop",
    "insert",
    "remove",
    "open",
    "close",
    "fold",
    "align",
    "reposition",
    "nudge",
    "press",
    "flatten",
    "smooth",
    "smoothen",
    "spread",
    "dip",
    "tie",
    "wrap",
    "seal",
    "attach",
    "detach",
    "brush",
    "sand",
    "iron",
    "spray",
    "stir",
    "mix",
    "sort",
    "stack",
    "fill",
    "empty",
    "drop",
    "cover",
    "apply",
    "squeeze",
    "flip",
    "trim",
    "peel",
    "level",
    "twist",
    "shake",
    "tap",
    "roll",
    "shape",
    "assemble",
    "disassemble",
    "separate",
    "organize",
    "pack",
    "unpack",
    "hang",
    "scrape",
    "sharpen",
    "wash",
    "dry",
    "polish",
    "file",
    "hammer",
    "screw",
    "unscrew",
    "tighten",
    "loosen",
    "measure",
    "mark",
    "draw",
    "write",
    "paint",
    "glue",
    "tape",
    "clip",
    "zip",
    "unzip",
    "button",
    "unbutton",
    "plug",
    "unplug",
]

VAGUE_VERBS = ["adjust", "reposition", "nudge", "move", "handle", "touch", "hold"]

TYPOISH_PATTERNS = [
    "sawsaw",
    "sliver",
    "envelop",
    "bowel",
    "scrapper",
    "place red place",
    "place bow o stove",
    "with with",
    "over turn",
]


@dataclass
class Segment:
    row_id: str
    episode_id: str
    index: int
    label: str
    start: Any = None
    end: Any = None


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def choose_rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        raise TypeError(f"Expected list or dict JSON root, got {type(data).__name__}")

    candidates: list[tuple[str, list[Any]]] = []
    for key, value in data.items():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            candidates.append((key, value))
    if not candidates:
        raise ValueError("Could not find a list of dict rows in JSON")
    candidates.sort(key=lambda item: len(item[1]), reverse=True)
    return candidates[0][1]


def first_present(row: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in row:
            return row[key]
    return None


def flatten_segments(rows: list[dict[str, Any]]) -> list[Segment]:
    segments: list[Segment] = []
    for row_index, row in enumerate(rows):
        episode_id = str(first_present(row, ["episode_id", "episodeId", "id"]) or row_index)
        preannotations = row.get("preannotations")
        if isinstance(preannotations, list):
            for ann_index, ann in enumerate(preannotations):
                if not isinstance(ann, dict):
                    continue
                label = str(first_present(ann, ["label", "vlmLabel", "target", "gt", "action"]) or "").strip()
                start = first_present(ann, ["event_annotation_start_time", "start_seconds", "startSeconds", "start"])
                end = first_present(ann, ["event_annotation_end_time", "end_seconds", "endSeconds", "end"])
                segments.append(Segment(f"{episode_id}::{ann_index}", episode_id, ann_index, label, start, end))
            continue

        label = str(first_present(row, ["label", "vlmLabel", "target", "gt", "action"]) or "").strip()
        start = first_present(row, ["event_annotation_start_time", "start_seconds", "startSeconds", "start"])
        end = first_present(row, ["event_annotation_end_time", "end_seconds", "endSeconds", "end"])
        index = int(first_present(row, ["segment_index", "index", "idx"]) or 0)
        segments.append(Segment(f"{episode_id}::{index}", episode_id, index, label, start, end))
    return segments


class LabelAuditor:
    def __init__(self, segments: list[Segment]) -> None:
        self.segments = segments
        boundary_alt = "|".join(re.escape(word) for word in BOUNDARY_WORDS)
        verbs = sorted(set(ACTION_VERBS), key=len, reverse=True)
        verb_alt = "|".join(re.escape(verb) for verb in verbs)
        vague_alt = "|".join(re.escape(verb) for verb in VAGUE_VERBS)
        typo_alt = "|".join(re.escape(term) for term in TYPOISH_PATTERNS)

        self.start_boundary_re = re.compile(rf"^\s*(?:,\s*)?({boundary_alt})\b", re.IGNORECASE)
        self.end_boundary_re = re.compile(rf"\b({boundary_alt})\s*(?:,\s*)?$", re.IGNORECASE)
        self.leading_comma_re = re.compile(r"^\s*,")
        self.first_word_comma_re = re.compile(r"^[a-z]+,\s+", re.IGNORECASE)
        self.comma_before_prep_re = re.compile(r",\s+(with|from|on|to|in|into|onto|under|over)\b", re.IGNORECASE)
        self.and_action_re = re.compile(rf"\band\s+({verb_alt})\b", re.IGNORECASE)
        self.start_action_re = re.compile(rf"^(?:{verb_alt})\b", re.IGNORECASE)
        self.action_re = re.compile(rf"\b(?:{verb_alt})\b", re.IGNORECASE)
        self.vague_re = re.compile(rf"\b(?:{vague_alt})\b", re.IGNORECASE)
        self.typoish_re = re.compile(rf"\b(?:{typo_alt})\b", re.IGNORECASE)
        self.and_split_re = re.compile(rf"\s+and\s+(?=(?:{verb_alt})\b)", re.IGNORECASE)

    def action_clauses(self, label: str) -> list[str]:
        clauses: list[str] = []
        for comma_chunk in label.split(","):
            for chunk in self.and_split_re.split(comma_chunk):
                text = chunk.strip().lower()
                if self.start_action_re.search(text):
                    clauses.append(text)
        return clauses

    def issue_flags(self, label: str) -> list[str]:
        flags: list[str] = []
        if not label:
            return ["empty_label"]
        if self.leading_comma_re.search(label):
            flags.append("leading_comma")
        if self.start_boundary_re.search(label):
            flags.append("starts_with_boundary_word")
        if self.end_boundary_re.search(label):
            flags.append("ends_with_boundary_word")
        if self.first_word_comma_re.search(label):
            flags.append("first_word_comma")
        if self.comma_before_prep_re.search(label):
            flags.append("comma_before_preposition")
        and_hits = self.and_action_re.findall(label)
        if and_hits:
            flags.append("and_action_separator")
            if len(and_hits) > 1:
                flags.append("multiple_and_action_separators")
        clauses = self.action_clauses(label)
        if len(clauses) > 4:
            flags.append("more_than_4_action_clauses")
        elif len(clauses) == 4:
            flags.append("four_action_clauses")
        if self.vague_re.search(label):
            flags.append("vague_or_adjust_like")
        if self.typoish_re.search(label):
            flags.append("typoish_token")
        if re.search(r"([^,]{8,}),\s*\1\b", label, re.IGNORECASE):
            flags.append("repeated_clause")
        return flags

    def summarize(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        issue_rows: list[dict[str, Any]] = []
        flag_counts: Counter[str] = Counter()
        end_words: Counter[str] = Counter()
        start_words: Counter[str] = Counter()
        and_verbs: Counter[str] = Counter()
        action_clause_counts: Counter[int] = Counter()
        label_counts: Counter[str] = Counter()
        episode_labels: dict[str, list[str]] = defaultdict(list)

        for segment in self.segments:
            label_counts[segment.label] += 1
            episode_labels[segment.episode_id].append(segment.label)
            flags = self.issue_flags(segment.label)
            clauses = self.action_clauses(segment.label)
            action_clause_counts[len(clauses)] += 1

            start_match = self.start_boundary_re.search(segment.label)
            if start_match:
                start_words[start_match.group(1).lower()] += 1
            end_match = self.end_boundary_re.search(segment.label)
            if end_match:
                end_words[end_match.group(1).lower()] += 1
            for verb in self.and_action_re.findall(segment.label):
                and_verbs[verb.lower()] += 1

            if flags:
                for flag in flags:
                    flag_counts[flag] += 1
                issue_rows.append(
                    {
                        "row_id": segment.row_id,
                        "episode_id": segment.episode_id,
                        "segment_index": segment.index,
                        "start": segment.start,
                        "end": segment.end,
                        "flags": "|".join(flags),
                        "action_clause_count": len(clauses),
                        "label": segment.label,
                    }
                )

        adjacent_same = 0
        adjacent_total = 0
        all_same_episodes = 0
        repeat_rates: list[float] = []
        top_all_same: list[dict[str, Any]] = []
        for episode_id, labels in episode_labels.items():
            if len(labels) > 1:
                same = sum(1 for left, right in zip(labels, labels[1:]) if left == right)
                adjacent_same += same
                adjacent_total += len(labels) - 1
                repeat_rates.append(same / (len(labels) - 1))
            if labels and len(labels) >= 10 and len(set(labels)) == 1:
                all_same_episodes += 1
                top_all_same.append({"episode_id": episode_id, "segments": len(labels), "label": labels[0]})

        top_all_same.sort(key=lambda item: item["segments"], reverse=True)
        repeat_quantiles = {}
        if repeat_rates:
            qs = quantiles(repeat_rates, n=100)
            repeat_quantiles = {f"p{q}": qs[q - 1] for q in [50, 75, 90, 95, 99]}

        total = len(self.segments)
        nonempty = sum(1 for segment in self.segments if segment.label)
        summary = {
            "total_segments": total,
            "total_episodes": len(episode_labels),
            "empty_labels": total - nonempty,
            "unique_labels": len(label_counts),
            "duplicate_label_ratio": 1 - (len(label_counts) / nonempty) if nonempty else 0,
            "flag_counts": dict(flag_counts),
            "start_boundary_words": dict(start_words.most_common()),
            "end_boundary_words": dict(end_words.most_common()),
            "and_action_verbs": dict(and_verbs.most_common(50)),
            "action_clause_distribution": {str(k): v for k, v in sorted(action_clause_counts.items())},
            "adjacent_same_labels": adjacent_same,
            "adjacent_pairs": adjacent_total,
            "adjacent_same_ratio": adjacent_same / adjacent_total if adjacent_total else 0,
            "episode_adjacent_repeat_quantiles": repeat_quantiles,
            "all_same_episodes_len_ge_10": all_same_episodes,
            "top_all_same_episodes": top_all_same[:25],
            "top_duplicate_labels": [
                {"label": label, "count": count}
                for label, count in label_counts.most_common(50)
                if label
            ],
        }
        return summary, issue_rows


def pct(count: int | float, total: int | float) -> str:
    return f"{(count / total * 100):.4f}%" if total else "0.0000%"


def example_rows(issue_rows: list[dict[str, Any]], flag: str, limit: int) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for row in issue_rows:
        flags = set(str(row["flags"]).split("|"))
        label = str(row["label"])
        if flag in flags and label not in seen:
            seen.add(label)
            out.append(row)
            if len(out) >= limit:
                break
    return out


def write_report(path: Path, summary: dict[str, Any], issue_rows: list[dict[str, Any]], example_limit: int) -> None:
    total = summary["total_segments"]
    flags = summary["flag_counts"]
    lines = [
        "# Label Quality Audit",
        "",
        f"- Segments: {total:,}",
        f"- Episodes: {summary['total_episodes']:,}",
        f"- Empty labels: {summary['empty_labels']:,} ({pct(summary['empty_labels'], total)})",
        f"- Unique labels: {summary['unique_labels']:,}",
        f"- Duplicate label ratio: {summary['duplicate_label_ratio'] * 100:.2f}%",
        f"- Adjacent same labels: {summary['adjacent_same_labels']:,} / {summary['adjacent_pairs']:,} ({pct(summary['adjacent_same_labels'], summary['adjacent_pairs'])})",
        f"- All-same episodes with >=10 segments: {summary['all_same_episodes_len_ge_10']:,}",
        "",
        "## Issue Counts",
        "",
        "| Issue | Count | Percent |",
        "|---|---:|---:|",
    ]
    for flag, count in sorted(flags.items(), key=lambda item: item[1], reverse=True):
        lines.append(f"| `{flag}` | {count:,} | {pct(count, total)} |")

    lines.extend(["", "## Boundary Words", "", "### Starts With Boundary Word", ""])
    for word, count in summary["start_boundary_words"].items():
        lines.append(f"- `{word}`: {count:,}")
    lines.extend(["", "### Ends With Boundary Word", ""])
    for word, count in summary["end_boundary_words"].items():
        lines.append(f"- `{word}`: {count:,}")

    lines.extend(["", "## Top `and <action>` Verbs", ""])
    for verb, count in list(summary["and_action_verbs"].items())[:25]:
        lines.append(f"- `{verb}`: {count:,}")

    lines.extend(["", "## Examples", ""])
    for flag in [
        "leading_comma",
        "starts_with_boundary_word",
        "ends_with_boundary_word",
        "comma_before_preposition",
        "first_word_comma",
        "and_action_separator",
        "more_than_4_action_clauses",
        "vague_or_adjust_like",
        "typoish_token",
        "repeated_clause",
    ]:
        rows = example_rows(issue_rows, flag, example_limit)
        if not rows:
            continue
        lines.extend([f"### `{flag}`", ""])
        for row in rows:
            lines.append(f"- `{row['label']}` ({row['episode_id']}:{row['segment_index']})")
        lines.append("")

    lines.extend(["## Top All-Same Episodes", ""])
    for item in summary["top_all_same_episodes"][:10]:
        lines.append(f"- {item['segments']} segments: `{item['label']}` ({item['episode_id']})")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_issue_csv(path: Path, issue_rows: list[dict[str, Any]]) -> None:
    fieldnames = ["row_id", "episode_id", "segment_index", "start", "end", "flags", "action_clause_count", "label"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(issue_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Input JSON dataset.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for report.md, summary.json, and issue_rows.csv.")
    parser.add_argument("--example-limit", type=int, default=20, help="Examples per issue type in report.md.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = load_json(args.input)
    rows = choose_rows(data)
    segments = flatten_segments(rows)
    if not segments:
        raise ValueError("No segment labels found")

    auditor = LabelAuditor(segments)
    summary, issue_rows = auditor.summarize()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_issue_csv(args.output_dir / "issue_rows.csv", issue_rows)
    write_report(args.output_dir / "report.md", summary, issue_rows, args.example_limit)

    total = summary["total_segments"]
    flags = summary["flag_counts"]
    print(f"segments={total:,} episodes={summary['total_episodes']:,}")
    for flag in [
        "starts_with_boundary_word",
        "ends_with_boundary_word",
        "leading_comma",
        "comma_before_preposition",
        "and_action_separator",
        "more_than_4_action_clauses",
        "vague_or_adjust_like",
    ]:
        count = flags.get(flag, 0)
        print(f"{flag}={count:,} ({pct(count, total)})")
    print(f"report={args.output_dir / 'report.md'}")
    print(f"issues={args.output_dir / 'issue_rows.csv'}")
    print(f"summary={args.output_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
