# codex-config

Personal Codex CLI configuration.

This repo stores:
- Global rules (`AGENTS.md`)
- Reusable skills (`skills/*/SKILL.md`)
- Compatibility skill shims for legacy `SKILLS.md` files

---

## Structure

codex-config/
├── AGENTS.md
├── README.md
└── skills/
    ├── code-review/
    ├── code-review-response/
    ├── html-video-viewer/
    ├── infra-reference/
    ├── modal-guidelines/
<<<<<<< HEAD
    ├── session-recovery/
=======
    ├── paper-to-beamer/
>>>>>>> e0549f2 (Add paper-to-beamer conference deck skill)
    └── split-stereo-hands-videos/

---

## New Machine Setup

Clone repo:

git clone git@github.com:jerrinbright/codex-config.git ~/Desktop/jb_ws/codex-config

Create folders:

mkdir -p ~/.codex
mkdir -p ~/.agents
mkdir -p ~/.codex/skills
mkdir -p ~/.agents/skills

Create symlinks:

ln -sf ~/Desktop/jb_ws/codex-config/AGENTS.md ~/.codex/AGENTS.md
ln -sf ~/Desktop/jb_ws/codex-config/AGENTS.md ~/.agents/AGENTS.md

For each skill directory that contains `SKILL.md`, symlink the whole directory into both skill roots:

ln -sfn ~/Desktop/jb_ws/codex-config/skills/training-progress ~/.codex/skills/training-progress
ln -sfn ~/Desktop/jb_ws/codex-config/skills/training-progress ~/.agents/skills/training-progress

For legacy skill directories that contain `SKILLS.md`, keep a directory shim and symlink it as `SKILL.md`:

mkdir -p ~/.codex/skills/modal-guidelines
ln -sf ~/Desktop/jb_ws/codex-config/skills/modal-guidelines/SKILLS.md ~/.codex/skills/modal-guidelines/SKILL.md

---

## Verify

ls -l ~/.codex/AGENTS.md
ls -l ~/.agents/AGENTS.md
ls -l ~/.codex/skills
ls -l ~/.agents/skills
readlink ~/.codex/AGENTS.md
readlink ~/.agents/AGENTS.md

Expected:

~/.codex/AGENTS.md -> ~/Desktop/jb_ws/codex-config/AGENTS.md
~/.agents/AGENTS.md -> ~/Desktop/jb_ws/codex-config/AGENTS.md

Codex Desktop reads custom skills from `~/.codex/skills`. Some CLI/agent setups also read `~/.agents/skills`, so this repo keeps both locations wired to the same checked-out skill files.

---

## Updating

Edit files in:

cd ~/jb_ws/codex-config

Changes apply automatically via symlinks.

If not, restart Codex CLI.

---

## Commit And Push Convention

When Codex is asked to commit or push:

- Write a detailed commit message for future git readers.
- Include what changed, why it changed, developer/user impact, validation, and remaining risk.
- Update the repo README whenever the change affects setup, usage, workflows, available skills, behavior, or conventions.
- If the target repo contains `activity.py`, inspect it before committing:
  - bump its version by `0.1` for significant behavior, workflow, or API changes
  - bump its version by `0.0.1` for small fixes or minor behavior adjustments
  - if no version field exists in `activity.py`, mention that explicitly before committing
- Never push unless the user explicitly asks.

---

## Add New Skill

mkdir -p skills/my-skill
nano skills/my-skill/SKILL.md

Template:

---
name: my-skill
description: clear trigger description
---

# My Skill

Instructions here.

---

## Secrets Policy

Never store secrets here.

Do NOT commit:
- .env
- API keys
- tokens
- credentials

Use environment variables instead.

---

## Project Secrets

Each project should have:

.env
.env.example

Add to .gitignore:

.env
.env.*

---

## Troubleshooting

Check symlinks:

readlink ~/.codex/AGENTS.md
readlink ~/.agents/AGENTS.md

Check skills:

ls ~/.codex/skills
ls ~/.agents/skills

If skill not triggering:
- fix description
- or invoke explicitly

---

## Available Skills

### AI Research And ML

- `ai-research-orchestrator`: use for broad model/data research loops: turn an idea into hypotheses, experiments, evals, synthesis, and follow-up. Trigger this when the goal is quality, strategy, or research direction rather than just speed.
- `finetuning-orchestrator`: use for SFT, LoRA, PEFT, QLoRA, full fine-tuning, projector/bridge training, trainable-module choices, LR groups, dataset splits, and checkpoint lineage.
- `posttraining-orchestrator`: use for DPO, SimPO, RLHF, GRPO, TRL/OpenRLHF/verl-style workflows, auditor corrections, chosen/rejected examples, reward data, and preference learning.
- `model-evaluation`: use for comparing checkpoints or model outputs against GT/auditors: exact/similar/wrong, top-k, action/object buckets, agreement/overlap, gated verifier policies, and regression examples.
- `prompt-structured-output`: use for JSON-only prompts, constrained outputs, tiny LLM extraction, Qwen noun/object parsing, schema validation, deterministic fallbacks, and prompt-output caching.
- `mlops-experiment-tracking`: use when runs need durable lineage: config snapshots, checkpoint manifests, dataset versions, W&B/MLflow/TensorBoard/local summaries, and comparison tables.

### Optimization And Training Ops

- `optimization-orchestrator`: use for speed/cost optimization across a repo. It gathers telemetry first, routes to specialist optimizer skills, plans controlled configurations, and benchmarks cost/accuracy impact.
- `modal-speed-optimizer`: use for Modal GPU jobs, detached apps, shard sizing, cold starts, empty shards, volume I/O, GPU selection, and cost/speed tradeoffs.
- `neural-inference-optimizer`: use for HF/Qwen/OWLv2/VLM inference speed: model load, batching, processor/tokenizer overhead, prompt/object caching, top-k candidates, and inference heuristics.
- `neural-training-optimizer`: use for training throughput: dataloaders, distributed strategy, frozen/trainable modules, checkpointing, validation cadence, mixed precision, and convergence-risk-aware speedups.
- `data-pipeline-speed-optimizer`: use for ML data prep bottlenecks: video/frame sampling, WES/crop prep, manifests, R2/S3/Mongo/file I/O, JSONL shards, and packed/chunked storage decisions.
- `training-progress`: use for active/completed training status: step/epoch progress, elapsed time, ETA, checkpoint health, train/validation curves, stalls, and run-risk summaries.
- `modal-spend`: use for Modal cost questions: rolling spend, jerrin environment/app breakdowns, and spend spike investigation.

### Data, Viewers, And Domain Utilities

- `mongo-episode-query-discovery`: use for Mecka Mongo episode discovery: campaigns, projects, WES/body/video/trajectory outputs, `pipeline_results` paths, and reusable episode queries.
- `html-video-viewer`: use to create local/tunnel HTML viewers for videos, segments, predictions, labels, confidence/top-k details, and model comparison artifacts.
- `split-stereo-hands-videos`: use to split stereo-hands `recording_primary.mp4` and `recording_secondary.mp4` into six corrected camera videos for `run_multi_camera_unified_v3.py`.

### Reviews, Handoffs, And Papers

- `code-review`: use for code review findings focused on bugs, regressions, risks, and missing tests; writes `code_review.md`.
- `code-review-orchestration`: use to coordinate review/response loops, delegated review, follow-up review, and approval/blocking decisions.
- `code-review-response`: use to verify and address an existing review by fixing or defending each point against the actual code.
- `context-handoff`: use to create concise handoff/status files for sessions, branches, agents, long-running jobs, or device/context transitions.
- `session-recovery`: use to recover prior Codex sessions from repo/task/job context hints and return resume commands plus evidence.
- `paper-template-starter`: use to create rough LaTeX research paper scaffolds or conference-paper starter workspaces.
- `paper-to-beamer`: use to turn LaTeX research papers into conference Beamer decks with speaker notes.
- `paper-to-poster`: use to turn papers or research material into scientific poster drafts.
