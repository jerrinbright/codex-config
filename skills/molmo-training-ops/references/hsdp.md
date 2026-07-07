# HSDP Checklist

Use the repo presets first:

```bash
python runs/train_labeler_blurpad_hsdp_2x8h200.py --dry-run
python runs/train_corrector_original_blurpad_hsdp_2x8h200.py --dry-run
python runs/run_preset.py train.labeler_blurpad_hsdp_2x8h200 --dry-run
```

The preset source of truth is `runs/registry.py`; thin wrapper scripts should
delegate to registry names.

Expected healthy 2x8 H200 shape:

- `MOLMO_HSDP_NNODES=2`
- `MOLMO_HSDP_GPUS_PER_NODE=8`
- `MOLMO_HSDP_GPU_TYPE=H200`
- `MOLMO_HSDP_RDMA=1`
- `MOLMO_TRAIN_MAX_FRAMES=96`
- `MOLMO_TRAIN_SEQ_LEN=12288`
- `MOLMO_TRAIN_GLOBAL_BATCH_SIZE=64`
- `MOLMO_TRAIN_DEVICE_BATCH_SIZE=2`
- `MOLMO_TRAIN_CPU_THREAD_COUNT=1`
- compile off for model, loss, LLM, and ViT

Expected warm throughput:

- `>=2000` tokens/sec/device
- `>=0.04` batches/sec/device

Stop and diagnose if the run settles near `0.025` batches/sec/device.

Checkpoint expectations:

- local checkpoint root under `/tmp/molmo_hsdp_checkpoints/...`
- per-node exports under `<run_root>/local_checkpoint_exports/node*`
- merged checkpoints under `<run_root>/merged_checkpoints`
- merge wait timeout at least `10800` seconds for long HSDP runs
