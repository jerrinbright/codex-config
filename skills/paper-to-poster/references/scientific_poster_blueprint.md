# Scientific Poster Blueprint

## Default Poster

- Size: landscape A0 / 48 x 36 style unless the user specifies otherwise.
- Layout: baposter-style 4-column grid with title band across the top.
- Reading order: research question, dataset, takeaways, failure modes/future work, wide method, main results, analysis/evidence boxes, interpretation, compact references.
- Target density: roughly 300-800 words total, less when figures are strong.
- Overall feel: polished conference artifact, not a compressed paper. Strong visuals, consistent typography, aligned boxes, minimal empty space, and no clipped figures.

## Visual Hierarchy

1. Title readable from far away.
2. One-sentence thesis directly below the title or in the first column.
3. Method overview or central figure as the largest object.
4. Result callouts with metric direction and dataset labels.
5. Analysis visuals such as confusion, feature importance, ablation, or qualitative results.
6. Interpretation and limitations near the end.

## Recommended Column Pattern

### Left Column

- `Research Question` or `Objective` at top.
- `Dataset` below the research question.
- `Key Takeaways` below dataset.
- `Failure Modes`, limitations, or future work at the bottom with one clear visual when possible.

### Center Columns

- A wide `Method` box spanning two columns near the top with the main pipeline/architecture figure.
- Lower evidence boxes such as `Confusion Pattern`, `Feature Importance`, `Ablation`, or `Qualitative Results`.

### Right Column

- `Main Results` at the top with compact table/callouts and one result visual.
- `Interpretation` below results.
- `References` at the bottom.
- Do not include a contact section by default.

## Baposter Defaults

- Use `\documentclass[landscape,a0paper,fontscale=0.345]{baposter}` as a starting point when the class is available; adjust `fontscale` around `0.345` to `0.365` during visual QA if readability or density requires it.
- Use `headerborder=closed`, white background, dark blue/gray headers, rounded content boxes, and consistent outer padding.
- Keep logos optional. Do not insert missing logo filenames that will break compilation.
- Use `\graphicspath{{../figures/}{../Figures/}{../}}` because generated posters live in `poster/`.
- If `baposter.cls` is unavailable, create a portable fallback that still looks like a landscape poster grid. Do not fall back to a portrait-like article layout.

## Design Rules

- Use headings as claims, not generic labels when possible.
- Prefer concise bullets over paragraphs.
- Keep each header box short. A poster is not a compressed paper.
- Use no more than 2-3 font sizes for content hierarchy.
- Keep body text large enough for real poster viewing.
- Keep all body content inside section boxes visually the same size. Avoid local `\scriptsize`/`\small` patches in tables, captions, bullets, and mini labels.
- Use color to group concepts and highlight best results, not as decoration.
- Leave enough whitespace around figures and tables.
- Avoid tiny legends, tiny table footnotes, and multi-line metric explanations.
- Avoid colored section backgrounds when imported figures use white backgrounds; white boxes with dark headers usually look cleaner.
- Fill space intentionally. If a box has a large empty region, either reduce its height, center/rebalance its contents, or add a meaningful concise point.
- References should usually be only 1-2 compact entries: `[n] Author et al. "Title." Abbrev. Venue, Year.` No page numbers.

## Figure Rules

- Figures are the poster's main story. Prefer large, readable figures over many small figures.
- If a figure appears clipped after compile, inspect the asset rather than only shrinking it. SVG/PDF conversions can clip embedded rasters at the bounding box.
- For clipped SVG-to-PDF assets, use an uncut PNG, regenerate the plot with more padding, or adjust the source viewBox/bounding box.
- Check pie charts, legends, axis labels, and heatmaps carefully; these are commonly clipped or too small.
- Do not accept cropped legends, cut-off wedges, or labels touching borders.

## Scientific Integrity

- Every numeric claim should trace back to a paper table, result log, or explicit user-provided value.
- If a figure is cropped, converted, or simplified, preserve its meaning.
- Do not make new claims from visual intuition alone.
- Mark missing values as `XX` and list them in `poster_notes.md`.

## Review Checklist

- Can someone understand the contribution in 30 seconds?
- Is the core method visible without reading body text?
- Are result directions obvious?
- Are datasets and baselines named exactly?
- Are unverified values marked as placeholders?
- Are all section body fonts visually consistent?
- Are any figures, legends, labels, or tables clipped?
- Are left/right/bottom outer paddings visually similar?
- Are any boxes too empty or too crowded?
- Does the poster compile from the `poster/` folder without needing files outside the paper workspace?
- Has the compiled PDF been rendered to an image and inspected before delivery?
