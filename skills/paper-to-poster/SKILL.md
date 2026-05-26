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
- `poster/baposter.cls` plus its notice/license, when generated through DraftPilot or when a bundled copy is available.

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
   - Default to a baposter-style landscape grid unless the user specifies another size.
   - Use 4 visual columns for the default method-paper poster.
   - Keep the poster box-based: title band, left motivation/dataset/highlights column, center results column, wide methodology and technical-detail boxes, and a compact bottom row.
   - Avoid making a portrait-looking document on a landscape page.
   - For portrait/A0 requests, adapt the same box hierarchy rather than squeezing the landscape layout.
   - Read `references/scientific_poster_blueprint.md` when choosing a layout or checking poster quality.

5. Create LaTeX poster source.
   - Prefer a `baposter`-style source for the default scientific-poster output: `\documentclass[landscape,a0paper,fontscale=0.345]{baposter}` with `\headerbox{...}{...}{...}` sections.
   - Do not copy third-party template comments, branding, or license text into generated posters. Use the layout pattern, not the template verbatim.
   - If DraftPilot already copied `poster/baposter.cls`, keep that class file and its notice/license beside the poster source so compilation is portable.
   - If `baposter.cls` is unavailable and no bundled copy exists, use a portable fallback that visually mimics baposter with `article`, `geometry`, `xcolor`, `multicol`, and boxed sections.
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

Use this default baposter-style structure and adjust to the paper:

1. Title band: title, authors, affiliation, optional logo/code/project link.
2. `Objectives`: short problem statement and goal.
3. `Introduction`: compact motivation and gap.
4. `Methodology`: wide top-right box spanning two columns with the main architecture/pipeline figure.
5. `Dataset`: input data, evaluation setting, sequences, and preprocessing summary.
6. `Highlights`: 3-5 contribution bullets.
7. `Results`: compact table/callout, not a dense paper table.
8. `Loss / Training` or `Technical Details`: only if the method needs equations/stages for credibility.
9. `Conclusion`: qualitative result visual plus 3 concise takeaways.
10. Bottom row: `References`, `Future Work`, and `Contact`.

Do not overdo the number of boxes. Prefer these sections first; add ablation/limitations only when the paper needs them and there is space.

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

DraftPilot-generated poster jobs copy the bundled `baposter.cls` and license/notice files into `poster/`. Use that local class file instead of assuming the user's TeX distribution has baposter installed system-wide.

## References

For layout, visual hierarchy, and poster review criteria, read `references/scientific_poster_blueprint.md` only when deciding poster structure or reviewing poster quality.
