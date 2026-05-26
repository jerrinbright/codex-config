# Scientific Poster Blueprint

## Default Poster

- Size: 48 x 36 inches, landscape.
- Layout: 3 columns, with title band across the top.
- Reading order: thesis, problem, method, evidence, takeaway.
- Target density: roughly 700-1000 words total, less when figures are strong.

## Visual Hierarchy

1. Title readable from far away.
2. One-sentence thesis directly below the title or in the first column.
3. Method overview or central figure as the largest object.
4. Result callouts with metric direction and dataset labels.
5. Secondary details, ablations, and limitations near the end.

## Recommended Column Pattern

### Left Column

- Problem and motivation.
- Key contributions.
- Dataset/task setup.
- Small schematic or example input.

### Center Column

- Main method pipeline.
- Technical mechanism, training stages, or system architecture.
- One compact equation only if it is central to the contribution.

### Right Column

- Quantitative results.
- Qualitative examples.
- Ablation/analysis.
- Limitations, conclusion, and QR/code/contact.

## Design Rules

- Use headings as claims, not generic labels when possible.
- Prefer concise bullets over paragraphs.
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
