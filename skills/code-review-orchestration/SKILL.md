---
name: code-review-orchestration
description: Coordinate an end-to-end code review loop using the existing code-review and code-review-response skills. Use when the user asks to spawn or delegate a fresh review, compare/respond to a review file, run follow-up review, or loop until a scoped code change is approved or blocked.
---

# Code Review Orchestration

Run a review loop that keeps reviewer independence, preserves a written review artifact, responds point-by-point, and asks for follow-up review before declaring closure.

This skill orchestrates the workflow only. Use `$code-review` for the reviewer pass and `$code-review-response` for the author response mechanics.

## Preconditions

- Default to a new, fresh-context reviewer subagent for the initial review pass. Treat a user request to use this orchestration skill as a request for delegated review.
- If the user specifies a model or reasoning level for the reviewer, pass those settings exactly.
- If subagents are unavailable or policy/tooling prevents spawning one, report that constraint and wait for the user's decision. Do not silently downgrade to a local self-review.
- Keep `code_review*.md` as review artifacts; do not stage, commit, overwrite, or delete them unless the user explicitly asks.

## Workflow

1. **Lock the scope before review**
   - Default the review scope to the current diff in the working directory.
   - If the user specifies a scope, diff range, file set, feature, or important risk area, use that instead of the default.
   - If the user provides both a scope and priority points to inspect, keep the scope bounded and foreground those points in the reviewer prompt.
   - Inspect the current diff and repo state enough to name the actual files and change areas.
   - Resolve the review artifact location, usually repo-root `code_review.md` or a non-conflicting variant.
   - Identify the intended behavior, not just the file list.

2. **Give the reviewer high-signal context**
   - Include exact scope: changed feature, files, and whether to review unstaged, staged, committed, or a diff range.
   - Include intent: what the change is trying to guarantee and why it was built.
   - Include invariants and risk areas the reviewer should pressure-test.
   - Include current verification already run and any unverified operations.
   - Include non-goals so the reviewer does not drift into unrelated refactors.

3. **Run the initial review**
   - Ask the reviewer to use `$code-review`.
   - Require a written `code_review*.md` artifact.
   - Keep the reviewer in review-only mode: no implementation edits during the initial pass.

4. **Respond to the review**
   - Read the review artifact.
   - Use `$code-review-response`.
   - Verify every finding against the actual code before acting.
   - Fix valid issues minimally; defend invalid or intentionally scoped choices with concrete evidence.
   - Append responses into the same review file without rewriting the reviewer text.
   - Run focused tests or checks that prove the response.

5. **Run follow-up review**
   - Prefer sending the same reviewer subagent back if available; otherwise spawn a fresh reviewer with the same model/reasoning and the same review file.
   - Ask it to follow the `$code-review` follow-up rules: verify code, author responses, and tests, then append a follow-up section if concerns remain.
   - Inspect the final review file yourself before reporting status.

6. **Decide**
   - `approved`: report closure, tests run, files touched, and review file path.
   - `request changes`: repeat response and follow-up review on remaining findings.
   - `needs discussion`: summarize the unresolved decision and stop rather than guessing.

## Reviewer Prompt Checklist

Good reviewer prompts usually include:

- Scope: exact diff, files, feature, and artifact path.
- Intent summary: user-facing behavior and operational reason for the change.
- Safety contracts: state files, caches, fingerprints, idempotency, tracking, migrations, compatibility, data correctness, or concurrency constraints.
- Interfaces: CLI commands, public modules, APIs, schemas, output files, and backwards compatibility expectations.
- Verification: tests already passed, checks not run, and real-world operations intentionally skipped.
- Review focus: ask for correctness and regression risk first, then docs and nits.

Avoid a prompt that only says "review the current diff" when the change has important invariants. Sparse prompts can miss deeper issues even with the same model and skill.

## Output

End with a concise status:

- Review artifact path.
- Initial verdict and follow-up verdict.
- Findings fixed, defended, or still open.
- Verification run.
- Whether review-stage status is approved, request changes, or needs discussion.
