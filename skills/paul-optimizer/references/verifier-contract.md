# Verifier Contract

The verifier is the reward function. It must be built before optimizer sub-agents make risky changes.

## Required Sections

```yaml
verifier_name:
repo:
service_entrypoint:
baseline_command:
candidate_command:
inputs:
hardware_policy:
correctness_gate:
quality_gate:
throughput_metric:
determinism_gate:
failure_gate:
artifact_policy:
thresholds:
report_path:
known_blind_spots:
```

## Gate Types

### Correctness Gate

Examples:

- Same final output count.
- Same expected artifact names.
- No missing shards/streams.
- No new exceptions or retries.
- Worker path completes, not just a local helper.

### Quality Gate

Examples:

- MPJPE / PA-MPJPE delta.
- Detection IoU and under/over-detect budgets.
- Privacy under-blur count must be zero.
- Trajectory path-length drift.
- Registered image count and reprojection error.
- SSIM/frame alignment.
- Deep JSON value equivalence.

### Throughput Gate

Examples:

- Episodes/hour.
- FPS.
- Wall time per episode.
- GPU-hours per episode.
- Queue drain rate.
- Cost estimate.

### Determinism Gate

Examples:

- md5 equality across repeat runs.
- Numeric delta under known floor.
- Warmup/autotune state fingerprint.
- MPS transient rate and max magnitude.

### Operability Gate

Examples:

- Feature flag exists.
- Kill switch exists.
- Strict mode fails loudly when required assets are missing.
- Fallback path is tested or intentionally disabled.
- Logs identify candidate vs baseline pipeline.

## Baseline/Candidate Comparison Rules

- Same git commit except candidate patch/config, unless comparing branches intentionally.
- Same hardware class, or state why comparison is only directional.
- Same inputs and output scope.
- Fresh artifacts from each run.
- Include failure and retry counts.
- Include stage-level telemetry when available.

## Pass/Fail Format

```md
| Gate | Baseline | Candidate | Threshold | Status |
|------|----------|-----------|-----------|--------|
| output count | | | exact | PASS/FAIL |
| quality | | | | PASS/FAIL |
| throughput | | | | PASS/FAIL |
| determinism | | | | PASS/FAIL |
| failures | | | | PASS/FAIL |
```

## Blind Spot Rules

If a verifier does not cover a risk, name it directly:

- "Does not check visual alignment."
- "Does not run real Temporal worker path."
- "Does not cover secondary camera videos."
- "Only verifies one GPU type."

Do not accept a high-risk candidate when the relevant blind spot is material.

