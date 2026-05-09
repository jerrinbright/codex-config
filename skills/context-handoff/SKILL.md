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
   - Capture all data locations needed to replicate the work, especially Modal volume paths, remote dataset paths, temp output directories, cache paths, artifact paths, and local staging paths.

3. Write the handoff:
   - Be concrete and chronological where it helps.
   - Separate verified facts from assumptions.
   - Call out unresolved issues and risks plainly.
   - Explain commands by purpose, not just raw syntax.
   - List file paths with one-line reasons each.
   - Clearly state where data was accessed from and where temporary/intermediate/final results were written.

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

## Data And Artifact Paths
- Modal volumes: exact `/vol/...` paths used and what each contains.
- Modal temp/output paths: exact remote temp/result directories and whether they are persistent.
- Local temp/output paths: exact repo-relative or absolute paths used for generated artifacts.
- Source data paths: datasets, episode ids, object keys, R2/S3 paths, Mongo fields, or other inputs accessed.
- Result artifacts: filenames/directories needed to reproduce, inspect, or compare the work.

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
- Use exact absolute paths for Modal, remote, mounted volume, temp, cache, dataset, and artifact locations when they are needed to reproduce the work.
- Do not include secrets, tokens, private credentials, or large pasted logs.
- Summarize long outputs; include only key lines needed for continuity.
- If verification was not run, say so directly.

## Replication Path Rules

- Treat data and artifact paths as first-class handoff content, not incidental details.
- For Modal work, always include:
  - environment name, such as `jerrin`
  - app/function/job name or run id when known
  - volume names and mounted paths
  - exact `/vol/...` paths read from or written to
  - local mirror/download paths if files were copied back
  - temp paths and whether they are disposable or required for follow-up
- If a path is unknown but important, add it under `Issues And Risks` as missing replication information.
