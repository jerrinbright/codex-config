# Objects and vocabulary

Everything here comes from a run that produced wrong numbers. Objects are parsed
out of free-text action labels, so the parser is the data pipeline -- treat its
output as untrusted until reviewed.

## The parser leaks verbs, and it leaks DIFFERENTLY on every pull

`LEADING_VERBS` in `fsr_objects_and_merge.py` is a fixed list. Any verb missing
from it survives into the "objects" field as a verb phrase.

Measured on pull6 (first pull containing non-first segments):

    sweep floor    1,286      mop floor   1,081      dispense liquid  648
    draw liquid      638      shape dough   483      wring cloth      281

Those were the SIX MOST FREQUENT "new objects" in the pull. 34% of the pull's
new vocabulary was actions -- against 6.5% on the previous pull, because a new
label distribution uses verbs the list never saw.

**Before extracting a new pull, diff its label verbs against `LEADING_VERBS`.**
Take the first token of every clause and list the ones not covered. Adding them
costs nothing; skipping it costs a 20-agent review to clean up afterwards.

## The counting trap: raw distinct terms are ~4x the real object count

pull6, step by step:

    12,252   raw terms not in the bank
     6,124   after agent review removed verbs and fragments      -34%
     4,889   after removing synonyms and plural/canonical dupes  -20%
     3,745   after generalising material/size/state modifiers    -23%
     3,248   after removing near-duplicates (cos >= 0.92)        -13%

Quote the final number, never the first. Reporting "12,252 new objects" and then
walking it down four times is worse than measuring once.

## Review procedure

Shard the unreviewed terms (exclude anything already judged in a prior pass --
persist verdicts per pull) and run ~500 terms per agent with:

- the term, its corpus count, and TWO example labels it was extracted from
- explicit reject classes: verb phrases, bare verbs, bare adjectives, dangling
  prepositions, body parts, pure locations
- explicit accept: any visually groundable thing however rare or specific,
  manipulated materials, colour/material compounds, generic role classes
- a `malformed` verdict with a `suggested` fix for repairable parser damage
- the test: "could you draw a box around it in a frame?"

Rarity is NOT grounds for rejection -- say so, or agents silently drop the tail.

Rejection rates vary 0.5%-45% ACROSS BATCHES of the same shuffled list. The
boundary is noisy; a term's verdict depends partly on which agent saw it. Do not
present the aggregate as precise.

## Deduplication, in this order

1. exact after whitespace/case normalisation
2. plural and `canonicalize_map_object_class_name` collapse
3. embedding cosine >= 0.92 against the EXISTING bank -> drop the new entry,
   the bank keeps the general form
4. embedding cosine >= 0.92 within the new set -> keep the SHORTEST member
5. drop leading-conjunction corruption (`and bag`, `and metal component`) --
   the `and`-split eats the first letter

Bands, calibrated on real pairs:

    >=0.95   pure duplicates      rubber bands / rubber band
    0.92-95  synonyms             aloe vera plant / aloe vera, adapter plug / adapter
    0.90-92  MIXED                air fryer grill / air fryer is a PART, not a synonym
    0.85-90  different objects    postcard / pamphlet, radial arm saw / table saw

Never merge below 0.92 without inspecting. Three separate embedding merges in one
session removed real objects at lower thresholds.

## What NOT to collapse

Nested entries (`adjustable wrench` under `wrench`, `bench vice handle` under
`handle`) are DISTINCT OBJECTS. Collapsing to head nouns scores 42% board recall
versus 74% for the full vocabulary -- it was independently refuted by another
team's `mcu23` arm at 66.50 vs 75.77.

Generalisations that are safe, because they strip a modifier that does not change
what the object IS: leading material, size/shape adjective, state participle,
trailing assembly/set/kit, `part|piece|element` -> `component`, `of X` phrase.

## Coverage metrics: apply rules to ONE side, not both

Applying the same canonicalisation to predictions AND ground truth reports 99.97%
for a vocabulary that scores 67% under the board's literal matching -- and it
endorses head-noun collapse at 99.99%, which actually scores 42%.

**Always measure the way the consumer matches.** If the scorer is literal, keep
ground truth raw. A 37-run sweep was ranked on the both-sides metric and every
absolute number was inflated by ~46 points.

## Audit the existing bank too, not just the new terms

b4 (5,463 entries), used all session as the "clean" reference, contains **1,451
internal duplicate pairs** at cos >= 0.92:

    baking pan / baking tin / baking tray / baking sheet
    baby cap / baby hat        bag strap / handbag strap

Every duplicate competes for the same top-10 slot. Run the dedup audit on the
bank you are merging INTO, not only on what you are adding.

## Bank size is a measured tradeoff, not a preference

    b4   5,463 entries    multicam 71.83   multicam6k 33.30
    b6  11,952 entries    multicam 66.01   multicam6k 31.88

Identical weights, only the vocabulary differs. Doubling the bank cost 5.8 points
because poorly-supported entries outrank correct ones. Coverage raises the
ceiling and lowers the realised score.

MAP's head is embedding-dim shaped, so a bank swap needs NO retraining -- A/B the
candidate banks against the board instead of arguing about size. A classifier
probe (V-JEPA) is the opposite: the class list is the output layer, so changing
it forces a full retrain.

## Transforming the bank transforms the GT — ship a resolution map

Every rule that reshapes a bank name (plural stripping, `of X` tails, cosine
dedup) breaks the manifests, because the ground truth still carries the original
surface form. The manifest resolver's ladder (exact → casefold → singular →
canon) has no step that undoes a merge, so `tape roll` resolves to nothing and
its row is dropped **silently** — the builder still reports
`ROWS_WITH_NONLITERAL: 0`, because it only checks the rows that survived.

Measured on a 314,009-row manifest after generalising materials/sizes/states:
**12.45% of object mentions and 25,410 rows (8.09%) vanished.** `plastic bag`
alone was 17,847 mentions, collapsed into `bag`.

So:

1. **The bank build emits `resolution_map`** — every `original surface form →
   final bank entry` hop, both the generalisation and the dedup, chained to the
   final survivor and filtered to entries that actually exist in `object_names`.
2. **The manifest resolver consults it first**, right after the literal check.
3. **Verify by re-resolving, not by trusting the builder.** Count unresolved
   mentions across the whole manifest and across the val set. Both must be 0.

## Do not generalise an identifying modifier

Material, size and state are sometimes the object. `plastic bag` is a distinct
thing from `bag` and is one of the most common objects in the corpus; stripping
its material destroys more than it saves. Strip plurals and `of X` tails; leave
the rest of the surface form alone.

Cosine dedup also merges containers into their contents — `perfume bottle →
perfume`, `blister pack → blister`, `paint can → paint`. The container is what
the hand manipulates. Keep an explicit `NO_MERGE` blocklist and add to it every
time a review surfaces one; `headlamp → headlight` (worn vs vehicle-mounted) came
from exactly that.

## Build the bank from train AND val

The val vocabulary is not a subset of the training vocabulary — a rare-weighted
val set is chosen for the opposite property. Of 6,437 val rows, 1,979 distinct
objects existed in no training-derived source, leaving 489 rows with no
resolvable GT at all. Out-of-bank GT measures **0.06% recall**, so those rows
are not hard, they are unscoreable, and they drag the metric down uniformly.
Feed b_prev + new-pull + val through the same transform in one pass.
