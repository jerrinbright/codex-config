# Evidence And Hypotheses

This reference distills useful patterns from literature-review, hypothesis-generation, scientific-critical-thinking, scholar-evaluation, and statistical-analysis skills.

## Literature Review Checklist

- Define scope and search terms.
- Prefer primary papers and official docs.
- Record search date for fast-moving ML topics.
- Extract method, data, metrics, compute, baseline, and limitations.
- Deduplicate related papers or tool versions.
- Separate evidence from interpretation.

## Hypothesis Generation

Good hypotheses are:

- specific,
- testable,
- falsifiable,
- connected to observed failure modes,
- paired with predicted metric changes.

Template:

```text
Observation:
Hypothesis:
Mechanism:
Prediction:
Minimal experiment:
Success metric:
Failure interpretation:
```

## Critical Evaluation

Check:

- Is the baseline fair?
- Are metrics comparable?
- Is the dataset representative?
- Is there leakage or selection bias?
- Are ablations sufficient?
- Are examples cherry-picked?
- Is compute/cost reported?
- Are claims stronger than evidence?

## Statistical Sanity

For model/eval comparisons:

- include denominators,
- report confidence intervals when sample size is small,
- use paired comparisons when the same segments/examples are evaluated by multiple models,
- avoid overclaiming from tiny slices,
- separate exploratory from confirmatory evals.

