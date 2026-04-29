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
    └── modal-guidelines/

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

