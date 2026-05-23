# Ten-Minute Beamer Blueprint

Use this reference when turning a research paper into a conference talk. The goal is a crisp spoken story, not a miniature version of the paper.

## Timing

| Slide | Time | Purpose |
|---|---:|---|
| Title | 0:15 | Name the paper and thesis. |
| Problem | 0:45 | Make the audience care. |
| Gap | 0:55 | Explain why prior work is insufficient. |
| Key idea | 0:55 | State the contribution in one memorable sentence. |
| Method overview | 1:15 | Show the whole pipeline. |
| Technical core | 1:20 | Explain the mechanism that makes the method work. |
| Training/optimization | 1:05 | Explain the practical recipe. |
| Main results | 1:20 | Prove the method works quantitatively. |
| Analysis/qualitative | 1:00 | Build trust with visual or ablation evidence. |
| Takeaway | 0:40 | Close with what the audience should remember. |

Total: roughly 9:50. Leave 10 seconds of buffer.

## Strong Slide Patterns

- **Problem slide:** one visual or schematic plus 2-3 constraints.
- **Gap slide:** "Existing methods entangle X/Y/Z" or equivalent, with a concrete failure mode.
- **Key idea slide:** one sentence plus a simple diagram.
- **Method slide:** pipeline blocks, not equations first.
- **Technical slide:** explain the one mechanism that differentiates the work.
- **Results slide:** 1 table crop or chart with highlighted best rows, not the full paper table if it is dense.
- **Ablation slide:** component on/off story, not every variant.
- **Takeaway slide:** 3 bullets maximum: contribution, evidence, implication.

## Beamer Style

- Use large type and short bullets.
- Avoid dense algorithm boxes unless the algorithm is the contribution.
- Use paper figures directly when they are readable; otherwise crop or redraw a simplified version.
- Put extra equations and detailed tables in backup.
- Prefer dark text on light background unless the user has a specific visual identity.

## Speaker Notes Checklist

Each slide should include:

- **Goal:** the audience question this slide answers.
- **Script:** 2-4 sentences that can be spoken naturally.
- **Timing:** target seconds.
- **Transition:** one sentence that moves to the next slide.

## Final QA

- Can the whole talk be understood from slide titles alone?
- Does every technical term appear only after being motivated?
- Are the main results visible from the back of a room?
- Are all numbers traceable to the paper?
- Are placeholders clearly marked?
