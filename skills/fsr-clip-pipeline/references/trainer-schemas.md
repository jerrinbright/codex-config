# Trainer schemas and object extraction

## MAP (`launch_scripts/train_map_positive_unknown.py`)

```json
{"row_id": "<episode>:<index>",
 "raw_clip_path": "/clips_mc/clips/<episode>/<segment>.mp4",
 "positive_object_names": ["cloth", "box"],
 "supervision_mode": "positive_unlabeled",
 "unlisted_class_semantics": "unknown"}
```

Rows missing `supervision_mode` / `unlisted_class_semantics`, or with a
non-absolute `raw_clip_path`, are **rejected**.

**Object names must be LITERAL bank strings.** The trainer builds
`name_to_id = {name: i for i, name in enumerate(object_names)}` and raises
`KeyError: "Manifest object 'foam' is absent from the MAP bank"`. Filtering by
*canonical* membership is not sufficient -- map through
`{canon(n): n for n in object_names}` first. Only 17 of 4,572 entries differ, and
one is enough to kill the run before any GPU work.

`world_size` is hard-validated to 8 and the launcher uses `torchrun --standalone`
(single-node by definition). Multi-node needs a separate clustered launcher.

## Marlin / generative

```json
{"row_id": "...", "video": "/clips_mc/clips/<ep>/<seg>.mp4",
 "prompt": "Question: Which objects ... {\"objects\":[\"name\"]}.",
 "target": "{\"objects\":[\"cloth\"]}"}
```

Target must be **sorted with compact separators** so the model learns one
canonical serialisation.

Three things that silently destroy a generative run:

**Mask the loss to the answer span, counted from the END of the real tokens.**
A `<video>` placeholder is one token as *text* but expands to ~1,150 visual
tokens after the processor. Measuring the prompt by tokenising raw text leaves
~1,000 video positions as training targets: >99% of the loss becomes "predict the
next video token" (easy -> loss 0.16, looks like convergence) while the answer
gets almost no gradient. Generation then collapses -- 11 distinct objects across
1,500 segments, `wire`/`cable` on two thirds of them. Log `supervised_tokens`
every N steps; for short JSON answers it should read ~7-15, and raise if > 128.

**Append EOS to the supervised target**, or the model never learns to stop.

**Use `no_sync()` for gradient accumulation.** DDP all-reduces on EVERY
`backward()` otherwise, so accumulation buys nothing. With a 2.2B model across 8
nodes that is ~4.4 GB of sync against ~2.5s of compute, and 64 GPUs run SLOWER
than 8 (measured 9.6 vs 12.6 samples/s).

## Object extraction from label text

Labels are regular: `"<verb> <object> with <hand>"`, comma-separated clauses.
`"... with <tool> in <hand>"` yields TWO objects.

Assume **~37% of naively extracted terms are not objects**. Measured failure
modes, all of which need explicit handling:

- **verb leakage** (largest, ~23%): `scoop X`, `scrape X`, `iron X`, `straighten X`
- **hand references**: strip `with/in <hand>` ANYWHERE in the clause, not just at
  the end -- `cloth right hand` and `left hand and knife` leak otherwise
- **clause-initial prepositions**: `on paper`, `off tape`, `down plastic bag`
- **conjunctions**: split on `and` ONLY when a verb follows. `box and place box`
  is an artifact; `bolt and nut` and `saucer and cup` are real two-object labels
- **stranded adjectives**: `electronic`, `dried`
- **generic heads**: bare `object`, `component`, `part`, `piece`

Junk rises sharply as frequency falls -- 18% of terms at high counts, **49% at
count 3**. A `>= 5` occurrence threshold removes most of it.

### Reviewing a vocabulary

Classify with independent agents, then run an **adversarial second round** on
low-confidence and disputed terms, arguing the opposite of round one. That round
overturned 13.8% of calls, and only it caught:

- misspellings hiding real objects: `clever`->cleaver, `lable`->label, `pilers`->pliers
- real tools whose names are verbs: `clothing iron`, `drill bit`, `wire stripper`
- real products reading as verb phrases: `squeeze bottle`, `zip bag`, `release liner`
- `chair`/`drawer` are manipulated objects, not locations, when every attached
  verb is work (grip, brush, dust off) and no `on chair` placement form exists

The strongest evidence is **corpus statistics, not intuition**: check whether bare
verbs or adjectives ever strand in the vocabulary (`scrape` 3, `sweep` 0, `pink`
0). If they never do, a high-count bare term is a real noun.

## MAP bank expansion

Nothing in the MAP head is sized by object count -- all 13 tensors are shaped by
the 1152-d embedding dim. Expansion adds ROWS, not head outputs.

- **carry `map_state_dict` forward verbatim.** `reset_parameters()` seeds the pool
  then `load_pretrained_bank()` overwrites it FROM THE BANK FILE. Training
  overrides it again from the overlay, so a bank rebuilt without it is invisible
  in training and destructive at eval.
- **embed with `padding="max_length", max_length=64`.** Re-embedding known names
  reproduces stored rows at cosine **0.99989**; `padding="longest"` gives **0.653**
  and raises nothing. Gate on reproducing known rows before writing.
- rows are unit-normalised; raw SigLIP text features have norm ~34
- dedup on `normalize_map_object_name` (the loader hard-fails on duplicates),
  while supervision matching uses the semantic canonicaliser
