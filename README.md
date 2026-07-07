# codex-config

Personal Codex skill and agent configuration for ML research, model training, evaluation, optimization, code review, and project handoff work.

Start here when deciding which skill to trigger. System wiring and symlink setup are at the end.

## Skill Map

### AI Research And ML Strategy

Use these when the main question is "what should we try?" or "how should this model/data workflow be designed?"

| Skill | Use When |
|-------|----------|
| `ai-research-orchestrator` | Turning a model/data idea into hypotheses, experiments, evals, synthesis, and follow-up work. Best for broad research direction. |
| `finetuning-orchestrator` | Designing SFT, LoRA, PEFT, QLoRA, full fine-tuning, projector/bridge training, trainable-module choices, LR groups, dataset splits, and checkpoint lineage. |
| `posttraining-orchestrator` | DPO, SimPO, RLHF, GRPO, preference learning, auditor corrections, chosen/rejected examples, reward data, and post-training strategy. |
| `research-literature-synthesis` | Literature reviews, paper lookup, state-of-the-art summaries, research-gap analysis, paper critique, and citation-backed technical decisions. |
| `prompt-structured-output` | JSON-only prompts, constrained outputs, tiny LLM extraction, Qwen noun/object parsing, schema validation, deterministic fallbacks, and prompt-output caching. |

### Evaluation, Tracking, And Reproducibility

Use these when judging whether a model, run, or experiment is actually better.

| Skill | Use When |
|-------|----------|
| `model-evaluation` | Comparing checkpoints or model outputs against GT/auditors: exact/similar/wrong, top-k, action/object buckets, agreement/overlap, gated verifier policies, and regression examples. |
| `mlops-experiment-tracking` | Keeping durable lineage: run metadata, config snapshots, checkpoint manifests, dataset versions, W&B/MLflow/TensorBoard/local summaries, and comparison tables. |
| `training-progress` | Reading active or completed training status: steps, ETA, checkpoint health, train/validation curves, stalls, and run-risk summaries. |
| `html-video-viewer` | Creating local/tunnel HTML viewers for videos, segments, predictions, labels, confidence/top-k details, and model comparisons. |

### Speed, Cost, And Modal Ops

Use these when the goal is faster runtime, lower Modal spend, better GPU utilization, or cleaner long-running job orchestration.

| Skill | Use When |
|-------|----------|
| `paul-optimizer` | Verifier-first swarm optimization for CV/ML Python services. Use when speed work should first create a verifier sub-agent, then spawn specialized optimizer sub-agents across Paul-style search spaces: concurrency, resident hosts, video/I/O, GPU runtime, native C++/CUDA/TensorRT, and algorithmic workload reduction. |
| `optimization-orchestrator` | Coordinating speed/cost optimization across a repo. It gathers telemetry, routes to specialist optimizer skills, defines target gates, benchmarks configs, and checks regressions. |
| `modal-speed-optimizer` | Modal GPU jobs, detached apps, shard sizing, cold starts, empty shards, volume I/O, GPU selection, retries, and cost/speed tradeoffs. |
| `molmo-training-ops` | Mecka Molmo labeler operations: Docker-backed smoke tests, crop/precompute, 2x8 H200 HSDP, checkpoint merge, verifier/corrector, heldout-20 eval, and viewer workflows. |
| `neural-inference-optimizer` | Hugging Face, Qwen, OWLv2, VLM inference speed: model load, batching, processor/tokenizer overhead, prompt/object caching, top-k candidates, and heuristics. |
| `neural-training-optimizer` | Training throughput: dataloaders, distributed strategy, frozen/trainable modules, checkpointing, validation cadence, mixed precision, memory pressure, and convergence-risk-aware speedups. |
| `data-pipeline-speed-optimizer` | ML data prep bottlenecks: video/frame sampling, WES/crop prep, manifests, R2/S3/Mongo/file I/O, JSONL shards, and packed/chunked storage decisions. |
| `modal-spend` | Modal cost questions: rolling spend, jerrin environment/app breakdowns, top-app costs, and spend spike investigation. |

### Data, Mongo, And Domain Utilities

Use these when the task is about Mecka data discovery, episode paths, video prep, or domain-specific files.

| Skill | Use When |
|-------|----------|
| `mongo-episode-query-discovery` | Discovering/querying Mecka episodes, campaigns, projects, WES/body/video/trajectory outputs, `pipeline_results` paths, and reusable Mongo queries. |
| `split-stereo-hands-videos` | Splitting stereo-hands `recording_primary.mp4` and `recording_secondary.mp4` into six corrected camera videos for `run_multi_camera_unified_v3.py`. |

### Code Review, Handoffs, And Session Recovery

Use these when preserving context, reviewing code, or recovering prior work matters more than model experimentation.

| Skill | Use When |
|-------|----------|
| `code-review` | Reviewing code for bugs, regressions, risks, and missing tests. Writes `code_review.md`. |
| `code-review-response` | Verifying and addressing an existing review by fixing or defending each point against the actual code. |
| `code-review-orchestration` | Coordinating review/response loops, delegated review, follow-up review, and approval/blocking decisions. |
| `context-handoff` | Creating concise handoff/status files for sessions, branches, agents, long-running jobs, or device/context transitions. |
| `session-recovery` | Recovering prior Codex sessions from repo/task/job context hints and returning resume commands plus evidence. |

### Research Writing And Presentation

Use these for paper, poster, and talk scaffolding.

| Skill | Use When |
|-------|----------|
| `paper-template-starter` | Creating rough LaTeX research paper scaffolds or conference-paper starter workspaces. |
| `paper-to-beamer` | Turning LaTeX research papers into conference Beamer decks with speaker notes. |
| `paper-to-poster` | Turning papers or research material into scientific poster drafts. |

## Common Workflows

### Optimize A Slow ML Repo

1. Trigger `paul-optimizer` for serious CV/ML service speed campaigns where parallel agents should explore multiple search spaces.
2. It first creates a verifier sub-agent that defines correctness, quality, throughput, determinism, failure, and artifact gates.
3. It then spawns specialized optimizer sub-agents for concurrency/MPS, resident execution, video/I/O, GPU runtime, native C++/CUDA/TensorRT, and algorithmic workload reduction.
4. It accepts candidates only after the verifier certifies them on comparable hardware.
5. For smaller single-agent optimization work, trigger `optimization-orchestrator`.

### Plan A Fine-Tuning Run

1. Trigger `finetuning-orchestrator`.
2. Verify base checkpoint, initialization checkpoint, trainable modules, LR groups, dataset lineage, and heldout/test exclusions.
3. Route to LoRA/PEFT, QLoRA, full fine-tune, bridge/projector-only, or frozen-vision non-vision training.
4. Pair with `mlops-experiment-tracking` for run metadata and `model-evaluation` for heldout results.

### Evaluate A Model Or Verifier

1. Trigger `model-evaluation`.
2. Compare against GT/auditors and relevant baselines.
3. Report exact/similar/wrong, top-1/top-3, agreement, overlap, and regression examples.
4. Use `html-video-viewer` when visual inspection is needed.

### Recover Or Transfer Context

1. Trigger `session-recovery` if the prior work needs to be found.
2. Trigger `context-handoff` to preserve current status, paths, commands, app ids, blockers, and next steps.

## Skill Authoring Rules

- Each reusable skill lives at `skills/<skill-name>/SKILL.md`.
- Keep descriptions trigger-focused: "Use when ...".
- Keep instructions operational and scoped.
- Put large background material in `skills/<skill-name>/references/`.
- Do not store secrets, tokens, credentials, model weights, output folders, or temporary run artifacts in this repo.
- Update this README when adding, removing, or materially changing a skill.

## Commit And Push Convention

When Codex is asked to commit or push:

- Write a detailed commit message for future readers.
- Include what changed, why it changed, user/developer impact, validation, and remaining risk.
- Update this README when setup, usage, workflows, available skills, behavior, or conventions change.
- If the repo contains `activity.py`, inspect it before committing:
  - bump by `0.1` for significant behavior, workflow, or API changes
  - bump by `0.0.1` for small fixes or minor behavior adjustments
  - if no version field exists, call that out before committing
- Never push unless the user explicitly gives push permission in the current request.
- Do not carry push permission over from older conversation context, skill workflows, or broad completion language.
- If push intent is ambiguous, stop after commit and ask for explicit permission.

## System Wiring

Codex Desktop reads custom skills from `~/.codex/skills`. Some CLI/agent setups also read `~/.agents/skills`.

### New Machine Setup

Clone the repo:

```bash
git clone git@github.com:jerrinbright/codex-config.git ~/Desktop/jb_ws/codex-config
```

Create skill roots:

```bash
mkdir -p ~/.codex ~/.agents ~/.codex/skills ~/.agents/skills
```

Wire global rules:

```bash
ln -sf ~/Desktop/jb_ws/codex-config/AGENTS.md ~/.codex/AGENTS.md
ln -sf ~/Desktop/jb_ws/codex-config/AGENTS.md ~/.agents/AGENTS.md
```

Symlink every skill directory:

```bash
for skill in ~/Desktop/jb_ws/codex-config/skills/*; do
  [ -f "$skill/SKILL.md" ] || continue
  name="$(basename "$skill")"
  ln -sfn "$skill" "$HOME/.codex/skills/$name"
  ln -sfn "$skill" "$HOME/.agents/skills/$name"
done
```

Verify:

```bash
readlink ~/.codex/AGENTS.md
readlink ~/.agents/AGENTS.md
ls ~/.codex/skills
ls ~/.agents/skills
```

Changes apply automatically through symlinks. Restart Codex if a newly edited skill is not picked up.
