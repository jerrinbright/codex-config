# Quantization, Distillation, And Model-Changing Optimizations

Use this reference only after systems telemetry shows model memory/compute is the limiting factor or when the user explicitly wants a smaller/faster model.

## Decision Guide

- **Mixed precision**: first-line speed/memory option when model supports BF16/FP16 safely.
- **Flash Attention**: useful for transformer attention bottlenecks with supported shapes/hardware.
- **bitsandbytes 8-bit/4-bit**: low-friction HF memory reduction, mostly inference or adapter fine-tuning.
- **AWQ/GPTQ/HQQ**: post-training quantization for serving; requires accuracy eval.
- **Pruning**: use when structured speedup is possible in the target runtime, not just sparsity on paper.
- **Distillation**: use when a small model must imitate a larger model or specialized pipeline.
- **Speculative decoding**: text-generation serving only; not useful for OWLv2-style vision detection.

## Distillation For Small Extractors

For Qwen-style noun extraction or verifier submodules:

1. Build high-quality teacher labels from Codex/manual/rule outputs.
2. Deduplicate by normalized input string.
3. Train/evaluate on strict JSON validity, copy-only behavior, and object overlap.
4. Cache outputs in production.

## Validation

Every model-changing optimization needs:

```text
baseline_accuracy
optimized_accuracy
latency_delta
memory_delta
cost_delta
failure_examples
rollback_flag_or_config
```

Do not accept speedups that silently change labels/crops/eval semantics.

