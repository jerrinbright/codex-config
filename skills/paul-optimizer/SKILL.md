---
name: paul-optimizer
description: "Verifier-first swarm optimization for CV/ML Python services. Use when the user asks to speed up a repo/service, run an overnight optimization campaign, improve GPU throughput/cost, or apply Paul-style optimization patterns: first build a strong verifier sub-agent, then spawn specialized optimizer sub-agents across concurrency, resident execution, video/I/O, GPU runtime, native C++/CUDA/TensorRT, and algorithmic workload-reduction search spaces."
---

# Paul Optimizer

## Purpose

Run a verifier-led optimization swarm for CV/ML services. The main agent must first create or harden a verifier sub-agent that can judge correctness, quality, throughput, determinism, and operability. Only after that verifier exists may optimizer sub-agents explore speedups.

The core rule:

```text
First create the judge.
Then unleash many builders.
Only the judge decides what survives.
```

This skill is inspired by repeated successful Mecka optimization patterns:

- Native resident C++/CUDA/TensorRT hosts replacing Python orchestration.
- Warm in-process or out-of-process model/process pools.
- Multi-lane GPU concurrency, MPS, and hardware-aware CPU/VRAM/NVENC caps.
- GPU-resident video decode/encode and reduced artifact I/O.
- Kernel/runtime tuning such as TensorRT, torch.compile, cuBLASLt, fp16/channels-last, and carefully gated quantization.
- Algorithmic workload reduction such as sparse sampling, interpolation, output-mode reduction, and cheaper detector cadence.
- Aggressive rejection of tempting but unsafe or non-e2e-winning levers.

Use this skill when the user wants a serious speed campaign, not a single small local tweak.

## Non-Negotiables

- Do not optimize before the verifier exists or is explicitly declared sufficient.
- Do not call a candidate faster unless it improves an end-to-end metric on comparable hardware.
- Do not accept a speedup that fails correctness, quality, determinism, crash-rate, or rollback gates.
- Do not trust optimizer sub-agents. They propose candidates; the verifier certifies them.
- Do not let microbenchmarks override real worker-path evidence.
- Do not hide semantic changes inside "optimization." Sampling, batching, output format, quantization, precision, cadence, and native rewrites all need explicit quality gates.
- Keep rollback knobs for risky changes: env flags, kill switches, strict mode, fallbacks, or disabled-by-default candidates.
- Record rejected levers and why so future agents do not rediscover them blindly.

## Required Reading

Read these files only as needed:

- `references/swarm-architecture.md`: verifier-first swarm design and agent roles.
- `references/paul-patterns.md`: optimization pattern catalog distilled from the PRs.
- `references/verifier-contract.md`: required verifier gates and report schema.
- `templates/experiment_plan.md`: plan format for an optimization campaign.
- `templates/verifier_brief.md`: prompt/brief for the verifier sub-agent.
- `templates/subagent_brief.md`: prompt/brief for optimizer sub-agents.
- `templates/final_report.md`: final evidence/report format.

## Operating Loop

### 1. Scope The Service

Identify:

- Repo, branch, entrypoint, worker path, Docker/Modal/RunPod/Temporal path.
- Target metric: episodes/hr, fps, wall time, latency, GPU-hours, cost, queue drain rate, VRAM, CPU, disk, or failure rate.
- Representative inputs: episodes, videos, heldout split, production goldens, or synthetic smoke slice.
- Baseline command and environment.
- Deployment constraints: GPU types, concurrency limits, queue names, image build path, secrets/assets availability.
- Quality bar: byte-identical, value-identical, MPJPE delta, IoU, SSIM, trajectory drift, privacy under-blur, or product-signoff threshold.

If the service path is ambiguous, inspect before asking. Ask only when the missing choice would make the verifier invalid.

### 2. Create The Verifier Sub-Agent First

Create a verifier sub-agent or verifier plan before optimization begins.

The verifier must produce:

- Baseline command and candidate command.
- Correctness gate.
- Quality metric and thresholds.
- Throughput metric.
- Same-hardware or comparable-hardware policy.
- Artifact comparison method.
- Determinism/crash/failure gate.
- Report format.
- Known blind spots.

Use `templates/verifier_brief.md` when launching or simulating the verifier sub-agent.

The verifier should prefer real service paths:

- Temporal/Modal/RunPod worker path over toy script.
- Same-pod A/B over cross-machine comparisons.
- Fresh end-to-end output over stale artifacts.
- Worker-output artifacts over internal stage-only files.

### 3. Run Baseline

Run or collect a baseline after the verifier is defined.

Record:

```text
git_commit
command
input_ids
gpu_type
gpu_count
cpu_quota
vram
worker_image
env
total_wall_time
throughput
per_stage_timing
output_count
quality_metrics
failure_count
cost_estimate
artifact_paths
```

If a baseline cannot be run because it is a long job, deployment, or expensive GPU run, follow safety gates and ask the user before launching. If the user explicitly asked for an overnight run, ensure progress logging and durable output paths first.

### 4. Spawn Optimizer Sub-Agents

Spawn multiple optimizer sub-agents only after the verifier is available. Give each one a non-overlapping search space and tell it that the verifier is the only acceptance authority.

Default sub-agent set:

1. **Concurrency Agent**
   - `MAX_CONCURRENT_ACTIVITIES`, worker lanes, MPS, multi-replica per GPU.
   - CPU quota, OpenMP/BLAS threads, DataLoader workers, writer threads.
   - VRAM-aware caps, NVENC session caps, BA/encoder serialization.

2. **Resident Execution Agent**
   - Warm model reuse, process pools, resident hosts, shared engines.
   - Avoid per-episode model loads and subprocess startup.
   - Cache policy and thread/process safety.

3. **Video And I/O Agent**
   - NVDEC/NVENC, no disk frame dumps, decode/compute overlap.
   - R2/S3/Mongo prefetch, compact JSON, JSONL shards, upload/download pipelining.
   - Artifact volume reduction and bounded queues.

4. **GPU Runtime Agent**
   - TensorRT, torch.compile, cuBLASLt algo forcing, fp16/channels-last, TF32, quantization.
   - Batch size, CUDA streams, graph capture, kernel-level profiling.
   - Must quantify e2e effect, not only kernel speed.

5. **Algorithmic Workload Agent**
   - Sample FPS/cadence, sparse inference + interpolation.
   - Output-mode reduction, skip unnecessary undistort/fanout, precheck gates.
   - Must require product/quality signoff for semantic changes.

6. **Native Rewrite Agent**
   - C++/CUDA/PyBind/TensorRT hot path proposals.
   - Only proceed when verifier is strong and the bottleneck justifies blast radius.
   - Must include feature flag, fail-loud startup, fallback/rollback, and parity evidence.

Use `templates/subagent_brief.md` for each agent.

### 5. Evaluate Candidates

For every candidate:

1. Apply patch or config in isolation.
2. Run candidate benchmark on the baseline slice.
3. Run verifier.
4. Store logs, metrics, artifacts, git diff, env, and hardware.
5. Mark `accept`, `reject`, or `inconclusive`.

Hard-fail candidate if:

- Output count changes unexpectedly.
- Quality metric exceeds threshold.
- Privacy/correctness gate fails.
- Candidate only improves a microbenchmark but e2e is flat/slower.
- Candidate needs unavailable hardware/assets.
- Failure/retry rate worsens.
- Rollback path is missing for risky changes.

For noisy cloud runs, repeat near-ties or compare medians.

### 6. Combine Winners

Only combine candidates that passed individually. Re-run the verifier on the combined stack because speedups interact.

Watch for common interaction failures:

- Batch size win disappears after pipelining removes idle time.
- Quantization wins a model stage but loses e2e due Amdahl limits.
- Concurrency improves throughput but breaks determinism or CPU oversubscribes.
- Model cache saves load time but OOMs under in-process concurrency.
- MPS improves throughput but introduces small numeric transients.

### 7. Produce Patch Or PR Evidence

The final output must include:

- Baseline vs candidate table.
- Correctness/quality gate result.
- Hardware and env.
- Implementation summary.
- Rollback switch.
- Known risks.
- Rejected levers table.
- Rollout recommendation.

Use `templates/final_report.md`.

## Paul-Style Search Spaces

Always consider these before declaring a service "optimized":

### Concurrency And Scheduling

- Multi-lane resident workers.
- MPS with shared daemon and shared IPC requirements.
- Per-GPU replicas vs activity threads.
- CPU quota-aware thread caps applied before heavy imports.
- VRAM-aware concurrency bounds.
- DataLoader/process/writer fanout caps.
- GPU BA/NVENC/session serialization.
- Download/GPU/upload pipeline gates.

### Resident Execution

- Warm process pools for prep.
- Warm TensorRT/model engines.
- In-process PyBind extension.
- Shared engine/device memory buffers.
- Cache off by default when in-process concurrency risks VRAM leaks.
- Lock/double-check caches when enabled.

### Video And Artifact I/O

- NVDEC and NVENC.
- Avoid frame dumps and redundant JSON scans.
- Compact artifacts with value-equivalence verifier.
- Decode/compute overlap with bounded queues and correct teardown.
- Fewer output streams when product can accept composite/fisheye-only outputs.

### GPU Runtime

- TensorRT export with strict I/O validation and md5 pinning.
- torch.compile where deterministic and warmup-controlled.
- cuBLASLt algo sweep with verified-shape fallback.
- fp16/channels-last after GT or parity clearance.
- Quantization only after e2e and quality proof.
- Reject if the faster kernel does not move total wall time.

### Algorithmic Workload Reduction

- Sparse inference + interpolation.
- Detector/keyframe cadence changes.
- Sample FPS changes.
- Precheck skip decisions.
- Reduced fanout/undistort.
- Must be treated as semantic unless verifier proves value equivalence.

### Native Rewrite

- C++ host for Python orchestration overhead.
- CUDA kernels for blur/remap/preprocess/NMS/ROIAlign/etc.
- TensorRT engines for models.
- PyBind in-process seam.
- Fail-loud if enabled but native artifacts are missing.
- Default-off unless product has signed rollout.

## Verifier Gate Examples

Use the strongest relevant gate:

```text
byte-identical artifact md5
value-identical deep JSON compare
MPJPE / PA-MPJPE delta
IoU / detection parity
under-blur leak count and over-blur budget
trajectory path-length drift
registered image count / reprojection error
SSIM / frame alignment
output count equality
worker-path smoke test
crash/retry count
determinism repeat run
```

## Reporting Tone

Be concrete. Do not overclaim.

Say:

- "Candidate passed verifier on 5 episodes and improved 91 -> 247 ep/hr on RTX PRO 6000."
- "Rejected: FP8 made backbone faster/slower but e2e lost or quality failed."
- "Inconclusive: same-pod A/B needed; current hardware is core-starved."

Do not say:

- "Should be faster."
- "Probably safe."
- "Native path is equivalent" without verifier evidence.

