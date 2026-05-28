# Optimization Skill Map

This local skill suite distills speed-optimization patterns from:

- davila7 claude-code-templates skills:
  - `development/performance-profiling`
  - `development/performance`
  - `development/senior-computer-vision`
  - `development/senior-ml-engineer`
  - `development/senior-data-engineer`
  - `development/async-python-patterns`
  - `ai-research/infrastructure-modal`
  - `ai-research/prompt-caching`
  - `ai-research/inference-serving-*`
  - `ai-research/data-processing-ray-data`
- K-Dense scientific-agent-skills:
  - `skills/modal`
  - `skills/optimize-for-gpu`
  - `skills/transformers`
  - `skills/dask`
  - `skills/polars`
  - `skills/zarr-python`
- Orchestra Research AI-Research-SKILLs:
  - `0-autoresearch-skill` for inner-loop experiments and outer-loop synthesis
  - `05-data-processing/ray-data`
  - `08-distributed-training/accelerate`, `deepspeed`, `pytorch-fsdp2`, `ray-train`
  - `09-infrastructure/modal`, `skypilot`, `lambda-labs`
  - `10-optimization/ml-training-recipes`, `flash-attention`, `bitsandbytes`, `awq`, `gptq`, `hqq`, `gguf`
  - `12-inference-serving/vllm`, `tensorrt-llm`, `sglang`, `llama-cpp`
  - `13-mlops/tensorboard`, `mlflow`, `weights-and-biases`
  - `17-observability/phoenix`, `langsmith`
  - `18-multimodal/clip`, `llava`, `segment-anything`
  - `19-emerging-techniques/knowledge-distillation`, `model-pruning`, `speculative-decoding`, `long-context`

Local routing:

| Problem | Local Skill |
| --- | --- |
| Modal fanout, detached jobs, GPU type/count, volume I/O, cold starts | `modal-speed-optimizer` |
| HF/Qwen/OWLv2 inference, model load, batch size, processor/tokenizer overhead | `neural-inference-optimizer` |
| Training throughput, dataloader stalls, checkpointing, distributed training | `neural-training-optimizer` |
| Frame sampling, video decode, crop prep, R2/Mongo/manifest I/O | `data-pipeline-speed-optimizer` |
| Active run ETA and curve health | `training-progress` |
| Eval/result review with videos | `html-video-viewer` |
| Episode/campaign/WES lookup | `mongo-episode-query-discovery` |

Use the upstream repos as inspiration, not as runtime dependencies.

Useful upstream ideas not yet represented as standalone local skills:

- Full LLM serving stacks (`vLLM`, `TensorRT-LLM`, `SGLang`) matter when the workload is text generation serving; for OWLv2/HF vision inference, borrow batching/model-load patterns only.
- Quantization skills (`bitsandbytes`, `AWQ`, `GPTQ`, `HQQ`, `GGUF`) matter when model memory or serving cost dominates; avoid them when accuracy comparability is the priority.
- Distillation/pruning/speculative decoding matter for productizing a smaller verifier model; they are second-pass work after systems telemetry.
- Observability tools (`Phoenix`, `W&B`, `TensorBoard`, `MLflow`) are useful when repeated experiments need durable comparison across many runs.
