# Paul Optimizer Swarm Architecture

## Wireframe

```text
                         User Goal / Repo
                       "make this faster"
                               |
                               v
                    Lead Paul Optimizer Agent
                 maps service, scope, baseline
                               |
                 first and most important step
                               |
                               v
                    Verifier Sub-Agent
        builds correctness, quality, throughput, determinism,
          crash, artifact, and same-hardware comparison gates
                               |
                verifier becomes the reward function
                               |
                               v
                   Parallel Optimizer Sub-Agents

   Concurrency      Resident Exec      Video/I/O        GPU Runtime
   lanes, MPS,      warm models,       NVDEC/NVENC,     TRT, compile,
   CPU/VRAM caps    process pools      compact JSON     fp16, kernels

   Algorithmic      Native Rewrite     Operability
   sampling,        C++/CUDA/PyBind    rollback,
   output modes     hot paths          fail-loud
                               |
                               v
                    Experiment Runner
          applies candidates, runs benchmark, runs verifier
                               |
                               v
                    Verifier Gate
          hard fail correctness/quality, then score speed
                               |
                               v
                    Winner Selection
        combine compatible winners, reject unsafe levers
                               |
                               v
                    Final Patch / PR Evidence
```

## Authority Model

- Lead agent coordinates and integrates.
- Verifier sub-agent defines pass/fail gates and checks candidates.
- Optimizer sub-agents are untrusted proposal generators.
- A candidate is accepted only after verifier certification.

## Why This Works

Many optimization tasks are hard to solve but easier to verify once a good verifier exists. The verifier turns speed work into a search problem: many agents can propose changes, but the reward signal is mechanical and repeatable.

## Failure Modes To Prevent

- Optimizers benchmark only their own micro-stage and ignore e2e wall time.
- Optimizers silently change output semantics.
- Multiple sub-agents edit the same files and clobber each other.
- A verifier compares stale artifacts or wrong commits.
- Same-hardware assumptions are violated.
- Long-running jobs lack durable logs.
- Rollback flags are missing for risky changes.

## Recommended Parallel Ownership

Keep write ownership disjoint:

```text
verifier-agent: verifier/, scripts/compare_*, benchmark report files
concurrency-agent: worker launch/env/config files
resident-agent: model load/cache/process-pool files
video-io-agent: decode, frame extraction, artifact serialization
gpu-runtime-agent: model runtime/export/precision files
native-agent: native/, pybind seams, Docker native build
```

The lead agent merges after individual candidates pass.

