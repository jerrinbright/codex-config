---
name: session-recovery
description: "Recover prior Codex sessions from partial context such as repo path, task topic, commands, app/job ids, dates, or files. Use when the user says a session/context was deleted or lost, asks to find/resume an old Codex session, or wants the session that ran a specific workflow, training job, Modal app, GitHub task, Mongo query, or artifact generation."
---

# Session Recovery

## Purpose

Find the most likely previous Codex session from sparse hints, then return enough evidence to resume work: session id, session JSONL path, matching user requests, key commands, app/job ids, files touched, and safe follow-up commands.

## Workflow

1. Extract search hints from the user:
   - Repo/workspace path, project name, branch, task domain, model/job/app names, command names, file paths, dates, and artifact ids.
   - Normalize typo-prone terms into variants, such as `egoposer`, `ego poser`, `EgoPoser`, `wholebody_pipeline`, `modal_train_mono_egoposer`.

2. Search low-cost indexes first:
   - `~/.codex/history.jsonl` for user prompts and `session_id`.
   - `~/.codex/memories/rollout_summaries/*.md` for compact summaries.
   - Current repo files for durable artifacts, launchers, configs, handoffs, logs, and output directories.

3. Search full session/log evidence:
   - `~/.codex/sessions/**/rollout-*.jsonl` for exact session transcripts.
   - `~/.codex/log/codex-tui.log` for tool calls, Modal/GitHub commands, app ids, function call ids, and tail logs.
   - Use specific `rg` patterns rather than broad dumps.

4. Rank candidate sessions:
   - Strong match: same cwd plus matching user request plus matching command/artifact.
   - Medium match: same cwd and topic, or same external job id.
   - Weak match: only topic or only repo path.
   - Prefer the newest strong match when the user asks for the session used to run a job.

5. Verify before reporting:
   - Locate the session JSONL file with `find ~/.codex/sessions -type f -name '*<session_id>*.jsonl'`.
   - Confirm at least one user prompt and one tool call or artifact line match the requested context.
   - If a remote job was involved, capture app/job/function ids and log commands when available.

6. Report concisely:
   - Session id and clickable local session file.
   - Why this is the right session.
   - Key commands or ids needed to resume.
   - Any uncertainty or missing evidence.
   - Do not paste huge logs; summarize only key lines.

## Command Patterns

Use read-only commands unless the user explicitly asks to resume/run something.

```bash
rg -n -i "hint1|hint2|repo_name|command_name" ~/.codex/history.jsonl ~/.codex/memories ~/.codex/sessions ~/.codex/log/codex-tui.log 2>/dev/null
find ~/.codex/sessions -type f -name '*<session_id>*.jsonl' -printf '%p\n'
rg -n "modal run|app logs|fc-|ap-|checkpoint|best|error|Traceback" ~/.codex/sessions/**/rollout-*.jsonl ~/.codex/log/codex-tui.log 2>/dev/null
rg -n -i "topic|command|artifact" . --glob '!**/.git/**' --glob '!**/__pycache__/**'
```

For large repositories or logs:

```bash
rg -n -i "specific_hint|session_id|job_id" ~/.codex/log/codex-tui.log | tail -200
rg -n -i "specific_hint|session_id|job_id" ~/.codex/sessions 2>/dev/null
```

## Output Template

```md
- Found session: `<session_id>`
- Session file: [rollout JSONL](/absolute/path/to/rollout.jsonl)
- Match evidence: same cwd `<path>`, user asked `<topic>`, commands included `<command>`.
- Resume command: `codex resume <session_id>`
- Useful follow-up commands:
  - `<command>`: why it matters
```

## Safety

- Do not modify or delete session, log, history, or repo files during recovery.
- Do not rerun Modal jobs, training, servers, deploys, or destructive commands unless the user explicitly asks.
- If secrets appear in logs, do not repeat them.
- If multiple sessions match, list the top candidates with evidence instead of pretending certainty.
