---
name: paper-to-poster
description: "Create scientific conference posters from LaTeX research papers. Use when the user asks to turn a paper into a poster, research poster, conference poster, scientific poster, poster PDF, poster TeX, or poster presentation workflow."
---

# Paper To Poster

## Purpose

Turn a LaTeX research paper into a polished conference poster that can be edited, compiled, and reviewed locally. Optimize for a real conference artifact by default: a sharp thesis, readable visual hierarchy, strong unclipped figures, compact evidence, faithful claims grounded in the paper, and a rendered layout that looks intentional rather than like paper text dumped into boxes.

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
   - Before writing TeX, create a short content plan that names the selected sections, the dominant method visual, the dominant results visual, and the single takeaway readers should remember.
   - If the user selected sections, honor that selection. If no sections are selected, use the detailed default section set below.

4. Choose poster layout.
   - Default to a baposter-style landscape grid unless the user specifies another size.
   - Use 4 visual columns for the default method-paper poster.
   - Keep the poster box-based: title band, left research-question/dataset/takeaways/failure-modes column, wide method box across the top center, main-results box at top right, analysis/evidence boxes across the lower center, and compact interpretation/references boxes at lower right.
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
   - Include a compact QR/code block only when useful. Do not include a contact section by default unless the user asks for it or the venue requires it.
   - Target 300-800 total words for an A0/48x36 poster. Keep individual boxes around 50-100 words maximum, and make the poster visually dominant rather than prose dominant.
   - Allocate space as if 60-70% of the poster should be visual material when suitable paper figures/tables exist.
   - Use no more than one dense technical/equation box unless the user explicitly asks for a theory-heavy poster.
   - Keep typography consistent inside section boxes. Define one body size through the poster class/global `textfont`, one section-header size, and at most one metric/title size. Do not sprinkle `\scriptsize`, `\small`, or ad hoc font changes across captions, tables, and bullets just to make content fit.
   - If content does not fit, shorten the text, resize/rearrange the box, or simplify the section. Do not hide layout problems by shrinking isolated text blocks.
   - Add editable header controls in the poster preamble so title placement can be tuned without editing the class: `\posterHeaderHeight`, `\posterTitleBoxXShift`, `\posterTitleBoxYShift`, `\posterTitleBoxWidth`, `\posterTitleBoxHeight`, and `\posterTitleFontScale`. Use `headerheight=\posterHeaderHeight` in the poster options.
   - The bundled `baposter.cls` supports those header controls and redraws each section tab above box contents; use the bundled/local class when possible so images cannot cover section headings.
   - Use only 1-2 clean references by default. Format them as compact BibTeX-style entries with `[n]`, first author `et al.`, title, abbreviated venue, and year. Omit page numbers. Cite them inline where used, such as `[1]`.

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
   - Inspect the log for overfull boxes, missing figure paths, and text cutoff risk. If the layout is crowded, shorten text or merge sections rather than reducing font to unreadable sizes.
   - Render the compiled PDF to an image and inspect it before finishing. Do not rely on LaTeX success alone.
   - Run a visual QA loop until the poster is clean: check for clipped figures, uneven white space, text overflow past borders, cramped section content, inconsistent font sizes, tiny legends, misaligned columns, uneven outer padding, and sections that look half-empty.
   - If a figure is clipped in the poster, inspect the source asset. SVG-to-PDF wrappers often clip embedded raster images; switching to an uncut PNG or regenerating the plot with more padding is better than merely shrinking `\includegraphics`.
   - Keep left, right, and bottom outer padding visually similar. Keep section borders aligned to the grid.

## Poster Structure

Use this default baposter-style structure and adjust to the paper:

1. Title band: title, authors, affiliation, optional logo/code/project link.
2. `Research Question` or `Objective`: the main question plus 3-4 bullets explaining what is tested.
3. `Dataset`: compact dataset description plus a small centered table or data visual.
4. `Key Takeaways`: 3-5 bullets that state the poster's main conclusions.
5. `Failure Modes` / `Limitations` / `Future Work`: one strong visual plus concise next steps.
6. `Method`: the largest central box, preferably spanning two columns, with the main pipeline/architecture figure and 2-4 bullets.
7. `Main Results`: compact table/callouts plus one result visual.
8. Lower analysis boxes such as `Confusion Pattern`, `Feature Importance`, `Ablation`, or `Qualitative Results`: use normal body font, readable figures, and concise interpretation.
9. `Interpretation`: short explanation of what the results mean and why errors persist.
10. `References`: 1-2 compact references. No contact box by default.

Do not overdo the number of boxes. Prefer these sections first; add ablation/limitations only when the paper needs them and there is space.

When the user or DraftPilot UI provides a section subset, include those sections first. It is acceptable to merge small bottom-row sections such as `References` and `Future Work` when space is tight, but do not silently drop a requested scientific section such as `Methodology`, `Dataset`, `Results`, or `Loss / Training`.

## Quality Rules

- Make the poster understandable in 30 seconds, useful in 3 minutes, and defensible in 10 minutes.
- Use large visual anchors: one method figure and one results figure should dominate.
- Avoid paragraph walls. If a section needs more than 60-90 words, compress it or move detail to notes.
- Keep each visual focused on one idea. Avoid tiny multi-stage diagrams with five or more steps; split or simplify them into a poster-readable figure.
- Use large readable labels in figures and captions. Poster figures should be understandable from several feet away.
- Use generous margins. Nothing should touch the physical poster edge or box border.
- Make figure quality a first-class requirement. No clipped pie charts, cropped legends, cut-off labels, or tiny unreadable plots. If the compiled preview shows clipping, fix the asset or regenerate the plot.
- Maintain visual density. Avoid boxes with large unused bottom gaps; reduce their height, add meaningful content, or rebalance neighboring boxes.
- Keep body text visually consistent across all scientific sections. Tables, captions, bullets, mini-labels, and interpretation text should look like one system.
- Prefer white boxes and restrained dark-blue/gray headers. Avoid colored section backgrounds when figures have white backgrounds.
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
