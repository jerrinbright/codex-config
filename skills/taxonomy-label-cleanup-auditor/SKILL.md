---
name: taxonomy-label-cleanup-auditor
description: "Audit action-label taxonomy outputs for spelling drift, bad verb/object taxonomy, noisy residual clauses, object fragments, punctuation leaks, and unsafe cleanup candidates. Use after building auxiliary verb/noun targets from labels such as Naruto, Mecka, or Molmo redelivery JSON files."
---

# Taxonomy Label Cleanup Auditor

Use this skill when auditing action-label datasets or manual verb/noun taxonomy outputs for spelling drift, bad verb/object taxonomy, noisy residual clauses, object fragments, and unsafe cleanup candidates. It is especially useful after building auxiliary verb/noun targets from labels such as Naruto/Mecka/Molmo redelivery JSON files.

## What This Skill Catches

- High-confidence typos that damage verb/object learning, such as `assay -> assess`, `peal -> peel`, `tun -> turn`, `pic/pock up -> pick up`, `turnoff -> turn off`, and `arrangescrews -> arrange screws`.
- Dangerous broad replacements that need context checks, such as `pink -> pick`, `sweet -> sweep`, `stair -> stir`, `shirt -> shift`, `hole -> hold`, `pill -> peel`, `form -> from`, and `shit -> shift`.
- Taxonomy bugs where object heads are misclassified as descriptors or dropped from nouns.
- Punctuation leaks where separators like `.` or following verbs leak into noun targets.
- No-verb residuals and first-token weirdness that usually reveal typos, object/list fragments, or missing verb vocabulary.
- Over-aggressive semantic collapsing. Keep raw taxonomy lossless; coarse buckets can be added later.

## Inputs

Prefer one or both:

- Source labels JSON, usually a cleaned selected dataset.
- Taxonomy output directory containing any of:
  - `clause_taxonomy.jsonl`
  - `segment_aux_targets.jsonl`
  - `verb_vocab.csv`
  - `noun_vocab.csv`
  - `no_verb_first_tokens.csv`
  - `taxonomy_coverage_summary.json`

## Workflow

1. Locate the latest cleaned label source and taxonomy artifact directory.
2. Run the bundled audit script:

```bash
python3 /Users/jerrinbright/Desktop/jb_ws/codex-config/skills/taxonomy-label-cleanup-auditor/scripts/audit_taxonomy_cleanup.py \
  --labels /path/to/labels.json \
  --taxonomy-dir /path/to/taxonomy_dir \
  --output-dir /tmp/taxonomy_cleanup_audit
```

3. Read `report.md`, `typo_candidates.csv`, `residual_first_tokens.csv`, and `target_integrity.json`.
4. Report issues grouped into:
  - high-confidence typo fixes
  - safe verb additions
  - context-only typo fixes
  - remove/review candidates
  - noun/descriptor bugs
  - punctuation or verb-as-noun leakage
5. Do not auto-apply broad replacements unless the user explicitly approves exact rules.
6. If fixes are applied, rerun taxonomy generation and this audit. Check that:
  - `descriptor_no_noun_rows == 0`
  - `punct_noun_rows == 0`
  - common object heads appear as nouns when standalone
  - no meaningful word remains in residual/unknown buckets

## Safety Rules

- Never globally replace color/location/common-object words with verbs.
- Preserve no-action rows unless the user explicitly asks to remove them.
- Treat unknown/review tokens as masked for auxiliary loss, never as negatives.
- Prefer surgical regex rules over token-level replacements.
- If a word can be a real noun or descriptor, classify by context:
  - `pick up cloth`: `cloth` is noun.
  - `fold paper`: `paper` is noun.
  - `wipe glass with cloth`: `glass` and `cloth` are nouns.
  - `pick up plastic bag`: `plastic` is descriptor, `bag` is noun.
- Keep particles explicit:
  - `pick up`: `pick` is verb, `up` is verb_particle.
  - `turn off`: `turn` is verb, `off` is verb_particle.
  - `place cloth on table`: `on` is preposition.

## Known Good Contextual Fix Patterns

- `assay` usually means `assess` in inspection/action labels.
- `pic up`, `pock up`, and `puck up` can be `pick up`, but do not rewrite `pink`.
- `peal` can be `peel`; `tun` can be `turn`.
- Clause-start `deep` can be `dip`; clause-start `flat` can be `flatten`.
- `fine tune` should normalize to `fine-tune` only when it is the intended action.
- `folk`/`folks` can be `fork`/`forks` in utensil contexts.
- `hummer` can be `hammer`; `hols` can be `hold`; `soon` can be `spoon`.
- `crew` can be `screw`; `facet` can be `faucet`.
- `crape`/`scape` can be `scrape`; `pray` can be `spray`.
- `attache`/`attack` can be `attach` in attachment contexts.
- `potion` can be `portion`; `inert` can be `insert`.
- `fe dough` can be `feed dough`; `gasp` can be `grasp`.
- `sweet floor` or `sweet debris` can be `sweep`; never rewrite `sweet potato`.
- `stair powder` can be `stir powder`; never rewrite actual stairs.
- `shit` requires context:
  - `t-shit` can be `t-shirt`.
  - object `shit` can be `sheet` only with supporting context.
  - clause-start `shit ...` can be `shift ...` only with safe following tokens.
- `pill` requires context:
  - `pill off` can be `peel off`.
  - `pill up/out` can be `pull up/out`.
  - `from pill` can be `from pile`.

## Output Expectations

When presenting findings, include counts and 2-5 concrete examples for each major issue. Be explicit about whether a recommendation is safe to auto-apply, needs human review, or should only be masked from auxiliary targets.
