# Paul-Style Optimization Pattern Catalog

## 1. Native Resident Host

Replace Python orchestration with a resident C++/CUDA/TensorRT host when Python/GIL/subprocess/model-load overhead dominates.

Signals:

- Multiple Python processes each load full model copies.
- GPU utilization is low while CPU orchestration is high.
- MPS helps only a little because the process model is the bottleneck.
- Per-episode startup and serialization dominate.

Required gates:

- Python-vs-native parity.
- Worker-path smoke.
- Feature flag and fail-loud startup.
- Rollback to Python path.

## 2. Warm Process Or Model Pool

Move repeated prep/model stages into warm processes or persistent hosts.

Signals:

- Same models loaded every episode.
- Stage is GIL-bound or unsafe in worker threads.
- GPU is underutilized at serial or low concurrency.

Risks:

- Pool branch misses fields the legacy branch returns.
- Spawn/fork CUDA hazards.
- Crash loops if default-on path is not worker-path tested.

Required gates:

- Seam test that both branches return the same key set.
- Same-pod A/B for final worker path.
- Crash/retry count.

## 3. Hardware-Aware Concurrency

Tune concurrency from cgroup CPU, GPU VRAM, GPU type, and stage-specific resource limits.

Signals:

- Worker has static `MAX_CONCURRENT_ACTIVITIES`.
- GPU idle during CPU/I/O phases.
- Small GPUs OOM at large concurrency.
- CPU-bound stages collapse when too many episodes run.

Required gates:

- Same-pod A/B.
- CPU quota and VRAM recorded.
- Caps apply before heavy imports when needed.
- Explicit kill switch.

## 4. MPS / Multi-Replica Per GPU

Use MPS when multiple worker processes need to share one GPU with lower scheduling overhead.

Signals:

- One process cannot saturate GPU.
- Thread concurrency causes shared-state hazards.
- Process isolation helps but normal multi-process GPU scheduling is inefficient.

Risks:

- MPS daemon lifecycle.
- Shared IPC/pipe mount misconfiguration silently losing gains.
- Small numeric transients.

Required gates:

- MPS sharing check.
- Determinism repeat runs.
- Strict fallback recipe when bitwise output is required.

## 5. Video And Artifact Pipeline

Keep decode/encode and artifact generation off the critical path.

Levers:

- NVDEC/NVENC.
- In-memory frame pipeline.
- Decode/compute overlap.
- Compact JSON or JSONL shards.
- Avoid redundant uploads/downloads.
- Reduce output fanout if product accepts it.

Required gates:

- Frame alignment.
- Output count and artifact value comparison.
- SSIM or visual diff when video output changes.

## 6. GPU Runtime / Kernel Wins

Tune the runtime only after knowing GPU time is the bottleneck.

Levers:

- TensorRT.
- torch.compile.
- cuBLASLt algo forcing.
- fp16/channels-last.
- TF32.
- Quantization.
- CUDA kernels for hot operators.

Required gates:

- End-to-end wall time, not only kernel time.
- Numeric/quality delta.
- Fallback on unverified shape/GPU/CUDA.
- Determinism if concurrency/MPS is used.

## 7. Algorithmic Workload Reduction

Reduce how much work is done when product semantics allow it.

Levers:

- Sample FPS/cadence.
- Sparse keyframes + interpolation.
- Precheck skip.
- Composite-only or fisheye-only outputs.
- Less undistort/fanout.

Risks:

- Product-visible behavior changes.
- Accuracy changes hidden by aggregate metrics.

Required gates:

- GT/product metric.
- Per-episode worst cases.
- Explicit signoff when quality shifts.

## 8. Rejected Lever Discipline

Record rejected ideas with numbers.

Examples:

- Faster quantized backbone but no e2e gain.
- Batch size win disappears after pipelining.
- Batched detector worsens contention.
- Lower FPS is faster but loses accuracy.
- Model cache saves load time but OOMs under concurrency.

Rejected levers are part of the result.

