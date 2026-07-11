# Paul Optimizer Wireframe

This is the core algorithmic shape of `paul-optimizer`: build the judge first, then fan out builders, then let only the judge certify winners.

```text
                         ┌─────────────────────────┐
                         │     User Goal / Repo     │
                         │ "make this faster"       │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │  Lead Optimizer Agent    │
                         │  - maps service          │
                         │  - picks episodes        │
                         │  - defines baseline      │
                         │  - coordinates swarm     │
                         └────────────┬────────────┘
                                      │
                    FIRST AND MOST IMPORTANT STEP
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Verifier Sub-Agent                           │
│                                                                     │
│ Builds the scoring harness before optimization starts:              │
│ - correctness / parity gate                                         │
│ - quality metric gate                                               │
│ - throughput benchmark                                              │
│ - same-hardware baseline                                            │
│ - artifact comparison                                               │
│ - failure / crash / determinism checks                              │
│                                                                     │
│ Output: verifier command + baseline report + pass/fail thresholds   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ verifier becomes the reward function
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Parallel Optimizer Sub-Agents                    │
│                                                                     │
│  ┌────────────────────┐  ┌────────────────────┐  ┌───────────────┐ │
│  │ Concurrency Agent  │  │ I/O Pipeline Agent │  │ GPU Agent     │ │
│  │ - worker lanes     │  │ - NVDEC/NVENC      │  │ - TRT         │ │
│  │ - MPS              │  │ - no disk frames   │  │ - fp16        │ │
│  │ - CPU/VRAM caps    │  │ - prefetch queues  │  │ - compile     │ │
│  └────────────────────┘  └────────────────────┘  └───────────────┘ │
│                                                                     │
│  ┌────────────────────┐  ┌────────────────────┐  ┌───────────────┐ │
│  │ Resident Agent     │  │ Algorithm Agent    │  │ Native Agent  │ │
│  │ - warm models      │  │ - sample FPS       │  │ - C++ hotpath │ │
│  │ - process pools    │  │ - output modes     │  │ - CUDA kernel │ │
│  │ - cache policy     │  │ - sparse+interp    │  │ - pybind      │ │
│  └────────────────────┘  └────────────────────┘  └───────────────┘ │
│                                                                     │
│ Each agent proposes patches/experiments from Paul-style tricks.      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Experiment Runner                           │
│                                                                     │
│ For every candidate:                                                │
│ 1. apply patch / config                                             │
│ 2. run benchmark                                                    │
│ 3. run verifier                                                     │
│ 4. collect logs/artifacts                                           │
│ 5. record hardware/env/git SHA                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Verifier Gate                               │
│                                                                     │
│ HARD FAIL if:                                                       │
│ - correctness broken                                                │
│ - quality exceeds threshold                                         │
│ - determinism breaks unexpectedly                                   │
│ - crash/failure rate worsens                                        │
│ - rollback path missing                                             │
│                                                                     │
│ SCORE only after passing gates:                                     │
│ - ep/hr, fps, latency                                               │
│ - GPU-hours saved                                                   │
│ - VRAM / CPU / disk                                                 │
│ - operational risk                                                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Winner Selection                            │
│                                                                     │
│ - keep best safe candidate                                          │
│ - combine compatible winners                                        │
│ - reject tempting unsafe levers                                     │
│ - request product signoff for quality tradeoffs                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Final Patch / PR                            │
│                                                                     │
│ Must include:                                                       │
│ - gated implementation / env flag                                   │
│ - fail-loud behavior                                                │
│ - rollback switch                                                   │
│ - verifier evidence                                                 │
│ - benchmark table                                                   │
│ - rejected levers table                                             │
│ - rollout recommendation                                            │
└─────────────────────────────────────────────────────────────────────┘
```

## Acceptance Principle

```text
The lead optimizer may coordinate.
The optimizer sub-agents may propose.
Only the verifier may certify.
```

## Why This Shape Matters

This skill is not a generic profiler. It is an optimization search system where verification is deliberately made cheaper than invention. Once the verifier is strong, many specialized agents can safely explore bold search spaces: C++ rewrites, TensorRT, MPS, fp16, resident pools, output-mode changes, and concurrency models.

The system should feel aggressive in search and conservative in acceptance.

