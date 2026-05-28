# Prompt Evaluation

Use this when changing prompts, schemas, examples, or tiny model extraction behavior.

## Test Set

Build a small fixed set with:

- easy examples,
- ambiguous examples,
- known hallucination traps,
- long labels,
- labels with multiple objects,
- labels with locations/secondary objects,
- examples that previously failed.

## Metrics

```text
json_validity
schema_validity
copy_only_rate
exact_field_accuracy
similar_field_accuracy
empty_when_expected
hallucination_rate
latency_per_unique_input
cache_hit_rate
```

## Change Control

- Version prompts.
- Store model name and prompt version in cache metadata.
- Compare old vs new on the same test set.
- Keep examples for every regression bucket.

