# Data Quality And Curation

Use this when building or reviewing fine-tuning datasets.

## Curation Checks

- Remove test/heldout campaigns before training.
- Track label provenance: human, auditor-corrected, model-derived, synthetic, noisy.
- Deduplicate near-identical segments when repetition can dominate.
- Preserve hard negatives and realistic failure modes separately from clean GT.
- Record filtering rules and counts.

## Dataset Mix

Report:

```text
clean_gt_count
noisy_prev_label_count
synthetic_count
auditor_corrected_count
excluded_test_count
duplicate_or_repetition_filter_count
```

## Risk

- More data can hurt if label provenance is mixed silently.
- Synthetic/noisy rows need explicit ratios.
- Holdout/test data must stay out of tuning decisions.

