---
name: context-handoff
description: "Create concise, high-signal Codex context handoff files for moving work between sessions, devices, branches, or agents. Use when the user asks to transfer context, summarize current work for another Codex instance, create named handoff/status/scope files, preserve findings/issues/commands/files touched, or prepare an orchestration handoff."
---

# Context Handoff

## Purpose

Write a handoff artifact that lets another Codex session continue without re-discovering the same context. Optimize for factual continuity: findings, issues, commands, files touched, decisions, blockers, and next steps.

## Workflow

1. Identify the handoff target:
   - `handoff_<context>_<date>.md` for general session transfer.
   - `scope.md` for orchestrator boundaries.
   - `status.md` for ongoing task state.
   - A user-provided path when specified.

2. Gather current state:
   - Run lightweight repo checks when useful: `git status --short`, `git diff --stat`, and focused `git diff -- <files>`.
   - Inspect relevant files already discussed or changed.
   - Include only commands actually run or explicitly recommended.

3. Write the handoff:
   - Be concrete and chronological where it helps.
   - Separate verified facts from assumptions.
   - Call out unresolved issues and risks plainly.
   - Explain commands by purpose, not just raw syntax.
   - List file paths with one-line reasons each.

4. If creating or updating a file, keep it repo-local unless the user specifies another location.

## Filename Convention

Default context handoff filenames must use:

```text
handoff_<context>_<date>.md
```

- `<context>`: short lowercase topic, using underscores when needed, such as `orch`, `review`, `ci_fix`, `modal_training`, or `yazi_setup`.
- `<date>`: local date in `DDMM` format unless the user asks for another format.
- Example: `handoff_orch_0805.md` for an orchestrator handoff created on May 8.
- If there may be multiple handoffs for the same context and date, append a short suffix, such as `handoff_orch_0805_scope.md`.

## Required Sections

Use these sections by default:

```md
# Codex Handoff

## Goal
What the user is trying to accomplish.

## Current State
What is true now, including installed tools, branch/worktree state, and important repo facts.

## Findings
Facts learned from reading code, docs, command output, or external sources.

## Issues And Risks
Known bugs, blockers, uncertain assumptions, safety constraints, or things not yet verified.

## Commands Run
- `<command>`: why it was run and the important result.

## Files Touched Or Reviewed
- `path/to/file`: changed/reviewed; why it matters.

## Decisions
Choices made and the reason for each.

## Next Steps
Concrete continuation steps in order.
```

## Scope Files For Orchestrators

When writing a scope file, add explicit boundaries:

```md
## In Scope
- Exact files, modules, commands, or behaviors the orchestrator may inspect or change.

## Out Of Scope
- CI/CD, deployment, infra, auth/security, file deletion, training/jobs, servers, large outputs, unrelated refactors, or third-party code unless explicitly allowed.

## Validation
- Focused checks the orchestrator may run.

## Safety
- Fail loudly on missing config/data.
- Do not hardcode local paths.
- Do not run long jobs, servers, training, deploys, or destructive commands without approval.
```

## Style Rules

- Keep the file concise but complete enough to resume.
- Prefer bullets over prose for scanability.
- Use absolute dates when relevant.
- Use repo-relative paths for files.
- Do not include secrets, tokens, private credentials, or large pasted logs.
- Summarize long outputs; include only key lines needed for continuity.
- If verification was not run, say so directly.
