---
name: paper-to-poster
description: "Create scientific conference posters from LaTeX research papers. Use when the user asks to turn a paper into a poster, research poster, conference poster, scientific poster, poster PDF, poster TeX, or poster presentation workflow."
---

# Paper To Poster

## Purpose

Turn a LaTeX research paper into a clean scientific poster that can be edited, compiled, and reviewed locally. Optimize for a conference poster by default: a sharp thesis, readable visual hierarchy, strong figures, compact evidence, and faithful claims grounded in the paper.

## Default Outputs

Unless the user asks otherwise, create a `poster/` folder inside the paper workspace:

- `poster/poster.tex`: poster source.
- `poster/poster.pdf`: compiled poster, when validation succeeds.
- `poster/poster_notes.md`: design notes, missing-content TODOs, and a short presenter walkthrough.

If a file already exists, write a non-conflicting filename such as `poster_v2.tex`.
Use extraction context and LaTeX build files as temporary artifacts. Do not keep `poster_context.md`, `.aux`, `.log`, `.out`, `.fls`, `.fdb_latexmk`, `.synctex.gz`, or other scratch files unless the user asks for debugging artifacts.
Do not write generated poster files or LaTeX build artifacts directly into the paper root unless the user explicitly asks for that.

## Workflow

1. Resolve the paper workspace.
   - Prefer a user-provided folder or TeX file.
   - If the current workspace has `main.tex`, use it by default.
   - If DraftPilot metadata names a different main TeX file, use that file.
   - Fail loudly if the main TeX file cannot be found.

2. Extract paper context before designing.
   - Create the output directory first:

```bash
mkdir -p /path/to/paper/poster
```

   - Run the bundled scanner:

```bash
python3 <skill_dir>/scripts/extract_latex_paper_context.py /path/to/paper --main main.tex --out /tmp/poster_context.md
```

   - Then read the extracted context plus the most relevant source sections directly.
   - Always inspect the abstract, introduction, method, experiments, key tables, key figures, limitations, conclusion, and supplementary files when present.
   - If the paper is on a VM or remote SSH host, copy the scanner to `/tmp` on that host and run it there so relative figure paths and included TeX files resolve correctly.

3. Build the poster message.
   - Identify the one-sentence thesis, problem, key insight, method pipeline, main quantitative result, best qualitative evidence, limitations, and code/project link.
   - Prefer claims already stated in the paper. Do not invent metrics, datasets, or qualitative results.
   - If a value is missing or marked `XX`, keep it as a placeholder or write a visible TODO in `poster_notes.md`.

4. Choose poster layout.
   - Default to a 48 x 36 inch landscape poster unless the user specifies another size.
   - Use 3 columns for most method papers.
   - Use 4 columns only when the paper has many compact result panels and the text remains readable.
   - For portrait/A0 requests, adapt the same hierarchy rather than squeezing the landscape layout.
   - Read `references/scientific_poster_blueprint.md` when choosing a layout or checking poster quality.

5. Create LaTeX poster source.
   - Prefer a portable LaTeX poster implementation that compiles in common TeX installs.
   - Use `beamerposter` only when it is available or already used locally. Otherwise use `article` with `geometry`, `multicol`, `graphicx`, `xcolor`, `tikz`, and `tcolorbox` if available.
   - Add a paper-root search path such as `\graphicspath{{../}}` because the poster lives in `poster/`.
   - Use relative paths for figures, usually the same paths used by the paper.
   - Keep poster text short: headings should carry the story, body copy should be scannable, and bullets should be sparse.
   - Convert dense tables into small result callouts when possible.
   - Include a compact QR/code/contact block if the paper has a repository URL or project URL.

6. Validate.
   - Run validation from the output folder:

```bash
cd /path/to/paper/poster
latexmk -pdf -interaction=nonstopmode -file-line-error poster.tex
```

   - If `latexmk` is unavailable, try `pdflatex`.
   - After a successful compile, clean temporary LaTeX build files with `latexmk -c poster.tex` or remove only generated scratch files. Keep `poster.pdf`.
   - Fix compile errors caused by the generated poster.
   - Do not change the original paper unless the user explicitly asks.

## Poster Structure

Use this baseline and adjust to the paper:

1. Title, authors, affiliations, and code/project link.
2. One-sentence thesis or key takeaway.
3. Motivation and problem.
4. Core insight or contributions.
5. Method overview pipeline.
6. Technical details that matter for credibility.
7. Main quantitative results.
8. Main qualitative results.
9. Ablations or analysis.
10. Limitations, conclusion, and next steps.

For method-heavy papers, give the center column to the pipeline and training/optimization strategy. For results-heavy papers, give the center and right columns to quantitative and qualitative evidence.

## Quality Rules

- Make the poster understandable in 30 seconds, useful in 3 minutes, and defensible in 10 minutes.
- Use large visual anchors: one method figure and one results figure should dominate.
- Avoid paragraph walls. If a section needs more than 60-90 words, compress it or move detail to notes.
- Preserve exact dataset names, method names, metric directions, table numbers, and figure meanings from the paper.
- Do not copy full paper paragraphs into the poster.
- Do not invent figure files. If a desired visual is missing, add a TODO in `poster_notes.md`.
- Use placeholders such as `XX` for unconfirmed results.
- Prefer readable colors and high contrast over decorative styling.
- Keep generated output organized under `poster/`.

## Poster Notes

Write `poster_notes.md` with:

- Poster goal and target audience.
- Layout rationale.
- Source figures/tables used.
- Missing assets or placeholder values.
- A 2-3 minute walkthrough script.
- Print/export reminders, including checking conference size requirements before final printing.

## When Using With DraftPilot

If the paper is open in DraftPilot, keep the generated poster under the paper root at `poster/` so it can be edited, compiled, and reviewed beside the manuscript without cluttering source sections. Do not place generated posters inside DraftPilot app/source directories.

## References

For layout, visual hierarchy, and poster review criteria, read `references/scientific_poster_blueprint.md` only when deciding poster structure or reviewing poster quality.
