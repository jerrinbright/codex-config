# Audit Label Evaluation

## Metrics

Useful tables:

```text
Model | Exact | Similar Accepted | Wrong | Total
Model | Object Top-1 | Object Top-3 | Action Top-1 | Full Label
```

For verifier agreement:

```text
Molmo correct, verifier agrees
Molmo correct, verifier disagrees
Molmo wrong, verifier agrees
Molmo wrong, verifier disagrees
```

For gated correction:

```text
coverage
salvages
false_overrides
wrong_overrides
net_delta
effective_accuracy
```

## Similar/Synonym Rules

Accept only if task meaning is preserved:

- "cup" vs "mug" may be similar depending context.
- "pants" vs "skirt" is wrong.
- "red" vs "orange" is usually wrong if color matters.
- "table" vs "pile" may be secondary-location confusion, not primary object match.

## Reporting

Always include:

- total segments,
- skipped/unknown count,
- GT provenance,
- checkpoint paths or model versions,
- examples for biggest failure buckets.

