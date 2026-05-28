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

- `code-review`: review code changes and write findings to `code_review.md`
- `code-review-orchestration`: coordinate review and response loops
- `code-review-response`: verify and address review feedback
- `context-handoff`: create concise handoff/status files for Codex sessions
- `data-pipeline-speed-optimizer`: optimize ML data prep, video/frame sampling, WES/crop prep, manifests, and Mongo/R2/file I/O
- `html-video-viewer`: create static HTML video/result viewers, serve them with byte-range support, and provide pasteable file/tunnel links
- `modal-speed-optimizer`: tune Modal GPU jobs, fanout, shard sizing, cold starts, volume I/O, and detached workload telemetry
- `modal-spend`: summarize Modal spend by environment and app
- `mongo-episode-query-discovery`: discover Mongo episode queries from project metadata, upstream-written episode fields, and requested output file keys
- `neural-inference-optimizer`: optimize HF/Qwen/OWLv2/VLM inference with batching, caching, model-load, prompt, and heuristic checks
- `neural-training-optimizer`: optimize neural training throughput, dataloaders, distributed execution, checkpointing, and convergence risk
- `optimization-orchestrator`: coordinate profiling, specialist speed skills, controlled experiments, agents when explicitly requested, benchmarking, and cost/accuracy reporting
- `paper-to-beamer`: turn LaTeX research papers into 10-minute conference Beamer decks with speaker notes
- `session-recovery`: recover prior Codex sessions from repo/task/job context hints and return resume commands plus evidence
- `split-stereo-hands-videos`: split stereo-hands `recording_primary.mp4` and `recording_secondary.mp4` into six corrected camera videos for `run_multi_camera_unified_v3.py`
- `training-progress`: analyze ML training logs and progress
