---
name: dataset-label-quality-auditor
description: Audit action-label datasets for training-quality issues such as malformed labels, incomplete boundary fragments, random comma usage, "and" used as an action separator, overloaded multi-action labels, adjust/no-action ambiguity, repeated labels, previous-label copy pressure, and noisy verb/object vocabulary. Use when checking Naruto/Mecka/Molmo redelivery JSON, preannotations, episode_vlm_segments exports, or any segment-label dataset before training.
---

# Dataset Label Quality Auditor

Use this skill when the user wants automated analysis of action-label quality before training or finetuning.

## Default Workflow

1. Locate the label source: usually a JSON file with episode rows and nested `preannotations`, or a flat list of segment rows.
2. Run the bundled audit script:

```bash
python3 /Users/jerrinbright/Desktop/jb_ws/codex-config/skills/dataset-label-quality-auditor/scripts/audit_label_quality.py \
  --input /path/to/labels.json \
  --output-dir /tmp/label_quality_audit
```

3. Report the highest-signal counts first:
   - incomplete labels that start/end with connector words or punctuation
   - comma misuse, especially `, with`, `, from`, first-word commas, and leading commas
   - `and <action verb>` action separators
   - labels with too many action clauses
   - `adjust` / `reposition` / vague-motion labels
   - adjacent repeated labels and all-same episodes
4. Use examples from `issue_rows.csv` and `report.md`; do not handwave.

## Input Shapes

The script supports:

- Episode-level JSON:
  - `[{ "episode_id": "...", "preannotations": [{ "label": "...", "event_annotation_start_time": 0, ... }] }]`
- Flat JSON:
  - `[{ "episode_id": "...", "label": "...", "start_seconds": 0, ... }]`
- Dict wrapping a list:
  - `{ "episodes": [...] }`, `{ "rows": [...] }`, or any dict where the largest list of dicts contains labels.

## Output Files

The script writes:

- `summary.json`: machine-readable metrics.
- `issue_rows.csv`: one row per issue hit, with reason flags and label text.
- `report.md`: compact human-readable report with examples.

## Interpretation Notes

- Boundary-fragment counts are usually high precision but low volume.
- `and <verb>` is a stronger training-style issue when the labeling convention expects comma-separated actions.
- Multi-action heuristics are approximate; use them to sample and route review, not as the only deletion rule.
- Adjacent repeat and previous-label-copy pressure often matter more than rare malformed labels because they affect many rows.
- Keep examples grouped by issue type so annotation leads can convert them into concrete policy changes.
