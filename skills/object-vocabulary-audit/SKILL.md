---
name: object-vocabulary-audit
description: Decide what counts as an object and clean any bucket of object strings - a MAP/SigLIP bank, a val/GT label set, or a new pull's extracted vocabulary. Use when auditing or reducing an object bank, checking whether ground-truth labels are over-specific or noisy, deciding if a term is a real object, or diagnosing why a model plateaus on a label set.
---

# Object vocabulary audit

Turn a raw bucket of object strings into a canonical vocabulary, or audit an
existing one. Works on a bank, a GT/val label set, or a fresh extraction.

Every rule was forced by a measured failure. Numbers are from the multicam corpus
(354k segments, Aug 2026).

## The one rule that governs everything else

There are TWO orthogonal axes. Confusing them corrupts the whole audit.

```
Axis A  is this a canonical OBJECT NAME?
        spelling · plurals · word order · colour/size/state prefixes ·
        fragments · true synonyms · over-specificity
        -> this, and ONLY this, decides what is deleted or merged

Axis B  does TRAINING DATA exist for it?
        -> a DIAGNOSTIC. It tells you what a model can learn.
           It NEVER decides whether a term belongs in the vocabulary.
```

A `jackhammer` seen zero times is exactly as much an object as a `brush` seen
6,866 times. Coverage is reported, never acted on.

**Failures this rule prevents, both observed:**

- Rejecting by lexical class deleted `brush` (6,866), `paper` (5,504),
  `fabric` (3,129), `iron` (2,549), `leather` (1,873), `hammer` (1,773) --
  they appeared on a "verbs" or "materials" list. It would have dropped 6,507
  training rows. These are verbs AND objects, materials AND objects; a word's
  part of speech does not settle whether it names a thing.
- Gating head-backoff on zero support collapsed `air fryer knob -> knob` *because
  no data existed for it*, not because the name is over-specific. Backwards: if
  the compound names a distinct thing it stays whatever its frequency; if it is
  over-specific it collapses whatever its frequency.

Patching the first failure with a frequency floor is also wrong -- right outcome,
wrong reason, and it re-imports Axis B through the back door.

**Over-specificity is a semantic judgement, not a data one.** Ask: does the
modifier change the physical thing being manipulated?

```
accessory pouch -> pouch     modifier adds nothing physical      COLLAPSE
plastic bag     -> bag       material IS the object              KEEP
perfume bottle  -> perfume   container is not its contents       KEEP
apple skin      -> apple     skin/peel/shell is a distinct thing KEEP
air fryer knob  -> knob      a knob is a knob                    COLLAPSE
```

This is the call the SPLITTER and MERGER agents argue over, and the only
evidence that counts is physical, not statistical.

## The naming invariant — never misname an object

Every collapse must leave a name that is still TRUE of the thing.

```
abrasive pad -> pad        a pad. VALID
X sleeve     -> sleeve     a sleeve. VALID
air blow gun -> gun        NOT a firearm. INVALID
air bulb     -> bulb       NOT a light bulb. INVALID
battery component -> battery   a PART of a battery, not a battery. INVALID
```

The head noun of an English compound is the LAST word. Dropping the last word
(`battery component -> battery`) collapses a part into its whole and is always
wrong.

**Rejected lever: cosine cannot detect this.** SigLIP text similarity encodes
general relatedness, not subtype:

```
air blow gun ~ gun    0.830   (must NOT collapse)
abrasive pad ~ pad    0.691   (safe to collapse)
```

The unsafe pair scores HIGHER. No threshold separates them. Do not try again.

## The standard collapse rule

Decide per HEAD NOUN, not per compound — 5,773 compounds reduced to 764 heads,
so the judgement is asked once each.

```
collapse compounds whose head has >= MIN_FANOUT compounds   (default 20)
   a head used 20+ times is a category word: cover, lid, frame, sleeve, tray
   a head used 2-3 times is probably naming a specific thing -- leave it

protect AMBIGUOUS_HEAD: the bare noun denotes something else
   gun bulb board machine toy bag paper tape chip nail spring mouse tank jack
   plug pad block cell key pin ring bar arm head body mount base stand bit lead
   seal joint spot face top bottom back front side end piece unit set kit line stick

protect KEEP_COMPOUND: the modifier is identifying
   plastic bag · paper bag · plastic sheet · perfume bottle · water bottle ·
   paint can · glue stick · blister pack · apple skin · orange peel · egg shell ·
   nut shell · book page · sand paper · masking tape · cutting board · headlamp
```

MIN_FANOUT is the size knob. Measured curve on one 7,774-name bank:

```
MIN_FANOUT     20      15      12      10       5       2
final       5,262   4,800   4,531   4,209   3,509   2,792
```

**Target ~5,000.** A 5,463-name bank beat an 11,952-name one by 5.8 points; nothing
below ~2,500 has ever been measured, so going smaller is a bet, not a cleanup.
MIN_FANOUT=20 lands at 5,262.

Re-derive AMBIGUOUS_HEAD for a new domain — it is a semantic list, not a constant.

## Running this on a new dataset

**Inputs required**

```
1. the bucket of object strings to audit          (bank / GT / fresh extraction)
2. a TRAIN-DERIVED reference bank                 (never train+val -- Stage 0b)
3. SigLIP text embeddings for the bucket          (for synonym merging)
4. per-object training counts                     (DIAGNOSTIC ONLY -- never a
                                                   deletion criterion)
```

**Sequence that actually produced a shipped bank** (8,428 -> 5,262):

```
A. ceiling gate                     what do the labels even allow?
B. normalise (Stages 1-5)           reject non-objects, strip colour/size/state,
                                    fragment tails, plurals, word order,
                                    hidden chars, synonyms at cos>=0.95
   -> re-run until 2 dry rounds; each pass exposes defects the last could not see
C. head-noun collapse               the standard collapse rule (MIN_FANOUT)
D. emit resolution_map              bank and GT must travel the SAME transform
E. normalise the GT with that map   both sides move together
F. verification gates               all four must pass
```

**Constants that MUST be re-derived per domain** -- these are semantic lists, not
universal truths:

```
AMBIGUOUS_HEAD   depends entirely on the vocabulary; derive from the head list
KEEP_COMPOUND    which modifiers are identifying in THIS corpus
NON_OBJECT       words that never name a thing here
MIN_FANOUT       tune to the target size using the measured curve
```

COLORS / SIZE / STATE / pluralia-tantum transfer as-is.

**What is validated vs not:** the deterministic path (B, C) is what produced the
shipped bank and is fully exercised. The adversarial loop below is designed but
has NOT been run end-to-end -- on this corpus the rules settled all but one case
(`headlamp ~ headlight`), so agents had nothing to adjudicate. Reach for it when
the contested set is large, not by default.

## Run this first: the ceiling gate

Before touching a model, compute what the labels even allow:

```
ceiling = mean over rows of  min(|GT ∩ trained_vocab|, k) / |GT|
```

If the ceiling is far below 1.0, model tuning is wasted — the labels are
unreachable. One val set measured **0.49 before this procedure and 0.98 after**,
with no model change. A 67-arm architecture sweep on that set moved the score
0.2646 → 0.3259; the label cleanup moved it 0.3247 → 0.5436.

## Stage 0 — go BROAD and naive

Start permissive. Accept anything that could plausibly name a thing, including
junk. Do not filter here. Precision comes from the adversarial loop below, which
sees the whole distribution; a filter applied at extraction time cannot, and
silently deletes objects you will never know were dropped.

The naive list is the input to the loop, not the answer.

## The adversarial loop — how the final list is actually decided

Single-pass rules are not enough. Every pass over this corpus revealed defects the
previous pass had no way to see: colour prefixes surfaced first, then over-specific
compounds, then head-noun backoffs, then attribute-phrases that were never objects.
**Each fix changed what the next audit could detect.** So iterate, and make agents
argue rather than trusting one pass.

Use the Workflow tool. Roles are adversarial by construction — each one is briefed
to win its case, and only the judge commits a change.

```
SPLITTER   argues two terms are DISTINCT and must not merge.
           Owns the container-vs-contents and identifying-modifier cases.
           Must cite: training frequency of each form, and what physical thing
           differs. This is the role that saves `plastic bag` (17,847x) from
           collapsing into `bag`.

MERGER     argues terms are the SAME object and proposes a survivor.
           Must cite: cosine, both frequencies, and why the modifier is not
           identifying. Proposes head-backoffs for zero-support terms.

REJECTOR   argues a term is NOT AN OBJECT at all -- a verb, bare material,
           attribute phrase, fragment, unit or category word.
           Must name which Stage-1 class it falls in.

JUDGE      the ONLY role that commits. Rejects any proposal whose evidence is
           missing or whose target is a generic attractor word (`component`,
           `part`, `material`). Re-checks the NO_MERGE blocklist every round.
```

### Loop structure

```
round:
  1. partition the current vocabulary into N disjoint shards (by first letter,
     or by embedding cluster -- clusters surface near-duplicates in the same shard)
  2. fan out: SPLITTER + MERGER + REJECTOR run on every shard in parallel
  3. collect proposals; a term touched by >1 role is CONTESTED
  4. JUDGE rules on contested terms first, then uncontested ones
  5. apply accepted changes, recompute metrics, log every rejection with its reason
until  2 consecutive rounds produce no accepted change   (loop-until-dry, not a fixed N)
```

Do not use a fixed round count. Convergence is the signal; a counter stops early
and leaves the tail uncleaned.

### Scale the fan-out to the work

If **n new objects** fall outside the reference bank, shard so each agent sees at
most ~300 terms — beyond that, recall drops and agents start rubber-stamping.
n=3,248 new objects took ~12 shards per role. Cluster-based sharding beats
alphabetical, because it puts `yellow sock`/`gray sock`/`sock` in front of the
same agent.

### What the judge decides on

Every accepted change must improve at least one, and worsen none:

```
distinct objects        down          (a merge that adds classes is not a merge)
unreachable GT mentions down or flat
ceiling                 up or flat
NO_MERGE violations     zero
```

Recompute after each round and put the numbers in the round log. A round that
moves nothing is a signal to stop, not to try harder.

### Record rejected proposals

Log what the judge refused and why. Without it, the next run re-litigates the same
merges. Real rejections from this corpus:

```
thread -> component     `component` is an attractor; thread has 765 occurrences
lever -> sieve          cosine artifact at 0.92
perfume bottle -> perfume   container vs contents
headlamp -> headlight   worn vs vehicle-mounted
plastic bag -> bag      material is identifying; 17,847 occurrences
plastic cog -> plastic  backoff onto a bare material
```

### Why adversarial rather than a single cleaner

A single pass optimises for one failure mode and is blind to its own bias. A
merge-only agent shrinks the vocabulary until distinctions are gone; a
reject-only agent deletes rare real objects. Running them against each other and
making a judge adjudicate on measured evidence is what kept `plastic bag` while
still cutting 5,827 -> 2,244 (61%) on one val set.

## Stage 0b — pick an uncontaminated reference

Use a **train-derived** bank as the reference vocabulary. A bank built from
train+val cannot flag val's defects because it contains them by construction:
b9 (train+val) reported 3,501/3,563 val objects "in bank"; b10 (train-only)
revealed 47.5% absent, 30% of which were plain synonyms.

## Stage 1 — REJECT (not objects)

| class | examples |
|---|---|
| verbs / verb-led | `drop`, `grip`, `pick up box` — but `brush`, `hammer`, `iron`, `press` are ALSO objects; reject only when the term never names a thing |
| bare materials | `acrylic`, `ash`, `grease`, `polystyrene` — but see the two-axes rule: `paper`, `fabric`, `leather`, `glass` ARE objects here |
| descriptions | `black circular`, `round object`, `white object`, `curved wooden` |
| fragments | `fragment`, `source`, `bottom`, `component housing unit` |
| units | `gram` |
| category words | `kitchenware`, `gift set`, `platform` |
| contains ` and ` | `bolt and nut` → split or drop |

## Stage 2 — STRIP false-class modifiers

```
colour  black white red blue green yellow orange purple pink brown grey/gray silver
        gold beige transparent clear dark light navy maroon teal violet bright pale
size    small large big tiny mini little short long thin thick wide narrow tall
state   dirty clean wet dry empty full open closed used unused new old broken
        folded wrapped sliced
```

`purple/gray/orange/yellow sock` are ONE object: `sock`. Colour prefixes were
**1,750 mentions / 25% of distinct objects** in one val set.

Drop trailing fragment nouns on 3+ word terms (`part parts piece component items
section`): `angle grinder spindle nut` → `nut`.

## Stage 3 — KEEP identifying modifiers

Material/size is sometimes THE object. Test: is the compound frequent in training,
or does the modifier change what is manipulated?

```
KEEP   plastic bag (17,847×) · paper bag · plastic sheet
KEEP   perfume bottle · blister pack · water bottle   (container ≠ contents)
STRIP  yellow sock · small tray · dirty cloth
```

## Stage 4 — NORMALISE

- Singularise, excluding pluralia tantum: `scissors pliers tongs tweezers glasses
  headphones gloves chopsticks shears jeans shorts tights spectacles goggles
  binoculars clippers snips`
- Fix misspellings by **mapping, never adding a class**:
  `potatoe→potato  knive→knife  shelve→shelf  chily→chilli  leave→leaf`
- Beware the `-es/-ves` rule turning `leaves`→`leave`; it then contaminates every
  compound (`dried tea leave`, `artificial maple leave`).

## Stage 5 — MERGE near-duplicates

Cosine over SigLIP text embeddings; shortest / most frequent form survives.

```
0.95  safe      chopsticks→chopstick · potatoe→potato · bed sheet→bedsheet
0.93  usable    tweezer→tweezers · earpod→earbud · molding→mold
0.92  BREAKS    thread→component · lever→sieve · picture→component
```

`component` is a semantic attractor — inspect any merge targeting a generic word.

**NO_MERGE blocklist**, re-check every run:
```
perfume bottle↛perfume · blister pack↛blister · water bottle↛water
milk carton↛milk · juice box↛juice · paint can↛paint · glue stick↛glue
headlamp↛headlight  (worn vs vehicle-mounted)
```

## Stage 6 — HEAD-NOUN COLLAPSE

> Superseded in practice by **The standard collapse rule** above, which decides
> per head noun with a fanout threshold instead of per compound. Keep the
> principles below; use the fanout rule to apply them at scale.

Collapse a compound to its head noun when the modifier does not change the
physical thing: `accessory pouch → pouch`, `windshield wiper → wiper`,
`mechanical counter button → button`, `air fryer knob → knob`.

Decide on the NAME, never on frequency. Do not back off when the modifier is
identifying (`plastic bag`), when it is a container (`perfume bottle`), or when
the part is a distinct thing (`apple skin`, `orange peel`, `nut shell`). Never
back off onto a bare material — `plastic cog → plastic` is wrong; `→ cog`.

Applied on NAME grounds this collapsed 1,215 terms on one val set. Note the
same collapse count arrived at via a zero-support gate is a coincidence, not a
justification -- see the two-axes rule above.

**NO_MERGE additions from this family:** `apple skin↛apple`, `orange peel↛orange`,
`nut shell↛nut`, `book page↛book`.

## Always ship a resolution map

Bank and GT must travel the SAME transform. Emit `resolution_map`
(`original → final`) inside the bank JSON and have the manifest builder consult it
first. Omitting it silently dropped **12.45% of mentions and 25,410 rows** while
still reporting `ROWS_WITH_NONLITERAL: 0` — the check only sees surviving rows.

## Verification gates

```
1. every GT object resolves to a LITERAL bank name       (unresolved == 0)
2. re-resolve full manifest AND val separately            (both 0)
3. train/val overlap on row_id AND episode_id == 0
4. ceiling check (above)
```

Beware gate 3 false positives: comparing a field neither side has (`segment_id`)
intersects `{None}` with itself and reports overlap 1.

## Sizing

Bigger is not better: a 5,463-name bank beat an 11,952-name one by **5.8 points**
on identical weights. Cover what occurs, then merge hard. Expect a 40–60%
reduction end to end (5,827 → 2,244 on one val set, with the ceiling rising
throughout).
