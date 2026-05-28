# Observability And Regression

Use this for recurring evals, production monitoring, LLM traces, or model quality gates.

## Tool Routing

- **W&B / TensorBoard / MLflow**: training curves, metrics, artifacts, model lineage.
- **Phoenix / LangSmith / Langfuse**: LLM traces, prompt/output debugging, online quality monitoring.
- **Local summaries**: fastest path for ad hoc Modal evals and checkpoint comparisons.

## Regression Gate

Define:

```text
eval_slice
gt_source
metric
minimum_acceptance
allowed_regressions
report_path
owner
```

## Trace Fields

For LLM/tool pipelines:

- input id,
- prompt version,
- model version,
- tool calls,
- parsed output,
- validation errors,
- latency,
- cost,
- final decision.

