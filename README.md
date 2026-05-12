# codex-config

Personal Codex CLI configuration.

This repo stores:
- Global rules (`AGENTS.md`)
- Reusable skills (`skills/*/SKILL.md`)

---

## Structure

codex-config/
├── AGENTS.md
├── README.md
└── skills/
    ├── code-review/
    ├── code-review-response/
    ├── infra-reference/
    ├── modal-guidelines/
    └── split-stereo-hands-videos/

---

## New Machine Setup

Clone repo:

git clone git@github.com:jerrinbright/codex-config.git ~/jb_ws/codex-config

Create folders:

mkdir -p ~/.codex
mkdir -p ~/.agents

Create symlinks:

ln -sf ~/jb_ws/codex-config/AGENTS.md ~/.codex/AGENTS.md
ln -sfn ~/jb_ws/codex-config/skills ~/.agents/skills

---

## Verify

ls -l ~/.codex/AGENTS.md
ls -l ~/.agents/skills
readlink -f ~/.codex/AGENTS.md
readlink -f ~/.agents/skills

Expected:

~/.codex/AGENTS.md -> ~/jb_ws/codex-config/AGENTS.md
~/.agents/skills -> ~/jb_ws/codex-config/skills

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

readlink -f ~/.codex/AGENTS.md
readlink -f ~/.agents/skills

Check skills:

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
- `modal-spend`: summarize Modal spend by environment and app
- `split-stereo-hands-videos`: split stereo-hands `recording_primary.mp4` and `recording_secondary.mp4` into six corrected camera videos for `run_multi_camera_unified_v3.py`
- `training-progress`: analyze ML training logs and progress
