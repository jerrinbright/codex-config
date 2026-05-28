# Research Loop

Use this when work spans multiple runs or uncertain model/data choices.

## Inner Loop

1. Pick one hypothesis.
2. Define the smallest experiment that can falsify or support it.
3. Run with durable config/metadata.
4. Evaluate on the same slice or heldout set.
5. Record keep/discard/iterate.

## Outer Loop

After a group of experiments:

- summarize what changed,
- identify consistent wins and regressions,
- update the research direction,
- decide the next experiment family.

## Evidence Rules

- Name exact checkpoints, datasets, campaign IDs, and output paths.
- Do not compare models across changed eval sets without saying so.
- Treat HTML viewers as inspection artifacts, not metrics by themselves.
- Keep test sets untouched by training and hyperparameter selection.

## Good Research Log Entry

```text
Date:
Question:
Run/config:
Dataset:
Baseline:
Metric:
Result:
Decision:
Follow-up:
```

