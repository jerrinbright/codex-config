---
name: paper-to-beamer
description: "Create conference Beamer presentations from LaTeX research papers. Use when the user asks to turn a paper such as SimGS into slides, a 10-minute talk, a conference presentation, a Beamer deck, speaker notes, or a paper-to-presentation workflow."
---

# Paper To Beamer

## Purpose

Turn a LaTeX research paper into a conference-ready Beamer deck and speaker-notes plan. Optimize for a clear 10-minute talk by default: one main story, strong visual choices, no overloaded slides, and faithful claims grounded in the paper.

## Default Outputs

Unless the user asks otherwise, create a simple `slides/` folder inside the paper workspace:

- `slides/presentation.tex`: Beamer source.
- `slides/presentation.pdf`: compiled deck, when validation succeeds.
- `slides/presentation_notes.md`: slide-by-slide speaker notes with approximate timing.

If a file already exists, write a non-conflicting filename such as `presentation_v2.tex`.
Use extraction context and LaTeX build files as temporary artifacts. Do not keep `presentation_context.md`, `.aux`, `.log`, `.nav`, `.snm`, `.toc`, `.out`, `.fls`, or `.fdb_latexmk` unless the user asks for debugging artifacts.
Do not write generated presentation files or LaTeX build artifacts directly into the paper root unless the user explicitly asks for that.

## Workflow

1. Resolve the paper workspace.
   - Prefer a user-provided folder or `main.tex`.
   - If the current workspace has `main.tex`, use it.
   - For DraftPilot projects, use the active paper root when available.
   - Fail loudly if `main.tex` cannot be found.

2. Extract paper context before drafting.
   - Create the default output directory first:

```bash
mkdir -p /path/to/paper/slides
```

   - Run the bundled scanner:

```bash
python3 <skill_dir>/scripts/extract_latex_paper_context.py /path/to/paper --main main.tex --out /tmp/presentation_context.md
```

   - Then read the extracted context plus the most relevant source sections directly.
   - For SimGS-style projects, always inspect `abstract`, `intro`, `method`, `experiments`, `discussion`, `conclusion`, and supplementary files when present.
   - If the paper is on a VM or remote SSH host, copy the scanner to `/tmp` on that host and run it there so relative figure paths and included TeX files resolve correctly.

3. Build the talk narrative.
   - Identify the central problem, why it is hard, the key idea, method stages, main results, ablations, limitations, and final takeaway.
   - Prefer claims already stated in the paper. Do not invent metrics, datasets, or qualitative results.
   - If a value is missing or marked `XX`, keep it as a placeholder or omit it from the slide.

4. Use a 10-minute slide budget by default.
   - Target 9-11 content slides, excluding optional backup.
   - Keep each slide to one message.
   - Prefer figures/tables already in the paper over dense prose.
   - Move detailed equations, long tables, and secondary ablations to backup slides.

5. Create Beamer source.
   - Use a clean, portable Beamer theme such as `metropolis` only if available or already used; otherwise use default Beamer with restrained styling.
   - Include needed paper macros from the paper preamble when they are used in slide text.
   - Use relative paths for figures, usually the same paths used by the paper.
   - Because the deck lives in `slides/`, add a paper-root search path such as `\graphicspath{{../}}` or rewrite figure paths so paper assets still resolve.
   - Keep slide text short: 3-5 bullets max, 7-10 words per bullet when possible.
   - Add speaker notes as `% Notes:` comments in `presentation.tex` and as fuller prose in `presentation_notes.md`.

6. Validate.
   - Run validation from the output folder:

```bash
cd /path/to/paper/slides
latexmk -pdf -interaction=nonstopmode -file-line-error presentation.tex
```

   - If `latexmk` is unavailable, try `pdflatex`.
   - After a successful compile, clean temporary LaTeX build files with `latexmk -c presentation.tex` or remove only the generated scratch files. Keep `presentation.pdf`.
   - Fix compile errors caused by the generated deck.
   - Do not change the original paper unless the user explicitly asks.

## 10-Minute Deck Structure

Use this baseline and adjust to the paper:

1. Title and one-sentence thesis.
2. Problem: what reconstruction/writing/science gap matters.
3. Why existing approaches fail.
4. Key idea and contributions.
5. Method overview figure.
6. Core technical mechanism.
7. Training or optimization strategy.
8. Main quantitative results.
9. Qualitative results or ablations.
10. Limitations and takeaway.

For a very technical method paper, split method into two slides and compress related work. For a results-heavy paper, use one method overview slide and give more time to experiments.

## Slide Quality Rules

- Make each slide answer one audience question.
- Prefer "claim to evidence" over section-summary slides.
- Use figure captions only as source material; rewrite slide captions for oral delivery.
- Preserve exact dataset names, method names, table numbers, and metric directions from the paper.
- Do not copy full paragraphs from the paper into slides.
- Use backup slides for extra tables, equations, and implementation details.
- If the paper is not camera-ready, include TODO placeholders rather than pretending results are final.

## Speaker Notes Rules

For each slide, write:

- Goal of the slide.
- 2-4 sentence spoken script.
- Timing estimate.
- Transition sentence to the next slide.

The notes should help the presenter rehearse a 10-minute talk, not repeat slide bullets verbatim.

## When Using With DraftPilot

If the paper is open in DraftPilot, keep the generated deck under the paper root at `slides/` so it can be edited, compiled, and reviewed beside the manuscript without cluttering source sections. Do not place generated slides inside DraftPilot app/source directories.

## References

For a detailed slide blueprint, read `references/ten_minute_beamer_blueprint.md` only when deciding deck structure or reviewing slide quality.
