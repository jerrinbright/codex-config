# Distributed Training

Use this reference when training is slow, GPUs are underutilized, memory is tight, or distributed strategy is unclear.

## Routing

- **PyTorch DDP**: default when the script is already mature and model fits per GPU.
- **Hugging Face Accelerate**: easiest upgrade path for custom PyTorch/HF scripts.
- **DeepSpeed ZeRO**: use when optimizer/state memory dominates or very large models need sharding.
- **PyTorch FSDP/FSDP2**: use for native PyTorch parameter sharding and large model training.
- **Ray Train**: use when distributed orchestration and data pipeline coordination are as important as training.
- **PyTorch Lightning**: useful if the repo already uses Lightning conventions.

## Throughput Diagnosis

Collect:

```text
step_time_ms
tokens_or_samples_per_sec
gpu_utilization
gpu_memory
dataloader_wait_ms
forward_ms
backward_ms
optimizer_ms
checkpoint_ms
validation_ms
global_batch
grad_accum
num_workers
```

Interpretation:

- Low GPU util + high dataloader wait: data pipeline bottleneck.
- High GPU memory + low batch: memory bottleneck.
- Slow checkpoint spikes: checkpoint I/O bottleneck.
- Rank imbalance: sharding or data skew.
- Frequent restarts: checkpoint/resume design bottleneck.

## Dataloader

- Avoid CPU video decode or expensive transforms during training if they are deterministic.
- Pin memory only when it helps host-to-GPU transfer.
- Tune workers empirically; more workers can worsen remote storage pressure.
- Make data order/resume semantics explicit.

## Checkpointing

- Save often enough to survive preemptions or platform runtime caps.
- Keep optimizer/scheduler/model state together unless intentionally doing inference-only checkpoint export.
- Write metadata: source checkpoint, dataset manifest, trainable modules, LR groups, max steps, save interval, git commit.

## Batch And LR

- If changing global batch, check whether LR schedule should scale.
- Prefer stable global batch via gradient accumulation when GPU memory varies.
- For new bridge/projector layers, parameter groups usually need higher LR than pretrained LLM layers.

