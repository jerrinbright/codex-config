---
name: paper-template-starter
description: "Create rough LaTeX research paper starter templates. Use when the user wants a new paper scaffold, custom manuscript template, conference-paper starting point, supplement skeleton, or DraftPilot-ready LaTeX workspace."
---

# Paper Template Starter

## Purpose

Create a clean, editable LaTeX research-paper starter that the user can build on quickly. Favor a useful first scaffold over a polished final paper: clear section boundaries, TODO placeholders, bibliography/figure/table folders, and enough structure for an AI agent to start drafting with context.

## Default Output

Unless the user asks otherwise, scaffold into the requested paper folder:

- `main.tex`: primary manuscript entrypoint.
- `supplementary.tex`: standalone supplement entrypoint.
- `refs.bib`: seed bibliography file with commented examples.
- `sections/*.tex`: manuscript sections with short TODO prompts.
- `figures/` and `tables/`: empty asset folders.
- `notes/paper_plan.md`: author-facing checklist and drafting plan.

Do not overwrite existing files unless the user explicitly asks. If the folder already contains a paper, add only missing files or create a new sibling folder.

## Workflow

1. Resolve the target folder.
   - Prefer the folder the user names.
   - For DraftPilot, use the active project root when the user says "this workspace" or "current paper".
   - If no folder is clear, ask once for the target folder.

2. Choose a profile.
   - `generic`: default for most research papers.
   - `ml`: machine-learning or robotics method papers.
   - `vision`: computer-vision reconstruction, generation, perception, or graphics papers.
   - `systems`: systems, infrastructure, or tool papers.
   - If unsure, use `generic` and customize section titles from the user's idea.

3. Run the bundled scaffold script:

```bash
python3 <skill_dir>/scripts/create_paper_template.py /path/to/paper \
  --title "Working Paper Title" \
  --profile vision \
  --venue "WACV 2027"
```

   - Add `--force` only when the user explicitly wants existing starter files replaced.
   - Add `--skip-existing` when adding missing template files to a partially populated workspace.

4. Customize the scaffold.
   - Replace generic placeholders with the user's topic, datasets, method modules, expected figures, and experiment plan when that information is available.
   - Keep unknown claims as `TODO:` or `XX`, never invent results.
   - Keep the template compact; avoid writing a full paper unless the user asks.

5. Validate when feasible.
   - Run `latexmk -pdf -interaction=nonstopmode -file-line-error main.tex` if LaTeX is available.
   - Also compile `supplementary.tex` if the user plans to use a supplement.
   - Fix template-generated compile errors, but do not install TeX dependencies without user approval.

## Quality Rules

- Make the first page useful immediately: title, abstract placeholder, and a concise contribution checklist.
- Use simple portable LaTeX packages unless the user asks for a venue-specific style.
- Put detailed writing prompts in comments or `notes/paper_plan.md`, not as visible manuscript prose.
- For venue templates, only use official style files that already exist in the target workspace or that the user provides.
- Keep output DraftPilot-friendly: `main.tex` should compile locally, and standalone files such as `supplementary.tex` should compile independently.

