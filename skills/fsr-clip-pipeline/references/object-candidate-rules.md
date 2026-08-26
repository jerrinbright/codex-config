# What counts as an object candidate

A reusable decision procedure for turning raw extracted terms into a bank, or for
auditing an existing bank / GT set. Every rule below was forced by a measured
failure; the numbers are from the multicam corpus (354k segments, Aug 2026).

Run it on any bucket of object strings: bank candidates, val GT, a new pull's
vocabulary. It is order-dependent — apply the stages top to bottom.

---

## Stage 0 — the reference vocabulary

Pick the reference bank BEFORE auditing, and make sure it is not contaminated.

**Use a TRAIN-DERIVED bank as the reference.** A bank built from train+val cannot
flag val's defects, because it contains them by construction. This cost a whole
audit pass: b9 (11,425, train+val) reported 3,501/3,563 val objects "in bank",
while b10 (8,367, train-only) revealed 47.5% were absent — and 30% of those were
plain synonyms of things already in the bank.

---

## Stage 1 — REJECT outright (not objects)

| class | examples | why |
|---|---|---|
| verbs / verb-led phrases | `drop`, `grip`, `pick up box` | parser leakage; ~37% of raw extracted terms |
| bare materials | `acrylic`, `ash`, `dust`, `grease`, `polystyrene`, `linen` | a substance, not a manipulable object |
| pure descriptions | `black circular`, `round object`, `white object`, `green`, `curved wooden` | attributes with no head noun |
| fragments | `fragment`, `source`, `bottom`, `excess trim`, `component housing unit` | not a nameable thing |
| units | `gram` | measurement |
| category words | `kitchenware`, `gift`, `gift set`, `platform` | too generic to be a prediction target |
| anything containing ` and ` | `bolt and nut` | two objects; split or drop |

## Stage 2 — STRIP modifiers that create false classes

Applied left to right, repeatedly, while the remainder is still multi-word:

```
colour   black white red blue green yellow orange purple pink brown grey/gray
         silver gold beige transparent clear dark light navy maroon teal violet
         multicolored bright pale
size     small large big tiny mini little short long thin thick wide narrow tall
state    dirty clean wet dry empty full open closed used unused new old broken
         folded wrapped sliced
```

`purple sock`, `gray sock`, `orange sock`, `yellow sock` are ONE object: `sock`.
Colour prefixes alone were **1,750 mentions / 25% of distinct objects** in one val
set, and stripping them lifted its achievable ceiling from 0.49 to 0.79.

Also drop trailing fragment nouns on 3+ word terms:
`part parts piece pieces component components item items section`
→ `angle grinder spindle nut` is a `nut`.

## Stage 3 — KEEP identifying modifiers (do NOT over-strip)

Material/size is sometimes **the** object. Strip it only when the compound is not
itself a distinct, well-attested thing.

```
KEEP    plastic bag (17,847 occurrences)  paper bag   plastic sheet
KEEP    perfume bottle   blister pack   paint can   water bottle
        (a container is not its contents)
STRIP   yellow sock   small tray   dirty cloth
```

Test: is the compound frequent in training, or does the modifier change what is
being manipulated? If yes, keep it.

## Stage 4 — NORMALISE form

- Singularise, with a pluralia-tantum exception list:
  `scissors pliers tongs tweezers glasses headphones gloves chopsticks shears
   jeans shorts tights spectacles goggles binoculars clippers snips`
- Fix misspellings by **mapping, never by adding a new class**:
  `potatoe→potato  knive→knife  shelve→shelf  chily→chilli  leave→leaf`
- Watch the `-es`/`-ves` singulariser: it turns `leaves` into `leave`, which then
  contaminates every compound (`dried tea leave`, `artificial maple leave`).

## Stage 5 — MERGE near-duplicates

Cosine over SigLIP text embeddings of the bank prompt, **shortest / most frequent
form survives**.

```
threshold   0.95   safe: chopsticks→chopstick, potatoe→potato, bed sheet→bedsheet
            0.93   still mostly safe: tweezer→tweezers, earpod→earbud, molding→mold
            0.92   TOO LOOSE: thread→component, lever→sieve, picture→component
```

`component` acts as a semantic attractor — inspect any merge whose target is a
generic word.

**NO_MERGE blocklist** (container vs contents, and homographs). Re-check this list
every run; it is not optional:

```
perfume bottle↛perfume   blister pack↛blister   water bottle↛water
milk carton↛milk   juice box↛juice   paint can↛paint   glue stick↛glue
headlamp↛headlight   (worn vs vehicle-mounted)
```

## Stage 6 — HEAD-BACKOFF, but only for zero-support terms

For a term with **no training support**, back off to the head noun if that head is
a trained object: `accessory pouch → pouch`, `windshield wiper → wiper`,
`mechanical counter button → button`. This is free — no model could have learned
the long form — and it converts an unreachable label into a reachable one.

Never back off a term that HAS training support: that destroys a real distinction.
Never back off onto a bare material: `plastic cog → plastic` is wrong; `→ cog`.

On one val set this collapsed 1,215 terms and cut unreachable mentions from 14.5%
to 1.9%.

---

## Always emit a resolution map

The bank and the GT must travel the same transform. Ship `resolution_map`
(`original surface form → final bank entry`) inside the bank JSON, and have the
manifest builder consult it before its own ladder. Skipping this silently dropped
**12.45% of object mentions and 25,410 rows** while still reporting
`ROWS_WITH_NONLITERAL: 0`, because the check only inspects surviving rows.

## Verification gates — run all four

```
1. every GT object resolves to a LITERAL bank name        (unresolved == 0)
2. re-resolve the full manifest and the val set separately (both 0)
3. train/val overlap on row_id AND episode_id == 0
4. ceiling check: max achievable r@10 given the vocabulary
       ceiling = mean over rows of min(|GT ∩ trained|, k) / |GT|
```

Gate 4 is the one people skip. If the ceiling is far below 1.0, tuning the model
is wasted effort — the labels are unreachable, and the fix is vocabulary or data,
not architecture. A val set measured 0.49 before this procedure and 0.98 after,
with no change to any model.

## Sizing

Bigger is not better. A 5,463-name bank beat an 11,952-name one by 5.8 points on
identical weights. Prefer full coverage of what actually occurs, then merge hard.
Expect a well-built bucket to shrink 40–60% end to end (5,827 → 2,244 on one val
set, 61% reduction, with the ceiling rising the whole way).
