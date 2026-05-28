# Serving And Batching

Use this reference for Hugging Face inference, Qwen noun extraction, OWLv2/open-vocab detection, VLM inference, and text-generation serving decisions.

## Universal Inference Wins

- Load model once per nonempty worker.
- Put empty-input checks before model load.
- Use `model.eval()` and `torch.inference_mode()`.
- Batch processor/tokenizer calls and forward passes.
- Keep images/prompts grouped so repeated preprocessing is avoided.
- Cache deterministic text extraction by normalized input string.
- Persist model cache (`HF_HOME`, Modal Volume, image layer) so downloads do not repeat.

## Batch Size Sweep

Run a small sweep:

```text
batch_size: 1, 4, 8, 16, 32
metrics: wall_ms, forward_ms, processor_ms, max_mem, outputs, accuracy/equivalence
```

Stop when:

- memory errors appear,
- per-item time stops improving,
- output quality changes,
- queue/cold-start overhead dominates.

## Prompt And Candidate Caching

For object verification:

- Qwen/tiny LLM should run on unique normalized top-k candidate strings.
- Cache output permanently.
- OWLv2 should receive filtered noun prompts, not full action labels.
- Track prompt count separately from frame count.

## Serving Stack Routing

- **Plain Transformers**: best for scripts, batch evals, vision models, and simple offline inference.
- **vLLM**: use for high-throughput text generation with many concurrent prompts.
- **SGLang**: use for structured generation, repeated prompt prefixes, agentic generation, or constrained outputs.
- **TensorRT-LLM**: use when production LLM latency/throughput is the priority and engine-building cost is worth it.
- **llama.cpp/GGUF**: use for CPU/Apple Silicon/local small-model serving.

Do not force vLLM/SGLang/TensorRT onto OWLv2-style vision detection unless the model/runtime supports it naturally.

## Quantization During Inference

Use quantization only after a baseline:

- `bitsandbytes`: easiest HF path for 8-bit/4-bit LLM-ish models.
- `AWQ/GPTQ/HQQ`: useful when memory and serving cost dominate.
- `GGUF`: useful for llama.cpp/local CPU/Metal.

Always run accuracy/equivalence checks after quantization.

## Metrics

Minimum useful inference telemetry:

```text
model_load_ms
tokenizer_or_processor_ms
image_open_decode_ms
forward_ms
postprocess_ms
batch_size
num_prompts
num_images
num_outputs
gpu_type
max_memory
accuracy/equivalence
```

