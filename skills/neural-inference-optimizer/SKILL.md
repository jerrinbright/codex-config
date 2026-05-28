---
name: neural-inference-optimizer
description: "Optimize neural network inference pipelines, especially Hugging Face, Qwen, OWLv2/open-vocabulary detection, vision-language models, processors/tokenizers, batching, model loading, prompt/object caching, top-k candidate extraction, and accuracy-preserving heuristics."
---

# Neural Inference Optimizer

## Purpose

Speed up inference while preserving output quality and evaluation comparability.

Read `references/serving-and-batching.md` for deeper batching/model-residency/serving-stack patterns.

## Workflow

1. **Establish baseline**
   - Model/checkpoint, device, dtype, batch size, input count, prompt/candidate count, image/frame count, wall time, accuracy/proxy metric.
   - Record the baseline as a gate: target speedup, maximum memory, maximum cost, and allowed accuracy/equivalence delta.

2. **Break down inference**
   - Model/tokenizer/processor load.
   - Candidate/prompt extraction.
   - Image open/decode/preprocess.
   - Processor/tokenizer call.
   - Forward pass.
   - Postprocess/NMS/heuristics.
   - Merge/scoring.

3. **Apply low-risk wins first**
   - Early-return when input rows/prompts are empty before loading model.
   - Cache prompt/noun extraction by normalized label/top-k string.
   - Batch processor and forward calls.
   - Keep model loaded per nonempty worker.
   - Avoid repeated image opens when multiple prompts use the same image.
   - Move deterministic parsing outside GPU workers.
   - Use `torch.inference_mode()`, eval mode, pinned expected dtype/device.
   - Reuse allocated tensors/buffers where practical and avoid repeated CPU/GPU transfers inside tight loops.
   - Watch Python object churn in postprocessing; prefer vectorized tensor/array operations when the profiler points there.

4. **Tune batch and shards together**
   - Larger batch reduces overhead but can increase memory and latency.
   - Fewer shards can be faster for small runs because model load dominates.
   - More shards help only when each shard has enough frames/prompts to amortize startup.
   - Serving stacks like vLLM, TensorRT-LLM, and SGLang are relevant for text-generation services; for HF vision/open-vocab detectors, borrow their ideas around continuous batching, cache reuse, and model residency rather than forcing a serving stack.

5. **Guard accuracy**
   - If changing prompt extraction, top-k handling, crop policy, resize, thresholds, or heuristics, rerun the same eval slice.
   - Report exact, similar/synonym, top-1/top-3, agreement, and regression examples when available.
   - Quantization, pruning, and distillation need their own accuracy table before being accepted.
   - Reject or gate changes that improve latency but cause >5% accuracy/equivalence regression unless the user explicitly accepts that tradeoff.

6. **Detect regressions**
   - Compare against the saved baseline for total wall time, model load, processor time, forward time, postprocess time, memory, and output quality.
   - Treat a stage-level slowdown as useful evidence even when total wall time is noisy; it often exposes cold-start, batching, or I/O effects.
   - If the candidate is close to the baseline, rerun the same slice and compare medians before drawing a conclusion.

## Object-Verifier Specific Guidance

- Use Molmo lower-confidence top-k object alternatives as the candidate vocabulary source, not arbitrary full labels.
- Run Qwen/tiny LLM only on unique normalized candidate strings; cache permanently.
- Feed OWLv2 noun prompts only, not full action labels.
- Keep top-1 and top-3 verifier candidates so gating policies can trade coverage for precision.
- Treat table/floor/pile/stack/bag/box as possible secondary/support objects unless the task makes them the primary object.
- Heuristics should consider both hands because each hand may interact with a different object.

## Validation Metrics

```text
segments
frames
prompts
model_load_ms
processor_ms
forward_ms
postprocess_ms
wall_ms
batch_size
nonempty_shards
molmo_top1
verifier_top1
verifier_top3
agreement_rate
coverage
false_override_rate
salvage_rate
```

## Benchmark Matrix

Use this compact shape when reporting candidate configs:

```md
| Config | Batch | Shards | GPU | Wall | Load | Preprocess | Forward | Postprocess | Accuracy/equiv | Gate |
|--------|------:|-------:|-----|-----:|-----:|-----------:|--------:|------------:|---------------:|------|
```
