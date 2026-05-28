# PEFT And Fine-Tuning Frameworks

## Routing

- **PEFT library**: direct control in existing training code; best for custom repos.
- **Axolotl**: config-driven LLM fine-tuning with many recipes.
- **LLaMA-Factory**: broad UI/config-oriented finetuning and alignment workflows.
- **Unsloth**: speed/memory-efficient LoRA/QLoRA for supported LLMs.
- **Custom training script**: best when repo has special multimodal loaders, projectors, crops, or checkpoints.

## Method Selection

| Need | Method |
| --- | --- |
| cheap adaptation | LoRA |
| memory-limited finetune | QLoRA |
| broad behavior change | full fine-tune |
| visual embedding mismatch | bridge/projector finetune |
| model must learn from corrections/preferences | post-training skill |

## Config Metadata

Every run should record:

```text
base_checkpoint
resume_checkpoint
dataset_manifest
train_count
validation_count
test_exclusion
trainable_modules
lr_groups
batch_size
grad_accum
max_steps
save_interval
eval_interval
git_commit
```

