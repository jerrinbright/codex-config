---
name: model-evaluation
description: "Evaluate and compare AI model outputs against ground truth, auditor corrections, baselines, top-k predictions, verifier outputs, and regression sets. Use for accuracy tables, exact/similar/wrong buckets, action/object error categories, top-1/top-3, overlap/agreement analysis, heldout campaign checks, and model comparison HTML/data artifacts."
---

# Model Evaluation

## Purpose

Produce trustworthy model comparisons with clear denominators, metrics, examples, and caveats.

Read `references/audit-label-eval.md` for audit/campaign/object-label evaluation patterns.

## Workflow

1. **Define eval slice**
   - Episodes/segments/campaigns, GT source, model outputs, checkpoint versions, and exclusions.

2. **Normalize outputs**
   - Preserve raw text.
   - Add normalized object/action fields when needed.
   - Mark exact, similar/synonym, partial, and wrong separately.

3. **Compute metrics**
   - Top-1 and top-k accuracy.
   - Exact and similar-accepted accuracy.
   - Error buckets: wrong object, missing action, wrong action, color, secondary object/location, hallucination.
   - Agreement/overlap between model and verifier.
   - Gated policy coverage, salvage, false override, and net delta.

4. **Inspect examples**
   - Include representative wins, regressions, and ambiguous cases.
   - Build HTML viewer with `html-video-viewer` when video context matters.

5. **Report**
   - State denominators everywhere.
   - Call out if GT is inferred, audited, or model-derived.
   - Do not compare runs with different eval slices as if they are identical.

## Output Shape

```md
**Evaluation**
- Slice:
- GT source:
- Models:
- Result:
- Best model:
- Error buckets:
- Caveats:
```

