# Statistical Comparison

Use this when model differences are close, sample sizes are small, or the user wants reliable claims.

## Paired Eval

If two models are evaluated on the same examples, compare paired outcomes:

```text
A correct, B correct
A correct, B wrong
A wrong, B correct
A wrong, B wrong
```

Report:

- total paired examples,
- net wins,
- win/loss ratio,
- examples changed from wrong to right,
- examples changed from right to wrong.

## Confidence Intervals

For accuracy on `n` examples, include a binomial confidence interval when:

- `n < 200`,
- improvements are small,
- results will decide training/deployment,
- the user asks for statistical confidence.

## Avoid Overclaiming

- Do not call a 1-2 point difference meaningful on a tiny slice without uncertainty.
- Do not mix slices with different GT quality.
- Do not tune on the final test set and then report it as unbiased.
- Label exploratory metrics as exploratory.

