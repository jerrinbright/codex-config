# Tracking Systems

## Routing

- **Local JSON/Markdown summaries**: fastest, best for ad hoc Modal/repo work.
- **TensorBoard**: training curves and scalar histories.
- **Weights & Biases**: broad experiment tracking, artifacts, sweeps, team dashboards.
- **MLflow**: model registry, lifecycle, local/server tracking.
- **SwanLab**: experiment tracking alternative used in some AI workflows.

## Required Metadata

```text
run_name
git_commit
repo
branch
command
env vars that affect behavior
model/checkpoint
dataset manifests
train/val/test exclusions
metrics
output paths
cost/time
known caveats
```

## Comparison Hygiene

- Same eval slice before ranking models.
- Same normalization/synonym policy.
- Same frame/crop/prompt settings for verifier comparisons.
- Explicitly mark model-derived pseudo-GT vs human GT.

