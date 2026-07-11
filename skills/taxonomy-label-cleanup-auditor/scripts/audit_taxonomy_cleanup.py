#!/usr/bin/env python3
"""Audit action-label taxonomy cleanup candidates.

This script is intentionally conservative: it reports counts, examples, and
candidate fixes, but it does not rewrite labels. Use the generated artifacts to
approve surgical cleanup rules before changing training data.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


LABEL_KEYS = (
    "label",
    "action",
    "caption",
    "text",
    "full_label",
    "annotation",
    "description",
)


TYPO_PATTERNS = [
    {
        "name": "assay_to_assess",
        "regex": r"\bassay(?:ing|s|ed)?\b",
        "suggestion": "assess",
        "risk": "low",
        "note": "Inspection/action labels often use assay as a typo for assess.",
    },
    {
        "name": "pick_up_phrase_typos",
        "regex": r"\b(?:pic|pock|puck)\s+up\b",
        "suggestion": "pick up",
        "risk": "low",
        "note": "Phrase-specific only. Do not rewrite pink.",
    },
    {
        "name": "peal_to_peel",
        "regex": r"\bpeal(?:ing|s|ed)?\b",
        "suggestion": "peel",
        "risk": "low",
        "note": "Usually a peel typo in manipulation labels.",
    },
    {
        "name": "tun_to_turn",
        "regex": r"\btun(?:ing|s|ed)?\b",
        "suggestion": "turn",
        "risk": "low",
        "note": "Likely misspelling of turn.",
    },
    {
        "name": "turnoff_to_turn_off",
        "regex": r"\bturnoff\b",
        "suggestion": "turn off",
        "risk": "low",
        "note": "Glued verb particle.",
    },
    {
        "name": "arrangescrews_to_arrange_screws",
        "regex": r"\barrangescrews\b",
        "suggestion": "arrange screws",
        "risk": "low",
        "note": "Glued verb and noun.",
    },
    {
        "name": "deep_clause_start_to_dip",
        "regex": r"(^|[.;,]\s*)deep\s+",
        "suggestion": "dip",
        "risk": "medium",
        "note": "Only plausible at clause start in cooking/tool-use actions.",
    },
    {
        "name": "flat_clause_start_to_flatten",
        "regex": r"(^|[.;,]\s*)flat\s+",
        "suggestion": "flatten",
        "risk": "medium",
        "note": "Only plausible at clause start.",
    },
    {
        "name": "folk_to_fork",
        "regex": r"\bfolk(s)?\b",
        "suggestion": "fork/forks",
        "risk": "medium",
        "note": "Only in utensil contexts.",
    },
    {
        "name": "hummer_to_hammer",
        "regex": r"\bhummer(s|ing|ed)?\b",
        "suggestion": "hammer",
        "risk": "medium",
        "note": "Likely tool/action typo.",
    },
    {
        "name": "soon_to_spoon",
        "regex": r"\bsoon(s)?\b",
        "suggestion": "spoon/spoons",
        "risk": "medium",
        "note": "Only in utensil/object contexts.",
    },
    {
        "name": "facet_to_faucet",
        "regex": r"\bfacet(s)?\b",
        "suggestion": "faucet/faucets",
        "risk": "medium",
        "note": "Likely sink/water object typo.",
    },
    {
        "name": "scrape_typos",
        "regex": r"\b(?:crape|scape)(s|d|ing)?\b",
        "suggestion": "scrape",
        "risk": "medium",
        "note": "Likely scrape misspelling.",
    },
    {
        "name": "spray_typo",
        "regex": r"\bpray(s|ed|ing)?\b",
        "suggestion": "spray",
        "risk": "medium",
        "note": "Only in cleaning/liquid contexts.",
    },
    {
        "name": "attach_typos",
        "regex": r"\b(?:attache|attack)(s|ed|ing)?\b",
        "suggestion": "attach",
        "risk": "medium",
        "note": "Only in attachment/fastening contexts.",
    },
    {
        "name": "potion_to_portion",
        "regex": r"\bpotion(s)?\b",
        "suggestion": "portion",
        "risk": "medium",
        "note": "Likely portion in food contexts.",
    },
    {
        "name": "inert_to_insert",
        "regex": r"\binert(s|ed|ing)?\b",
        "suggestion": "insert",
        "risk": "medium",
        "note": "Likely insert typo.",
    },
    {
        "name": "fe_dough_to_feed_dough",
        "regex": r"\bfe\s+dough\b",
        "suggestion": "feed dough",
        "risk": "medium",
        "note": "Specific phrase typo.",
    },
    {
        "name": "gasp_to_grasp",
        "regex": r"\bgasp(s|ed|ing)?\b",
        "suggestion": "grasp",
        "risk": "medium",
        "note": "Likely grasp typo.",
    },
    {
        "name": "sweet_to_sweep_contextual",
        "regex": r"\bsweet\s+(?:floor|debris|dust|crumbs?|surface|table)\b",
        "suggestion": "sweep",
        "risk": "medium",
        "note": "Contextual only. Never rewrite sweet potato/sweets.",
    },
    {
        "name": "stair_to_stir_contextual",
        "regex": r"\bstair\s+(?:powder|mixture|batter|sauce|liquid|contents?)\b",
        "suggestion": "stir",
        "risk": "medium",
        "note": "Contextual only. Never rewrite actual stairs.",
    },
    {
        "name": "shirt_clause_start",
        "regex": r"(^|[.;,]\s*)shirt\s+",
        "suggestion": "review/remove",
        "risk": "high",
        "note": "Clause-start shirt was previously unsafe to correct automatically.",
    },
    {
        "name": "shit_contextual_review",
        "regex": r"\bshit\b|\bt-shit\b",
        "suggestion": "review: sheet/shift/t-shirt",
        "risk": "high",
        "note": "Needs context. Do not globally rewrite.",
    },
    {
        "name": "pill_contextual_review",
        "regex": r"\bpill\b",
        "suggestion": "review: peel/pull/pile/pill",
        "risk": "high",
        "note": "Needs context. Do not globally rewrite.",
    },
]


DANGEROUS_GLOBAL_TOKENS = {
    "pink": "Often a real color descriptor. Do not rewrite to pick globally.",
    "sweet": "Often a real food/object descriptor. Only sweep in cleaning contexts.",
    "stair": "Often a real location/object. Only stir in mixture contexts.",
    "shirt": "Often a real object. Clause-start cases need review.",
    "hole": "Often a real object. Do not rewrite to hold globally.",
    "pill": "Can be a real noun or typo. Needs phrase context.",
    "form": "Can be a real noun/verb. Do not rewrite to from globally.",
    "shit": "Can indicate several typos. Needs phrase context.",
}


COMMON_OBJECT_HEADS = (
    "cloth",
    "paper",
    "fabric",
    "glass",
    "plastic",
    "knife",
    "plate",
    "fork",
    "bowl",
    "cup",
    "lid",
    "container",
    "table",
    "dough",
    "screw",
    "screws",
    "faucet",
)


OBJECT_FRAGMENT_TOKENS = {
    "knife",
    "plastic",
    "plate",
    "fork",
    "cloth",
    "leaf",
    "fabric",
    "forks",
    "paper",
    "pot",
    "dough",
    "knives",
    "cottons",
    "debris",
    "table",
    "bottle",
    "assembly",
    "cup",
    "glass",
    "pliers",
    "lid",
    "container",
}


LIKELY_VERB_REVIEW_TOKENS = {
    "accommodate",
    "budge",
    "cuff",
    "uncuff",
    "slip",
    "seat",
    "match",
    "torch",
    "needle",
    "scan",
    "browse",
    "enlarge",
    "hover",
    "isolate",
    "stomp",
    "bang",
    "detail",
    "receive",
    "strap",
    "unstick",
    "dislocate",
    "net",
    "mask",
    "blot",
    "slash",
    "butter",
    "dress",
    "eject",
    "butcher",
    "choose",
    "give",
    "unhang",
    "harrow",
    "pivot",
    "reflow",
    "service",
    "space",
    "tunnel",
    "append",
    "band",
    "enclose",
    "retain",
    "twine",
    "direct",
    "style",
    "caress",
    "couple",
    "crunch",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
            if isinstance(obj, dict):
                yield obj


def stringify_label(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = [stringify_label(v) for v in value]
        parts = [p for p in parts if p]
        return ", ".join(parts) if parts else None
    if isinstance(value, dict):
        for key in LABEL_KEYS:
            text = stringify_label(value.get(key))
            if text:
                return text
    return None


def extract_labels_from_obj(obj: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def walk(value: Any, context: dict[str, Any], key: str | None = None) -> None:
        if isinstance(value, dict):
            next_context = dict(context)
            for context_key in (
                "episode_id",
                "episode",
                "id",
                "segment_index",
                "start",
                "end",
                "event_annotation_start_time",
                "event_annotation_end_time",
            ):
                if context_key in value and context_key not in next_context:
                    next_context[context_key] = value[context_key]
            label = stringify_label(value)
            if label:
                row = dict(next_context)
                row["label"] = label
                rows.append(row)
                return
            for child_key, child in value.items():
                walk(child, next_context, child_key)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                child_context = dict(context)
                child_context.setdefault("list_index", index)
                walk(child, child_context, key)
        elif isinstance(value, str):
            if key not in LABEL_KEYS and key is not None:
                return
            text = value.strip()
            if text and len(text.split()) <= 40:
                row = dict(context)
                row["label"] = text
                rows.append(row)

    walk(obj, {})
    return rows


def read_labels(path: Path | None) -> list[dict[str, Any]]:
    if not path:
        return []
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        rows = []
        for obj in iter_jsonl(path):
            label = stringify_label(obj)
            if label:
                row = dict(obj)
                row["label"] = label
                rows.append(row)
        return rows
    if suffix == ".json":
        return extract_labels_from_obj(load_json(path))
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = []
            for row in reader:
                label = stringify_label(row)
                if label:
                    row["label"] = label
                    rows.append(row)
            return rows
    raise ValueError(f"Unsupported labels file type: {path}")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def read_vocab_csv(path: Path) -> Counter:
    counter: Counter[str] = Counter()
    if not path.exists():
        return counter
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            token = (row.get("token") or row.get("verb") or row.get("noun") or row.get("word") or "").strip()
            if not token:
                continue
            count_text = row.get("count") or row.get("segments") or row.get("frequency") or "1"
            try:
                count = int(float(count_text))
            except ValueError:
                count = 1
            counter[token] += count
    return counter


def first_words(text: str, n: int = 12) -> str:
    return " ".join(text.split()[:n])


def collect_pattern_matches(labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compiled = [
        (spec, re.compile(spec["regex"], flags=re.IGNORECASE))
        for spec in TYPO_PATTERNS
    ]
    by_name: dict[str, dict[str, Any]] = {}
    for spec, pattern in compiled:
        by_name[spec["name"]] = {
            "name": spec["name"],
            "suggestion": spec["suggestion"],
            "risk": spec["risk"],
            "note": spec["note"],
            "count": 0,
            "examples": [],
        }

    for row in labels:
        label = row["label"]
        for spec, pattern in compiled:
            if not pattern.search(label):
                continue
            bucket = by_name[spec["name"]]
            bucket["count"] += 1
            if len(bucket["examples"]) < 5:
                bucket["examples"].append(label)

    out = []
    for bucket in by_name.values():
        if bucket["count"]:
            examples = " || ".join(bucket.pop("examples"))
            bucket["examples"] = examples
            out.append(bucket)
    out.sort(key=lambda r: (-r["count"], r["risk"], r["name"]))
    return out


def dangerous_token_counts(labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counters: dict[str, int] = defaultdict(int)
    examples: dict[str, list[str]] = defaultdict(list)
    patterns = {
        token: re.compile(rf"\b{re.escape(token)}\b", flags=re.IGNORECASE)
        for token in DANGEROUS_GLOBAL_TOKENS
    }
    for row in labels:
        label = row["label"]
        for token, pattern in patterns.items():
            if pattern.search(label):
                counters[token] += 1
                if len(examples[token]) < 5:
                    examples[token].append(label)
    rows = []
    for token, count in sorted(counters.items(), key=lambda item: (-item[1], item[0])):
        rows.append(
            {
                "token": token,
                "count": count,
                "warning": DANGEROUS_GLOBAL_TOKENS[token],
                "examples": " || ".join(examples[token]),
            }
        )
    return rows


def load_no_verb_first_tokens(taxonomy_dir: Path | None) -> list[dict[str, Any]]:
    if not taxonomy_dir:
        return []
    path = taxonomy_dir / "no_verb_first_tokens.csv"
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            token = (row.get("token") or row.get("first_token") or row.get("word") or "").strip().lower()
            if not token:
                continue
            count_text = row.get("count") or row.get("segments") or "0"
            try:
                count = int(float(count_text))
            except ValueError:
                count = 0
            if token in OBJECT_FRAGMENT_TOKENS:
                bucket = "object_fragment"
            elif token in LIKELY_VERB_REVIEW_TOKENS:
                bucket = "likely_missing_verb_vocab"
            elif token in DANGEROUS_GLOBAL_TOKENS:
                bucket = "contextual_typo_review"
            elif token in {"no", "none", "nothing"}:
                bucket = "no_action"
            else:
                bucket = "review"
            rows.append({"token": token, "count": count, "bucket": bucket})
    rows.sort(key=lambda r: (-int(r["count"]), str(r["token"])))
    return rows


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip().lower() for v in value if str(v).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                parsed = json.loads(text)
                return normalize_list(parsed)
            except json.JSONDecodeError:
                pass
        return [part.strip().lower() for part in re.split(r"[|,;]", text) if part.strip()]
    return [str(value).strip().lower()]


def target_integrity(taxonomy_dir: Path | None) -> dict[str, Any]:
    if not taxonomy_dir:
        return {}
    path = taxonomy_dir / "segment_aux_targets.jsonl"
    if not path.exists():
        return {}

    punct_rows = []
    descriptor_no_noun_rows = []
    verb_as_noun_rows = []
    object_counts = {
        word: {"noun": 0, "descriptor": 0}
        for word in COMMON_OBJECT_HEADS
    }
    noun_counter: Counter[str] = Counter()
    descriptor_counter: Counter[str] = Counter()
    verb_counter: Counter[str] = Counter()
    total_rows = 0

    verb_vocab = set(read_vocab_csv(taxonomy_dir / "verb_vocab.csv"))
    for row in iter_jsonl(path):
        total_rows += 1
        nouns = normalize_list(row.get("nouns") or row.get("noun_targets") or row.get("noun"))
        descriptors = normalize_list(row.get("descriptors") or row.get("descriptor_targets") or row.get("descriptor"))
        verbs = normalize_list(row.get("verbs") or row.get("verb_targets") or row.get("verb"))
        noun_counter.update(nouns)
        descriptor_counter.update(descriptors)
        verb_counter.update(verbs)

        if any(token in {".", ",", ";", ":"} for token in nouns):
            if len(punct_rows) < 10:
                punct_rows.append(row)
        if descriptors and not nouns:
            if len(descriptor_no_noun_rows) < 10:
                descriptor_no_noun_rows.append(row)
        leaks = sorted(set(nouns) & verb_vocab)
        if leaks and len(verb_as_noun_rows) < 10:
            sample = dict(row)
            sample["_leaked_nouns"] = leaks
            verb_as_noun_rows.append(sample)
        for word in COMMON_OBJECT_HEADS:
            if word in nouns:
                object_counts[word]["noun"] += 1
            if word in descriptors:
                object_counts[word]["descriptor"] += 1

    return {
        "total_rows": total_rows,
        "punct_noun_rows": len(punct_rows),
        "descriptor_no_noun_rows": len(descriptor_no_noun_rows),
        "verb_as_noun_sample_rows": len(verb_as_noun_rows),
        "object_head_counts": object_counts,
        "top_verbs": verb_counter.most_common(50),
        "top_nouns": noun_counter.most_common(50),
        "top_descriptors": descriptor_counter.most_common(50),
        "punct_noun_examples": punct_rows,
        "descriptor_no_noun_examples": descriptor_no_noun_rows,
        "verb_as_noun_examples": verb_as_noun_rows,
    }


def taxonomy_summary(taxonomy_dir: Path | None) -> dict[str, Any]:
    if not taxonomy_dir:
        return {}
    summary_path = taxonomy_dir / "taxonomy_coverage_summary.json"
    summary = {}
    if summary_path.exists():
        summary = load_json(summary_path)
    verb_vocab = read_vocab_csv(taxonomy_dir / "verb_vocab.csv")
    noun_vocab = read_vocab_csv(taxonomy_dir / "noun_vocab.csv")
    if verb_vocab:
        summary["verb_vocab_size"] = len(verb_vocab)
        summary["top_20_verbs_from_vocab"] = verb_vocab.most_common(20)
    if noun_vocab:
        summary["noun_vocab_size"] = len(noun_vocab)
        summary["top_20_nouns_from_vocab"] = noun_vocab.most_common(20)
    return summary


def write_report(
    path: Path,
    label_count: int,
    typo_rows: list[dict[str, Any]],
    dangerous_rows: list[dict[str, Any]],
    residual_rows: list[dict[str, Any]],
    integrity: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    lines = []
    lines.append("# Taxonomy Cleanup Audit")
    lines.append("")
    lines.append(f"- Labels scanned: {label_count:,}")
    if summary:
        lines.append(f"- Verb vocab size: {summary.get('verb_vocab_size', 'n/a')}")
        lines.append(f"- Noun vocab size: {summary.get('noun_vocab_size', 'n/a')}")
        if "verb_clause_coverage_percent" in summary:
            lines.append(f"- Verb clause coverage: {summary['verb_clause_coverage_percent']}")
    if integrity:
        lines.append(f"- Aux rows scanned: {integrity.get('total_rows', 0):,}")
        lines.append(f"- Punctuation-as-noun sample rows: {integrity.get('punct_noun_rows', 0)}")
        lines.append(f"- Descriptor-without-noun sample rows: {integrity.get('descriptor_no_noun_rows', 0)}")
        lines.append(f"- Verb-as-noun sample rows: {integrity.get('verb_as_noun_sample_rows', 0)}")

    lines.append("")
    lines.append("## Typo Candidates")
    if typo_rows:
        for row in typo_rows[:30]:
            lines.append(
                f"- `{row['name']}`: {row['count']} matches, risk={row['risk']}, suggestion={row['suggestion']}. {row['note']}"
            )
            if row.get("examples"):
                lines.append(f"  Examples: {row['examples']}")
    else:
        lines.append("- No known typo patterns matched.")

    lines.append("")
    lines.append("## Dangerous Tokens")
    if dangerous_rows:
        for row in dangerous_rows[:30]:
            lines.append(f"- `{row['token']}`: {row['count']} matches. {row['warning']}")
            if row.get("examples"):
                lines.append(f"  Examples: {row['examples']}")
    else:
        lines.append("- No dangerous broad-replacement tokens matched.")

    lines.append("")
    lines.append("## No-Verb Residual First Tokens")
    if residual_rows:
        for row in residual_rows[:50]:
            lines.append(f"- `{row['token']}`: {row['count']} ({row['bucket']})")
    else:
        lines.append("- No `no_verb_first_tokens.csv` found or no residuals reported.")

    if integrity and integrity.get("object_head_counts"):
        lines.append("")
        lines.append("## Common Object Heads")
        for word, counts in integrity["object_head_counts"].items():
            total = counts["noun"] + counts["descriptor"]
            if total:
                lines.append(f"- `{word}`: noun={counts['noun']}, descriptor={counts['descriptor']}")

    lines.append("")
    lines.append("## Recommended Next Step")
    lines.append(
        "Approve only low-risk surgical cleanup rules first, rerun taxonomy generation, then rerun this audit before using auxiliary targets for training."
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, help="Source label JSON/JSONL/CSV file.")
    parser.add_argument("--taxonomy-dir", type=Path, help="Directory containing taxonomy artifacts.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for audit artifacts.")
    args = parser.parse_args()

    if not args.labels and not args.taxonomy_dir:
        raise SystemExit("Provide --labels, --taxonomy-dir, or both.")
    if args.labels and not args.labels.exists():
        raise SystemExit(f"Labels file does not exist: {args.labels}")
    if args.taxonomy_dir and not args.taxonomy_dir.exists():
        raise SystemExit(f"Taxonomy directory does not exist: {args.taxonomy_dir}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    labels = read_labels(args.labels)
    typo_rows = collect_pattern_matches(labels)
    dangerous_rows = dangerous_token_counts(labels)
    residual_rows = load_no_verb_first_tokens(args.taxonomy_dir)
    integrity = target_integrity(args.taxonomy_dir)
    summary = taxonomy_summary(args.taxonomy_dir)

    write_csv(
        args.output_dir / "typo_candidates.csv",
        typo_rows,
        ["name", "count", "risk", "suggestion", "note", "examples"],
    )
    write_csv(
        args.output_dir / "dangerous_token_counts.csv",
        dangerous_rows,
        ["token", "count", "warning", "examples"],
    )
    write_csv(
        args.output_dir / "residual_first_tokens.csv",
        residual_rows,
        ["token", "count", "bucket"],
    )
    (args.output_dir / "target_integrity.json").write_text(
        json.dumps(integrity, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "taxonomy_cleanup_summary.json").write_text(
        json.dumps(
            {
                "labels_scanned": len(labels),
                "typo_candidate_types": len(typo_rows),
                "dangerous_token_types": len(dangerous_rows),
                "residual_token_types": len(residual_rows),
                "taxonomy_summary": summary,
                "target_integrity": {
                    key: value
                    for key, value in integrity.items()
                    if not key.endswith("_examples")
                },
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    write_report(
        args.output_dir / "report.md",
        len(labels),
        typo_rows,
        dangerous_rows,
        residual_rows,
        integrity,
        summary,
    )
    print(f"Wrote audit artifacts to {args.output_dir}")


if __name__ == "__main__":
    main()
