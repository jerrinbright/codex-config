# Paul Optimizer Experiment Plan

## Goal

- Repo:
- Service:
- Target metric:
- Desired improvement:
- Max acceptable quality regression:
- Runtime/hardware:

## Verifier

- Verifier owner:
- Correctness gate:
- Quality gate:
- Throughput metric:
- Determinism/failure gate:
- Known blind spots:

## Baseline

```text
command:
git_commit:
inputs:
hardware:
env:
output_path:
```

| Metric | Value |
|--------|------:|
| wall time | |
| throughput | |
| GPU util | |
| CPU quota | |
| VRAM peak | |
| output count | |
| quality | |
| failures | |

## Sub-Agent Matrix

| Agent | Search Space | Candidate Budget | Files/Scope | Risk |
|-------|--------------|-----------------:|-------------|------|
| verifier | gates/report | 1 | verifier/scripts | low |
| concurrency | lanes/MPS/caps | | | |
| resident | warm pools/cache | | | |
| video-io | decode/artifacts | | | |
| gpu-runtime | TRT/compile/fp16 | | | |
| algorithmic | cadence/output modes | | | |
| native | C++/CUDA/PyBind | | | high |

## Candidate Log

| ID | Agent | Change | E2E Speed | Quality | Gate | Decision |
|----|-------|--------|----------:|--------:|------|----------|
| baseline | | | | | | |

## Rejected Levers

| Lever | Reason | Evidence |
|-------|--------|----------|

