# Scientific Poster Blueprint

## Default Poster

- Size: landscape A0 / 48 x 36 style unless the user specifies otherwise.
- Layout: baposter-style 4-column grid with title band across the top.
- Reading order: objectives, introduction, methodology, dataset/highlights, results, technical details, conclusion, bottom-row references/contact.
- Target density: roughly 700-1000 words total, less when figures are strong.

## Visual Hierarchy

1. Title readable from far away.
2. One-sentence thesis directly below the title or in the first column.
3. Method overview or central figure as the largest object.
4. Result callouts with metric direction and dataset labels.
5. Secondary details, ablations, and limitations near the end.

## Recommended Column Pattern

### Left Column

- `Objectives` at top.
- `Dataset` below objectives.
- `Highlights` filling the remaining height.

### Middle Column

- `Introduction` at top aligned with objectives.
- `Results` below, compact and table/callout driven.

### Right Two Columns

- `Methodology` wide box at top with the main architecture/pipeline figure.
- `Loss / Training` or technical-details box below methodology when needed.
- `Conclusion` wide box with qualitative result visual and concise takeaways.
- Bottom row: `References`, `Future Work`, `Contact`.

## Baposter Defaults

- Use `\documentclass[landscape,a0paper,fontscale=0.345]{baposter}` when the class is available.
- Use `headerborder=closed`, `colspacing=1em`, white background, dark blue/gray headers, and rounded-left content boxes for a familiar academic poster style.
- Keep logos optional. Do not insert missing logo filenames that will break compilation.
- Use `\graphicspath{{../figures/}{../Figures/}{../}}` because generated posters live in `poster/`.
- If `baposter.cls` is unavailable, create a portable fallback that still looks like a landscape poster grid. Do not fall back to a portrait-like article layout.

## Design Rules

- Use headings as claims, not generic labels when possible.
- Prefer concise bullets over paragraphs.
- Keep each header box short. A poster is not a compressed paper.
- Use no more than 2-3 font sizes for content hierarchy.
- Keep body text large enough for real poster viewing.
- Use color to group concepts and highlight best results, not as decoration.
- Leave enough whitespace around figures and tables.
- Avoid tiny legends, tiny table footnotes, and multi-line metric explanations.

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
- Does the poster compile from the `poster/` folder without needing files outside the paper workspace?
