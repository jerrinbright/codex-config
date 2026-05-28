---
name: ai-research-orchestrator
description: "Coordinate end-to-end AI research and engineering work from question or idea to experiments, evaluation, synthesis, and writeup. Use when the user wants to explore a model/dataset idea, compare approaches, design experiments, run multi-stage AI research, or turn scattered runs into a clear research plan."
---

# AI Research Orchestrator

## Purpose

Manage the full research loop: clarify the question, form hypotheses, route to specialist skills, run controlled experiments, preserve evidence, and synthesize the next move.

This is broader than `optimization-orchestrator`. Use `optimization-orchestrator` when the main goal is speed/cost. Use this skill when the goal is model quality, research direction, dataset strategy, training/eval design, or experiment synthesis.

## Routing

- Finetuning/LoRA/PEFT/SFT design: `finetuning-orchestrator`.
- DPO/RLHF/GRPO/SimPO/auditor preference learning: `posttraining-orchestrator`.
- Eval design, audit comparison, regression tables, model ranking: `model-evaluation`.
- Prompt/JSON/parser/tiny LLM structured extraction: `prompt-structured-output`.
- Literature review, research lookup, hypothesis generation, paper critique: `research-literature-synthesis`.
- Run lineage, experiment tracking, W&B/MLflow/TensorBoard: `mlops-experiment-tracking`.
- Speed/cost bottlenecks: `optimization-orchestrator`.
- Training ETA/curves: `training-progress`.
- Video/result inspection: `html-video-viewer`.
- Mongo/campaign/episode lookup: `mongo-episode-query-discovery`.
- Research artifact handoff: `context-handoff`.

Read `references/research-loop.md` when the task is multi-day, ambiguous, or needs experiment tracking across several branches/runs.

## Workflow

1. **Frame the question**
   - What is the hypothesis?
   - What dataset/model/checkpoint is in scope?
   - What metric or human judgment decides success?
   - What cost/time constraints exist?

2. **Map current evidence**
   - Existing runs, checkpoints, configs, datasets, eval HTML, logs, campaign ids, and known failure modes.
   - Separate measured facts from assumptions.
   - If the question depends on outside research or fast-moving methods, route to `research-literature-synthesis` before designing experiments.

3. **Design a small experiment set**
   - Prefer 2-4 experiments with clear deltas.
   - Include baseline, target metric, expected risk, and rollback/stop condition.
   - Hold out test data before training/prep.

4. **Route specialists**
   - Load only the specific specialist skill needed for the next step.
   - Use agents only when the user explicitly asks for parallel/delegated agent work.

5. **Run, evaluate, synthesize**
   - Save commands, paths, commit ids, run ids, and result summaries.
   - Compare against baseline.
   - Decide keep/discard/iterate.

6. **Report**
   - Give concise status, key evidence, recommendation, and next action.

## Output Shape

```md
**Research Status**
- Question:
- Evidence:
- Experiments:
- Current best:
- Risks:
- Next action:
```
