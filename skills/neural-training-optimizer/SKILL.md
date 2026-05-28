---
name: neural-training-optimizer
description: "Optimize neural network training speed and cost: dataloaders, distributed GPU throughput, checkpointing, frozen modules, mixed precision, gradient accumulation, logging overhead, validation cadence, resume behavior, and learning-rate strategy."
---

# Neural Training Optimizer

## Purpose

Improve training throughput and cost while protecting convergence and resume safety.

Read `references/distributed-training.md` when the issue involves multi-GPU strategy, FSDP/DeepSpeed/Accelerate/Ray Train, dataloader scaling, or GPU underutilization. Read `references/quantization-distillation.md` when the proposed optimization changes model size, precision, distillation, pruning, or adapter strategy.

## Workflow

1. **Read the training config/code**
   - Model init checkpoint, frozen/trainable modules, dataset, batch size, workers, precision, optimizer, LR schedule, max steps, checkpoint interval, validation interval.

2. **Measure throughput**
   - Step time recent vs average.
   - GPU utilization if available.
   - Dataloader wait/stall warnings.
   - Checkpoint/validation overhead.
   - Resume/checkpoint health.
   - Record an explicit performance gate: target step-time improvement, max cost, max memory, quality/convergence proxy, and acceptable regression threshold.

3. **Diagnose likely bottleneck**
   - GPU underutilized: dataloader, CPU decode, small batch, sync/logging, distributed imbalance.
   - GPU memory-bound: batch too large, activation checkpointing, sequence length/frame count.
   - I/O-bound: video/frame decode, remote storage, many small files, volume commit.
   - Restart-bound: checkpoint interval too sparse, non-resumable dataloader, 24h app cap.

4. **Safe optimization levers**
   - Increase dataloader workers only when CPU/I/O can sustain it.
   - Precompute expensive deterministic data transforms.
   - Tune batch size/grad accumulation for stable global batch.
   - Use mixed precision where model already supports it.
   - Save enough checkpoints for preemption/resume, but avoid excessive checkpoint I/O.
   - Reduce validation frequency only when it does not hide regressions.
   - Keep metadata/config in checkpoint folders.
   - Consider distributed frameworks only when local patterns fit: Accelerate for simple PyTorch multi-GPU, DeepSpeed/FSDP for memory pressure and large models, Ray Train when data/distributed orchestration is the bottleneck.
   - Check memory pressure before changing model strategy: activation checkpointing, batch sizing, host memory churn, pinned memory, and dataloader prefetch can matter more than model code.

5. **LR and trainable-module strategy**
   - When training newly initialized adapters/bridges plus an already-trained LLM/projector, use parameter groups.
   - Higher LR can be appropriate for new bridge/projection layers; lower LR for pretrained LLM/projector.
   - If vision encoder is frozen, verify crops/preprocessing match inference before blaming convergence.

6. **Model-changing optimizations**
   - Flash Attention, quantization, pruning, distillation, and speculative decoding can be valuable, but treat them as separate experiments with explicit quality checks.
   - For training speed, prefer dataloader/batch/distributed fixes before quantization-like changes unless memory is the blocker.

7. **Regression checks**
   - Compare candidate runs against the baseline for step time, examples/sec, GPU utilization, dataloader wait, checkpoint/validation overhead, memory, cost, and validation quality.
   - Treat >5% step-time or cost regression, weaker resume behavior, or unexplained validation degradation as a failed gate unless the user explicitly chooses that tradeoff.
   - Use the same data slice and checkpoint initialization for benchmark comparisons whenever possible.

## Report

Always separate:

- Throughput issue.
- Cost issue.
- Convergence/quality issue.
- Resume/checkpoint issue.

Do not recommend broad training changes without evidence from logs or a small controlled run.

## Benchmark Matrix

Use this shape for training optimization comparisons:

```md
| Config | GPUs | Batch/global | Workers | Step time | Examples/sec | Dataloader wait | Memory | Val metric | Cost est. | Gate |
|--------|-----:|-------------:|--------:|----------:|-------------:|----------------:|-------:|-----------:|----------:|------|
```
