---
name: modal-guidelines
description: Modal rules for environment, GPU, volumes, and deployment.
---

# Modal Rules

## Environment

- Always use `jerrin`
- Never use `main`
- Verify before running:

modal config show | grep environment

## GPU

- Never assume GPU
- Always ask before launching
- No spot/preemptible

## Volumes

- Use jb_ws
- Never create unless asked

## Safety

Ask before:
- launching jobs
- changing env
- copying data
- deleting data
