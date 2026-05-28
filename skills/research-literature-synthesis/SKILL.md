---
name: research-literature-synthesis
description: "Search, read, and synthesize research literature and technical evidence for AI/ML work. Use for literature reviews, paper lookup, state-of-the-art summaries, hypothesis generation, research gap analysis, critical evaluation of papers, citation-backed technical decisions, and turning research evidence into experiment plans."
---

# Research Literature Synthesis

## Purpose

Build citation-backed understanding before research or engineering decisions. This fills the gap between broad `ai-research-orchestrator` planning and paper-writing/presentation skills.

Use this when the user asks what the literature says, whether an approach is sound, what papers/tools exist, how to frame a hypothesis, or how to critically assess a paper.

Read `references/evidence-and-hypotheses.md` for literature-review, hypothesis-generation, and critical-thinking checklists.

## Workflow

1. **Define question**
   - Topic, model/task/domain, time horizon, required depth, and whether current web search is needed.

2. **Search**
   - Prefer primary sources: papers, official docs, benchmark reports, and repo docs.
   - Track search queries and inclusion/exclusion criteria when doing a real review.
   - For current tools or emerging methods, verify dates and latest versions.

3. **Extract**
   - Problem, method, data, metrics, baselines, limitations, compute, reproducibility signals, and claimed contribution.

4. **Critique**
   - Check whether claims are supported by experiments.
   - Identify confounders, missing baselines, weak evals, data leakage, small samples, or non-comparable metrics.

5. **Synthesize**
   - Group findings by theme.
   - Separate consensus, disputed claims, and open gaps.
   - Convert evidence into testable hypotheses or concrete engineering recommendations.

6. **Report**
   - Include links/citations.
   - State confidence and what evidence is missing.
   - If this feeds our own experiments, propose the smallest validation run.

## Output Shape

```md
**Research Synthesis**
- Question:
- Sources checked:
- What seems true:
- What is uncertain:
- Best next experiment:
- Key sources:
```

