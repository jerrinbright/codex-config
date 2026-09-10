---
name: delivery-readiness-check
description: Verify whether a candidate episode list is safe to ship — currently deliverable (strict-ready), not exclusively delivered to a partner, not rejected since pick, and free of banned businesses/users/tasks. Use when the user asks about delivery readiness, exclusivity, shipping a candidate list, "is this list clean", QA gates, dedup against prior deliveries, `delivered.isExclusive`, `is_strict_ready`, cross-client conflict, `delivery-suite/qa-check`, or wants to know how many of a set are already delivered. Mirrors the checks the hosted `delivery.mecka.ai/delivery-suite/qa-check` page runs, plus the `~/.claude/skills/qa-check/qa_check.py` skill twin.
---

# Delivery Readiness Check

## Core Rule (from `docs/DELIVERY_PLAYBOOK.md`)

For any candidate list, always run three checks:

1. **QA approved** — episode is not currently `REJECTED` in `episode_fact_current`.
2. **`delivered.isExclusive != true`** — episode is not already exclusively delivered.
3. **`delivered_to != <this client>`** — episode has not already been delivered to the target partner.

Never trust a single source of truth without cross-checking. Do NOT use ClickHouse `delivery_fact_current` to decide "was this delivered" — historical measurements found both stale-deleted and missing-delivered rows. The delivery-safe answer combines the ClickHouse `delivery_event_fact_current` fact with a MongoDB `delivered` probe.

Fail closed: if the delivery fact / snapshot is empty or absent, RAISE — never silently report "nothing to exclude." The only override is `STATS_ALLOW_EMPTY_DELIVERABLE=1` (dev only).

## Signals At A Glance

| gate | source of truth | field | fail-closed? |
|---|---|---|---|
| Currently deliverable | ClickHouse `stats.strict_ready_episode_current` | `is_strict_ready = 1` in the latest `snapshot_version` | yes |
| Rejected since pick | ClickHouse `stats.episode_fact_current` FINAL | `upper(status) = 'REJECTED'` OR `upper(human_status) = 'REJECTED'` OR `upper(automated_qa_status) = 'REJECTED'` | no |
| Delivered / Exclusive | ClickHouse `stats.delivery_event_fact_current` FINAL | canonical: `toUInt8(max(coalesce(is_exclusive, 0)))` GROUP BY `episode_id_string`, filtered by `is_deleted = 0` | yes |
| Delivered / Exclusive (Mongo cross-check) | MongoDB `delivered` | `episode_id` (stored MIXED — probe both `ObjectId` and string forms in one `$in`), `isExclusive`, `delivered_to` | no |
| Banned businesses / tasks / users | ClickHouse (via `apps/delivery/src/server/delivery/qa-check.ts`) | strict-ready `banned = 1` rows + fleet reference lists | yes (contractual) |

## Canonical ClickHouse Queries (verbatim from the hosted app)

Copy from [references/canonical-clickhouse-queries.md](references/canonical-clickhouse-queries.md). Source files in `mecka-ai/mecka-ai-studio`:
- `apps/delivery/src/server/analytics/clickhouse/delivery-reverify.ts` — `getEpisodeDeliveryStates`, `verifyEpisodesStrictReady`, `verifyEpisodesNotRejected`.
- `apps/delivery/src/server/delivery/qa-check.ts` — full `checkDeliveryQaBatch` orchestration (bans, autoQA, exclusivity).

Table names (`packages/delivery-pipeline-shared/src/sql.ts`):
- `stats.delivery_event_fact_current`
- `stats.strict_ready_episode_current`
- `stats.episode_fact_current`

## Canonical Mongo Cross-Check

`delivered.episode_id` is stored MIXED (`ObjectId` AND string) — probe both forms in one indexed `$in`, hint the destination index:

```python
from bson import ObjectId
keys = []
for e in episode_ids:
    if len(e) == 24: keys.append(ObjectId(e))
    keys.append(e)
db.delivered.find(
    {"episode_id": {"$in": keys}},
    {"_id": 0, "episode_id": 1, "delivered_to": 1, "isExclusive": 1, "timestamp": 1, "tags": 1},
).hint("delivered_episode_destination_idx")
```

Delivery source of truth is MongoDB `delivered` (per `mongo-episode-query-discovery` skill's `references/query-performance.md`, "Delivery Source Of Truth"). Do NOT use ClickHouse `delivery_fact_current` for this decision.

## Workflow

1. **Confirm scope.** Ask the user which candidate id file to check and which partner (`--partner <client>`) matters for the cross-client conflict gate. Without partner context, produce only `exclusive` / `unknown_exclusive` / `not_deliverable` / `rejected`.

2. **Prefer the Python skill twin when installed.** If `~/.claude/skills/qa-check/qa_check.py` exists, run it — it is the shipping-authority implementation and is more complete than the hosted UI (hosted lacks banned businesses/tasks/users, CV pass, `isExclusive`, not-in-delivered per Linear SWE-152 as of 2026-08-13):

   ```
   python3 ~/.claude/skills/qa-check/qa_check.py <eids.txt> \
     [--fast | --thorough] \
     [--partner <client>] \
     [--mono] [--hands-min 95] [--rep-max 0.95] \
     [--env-id home] [--banned ...] [--env .env]
   ```

   Writes `<base>_qa_clean.txt`, `<base>_qa_removed.txt`, and a per-gate hours table. Use FAST to vet a parent pool BEFORE picking; use THOROUGH on the final list AT SHIP.

3. **If the skill is absent** — fall back to running the three canonical ClickHouse queries yourself (see `references/canonical-clickhouse-queries.md`) plus the Mongo cross-check. ClickHouse creds live in `STATS_CLICKHOUSE_URL` / auth headers, concurrency budget is 1 (`STATS_CLICKHOUSE_MAX_CONCURRENCY=1`), do not parallelize.

4. **Batch sizes matter.**
   - `stats.delivery_event_fact_current` is `ORDER BY delivery_id_string` — an episode predicate CANNOT prune. **Send ONE query with all ids up to `UNIVERSAL_GATE_CHECK_MAX = 50,000`** (chunking multiplies work rather than dividing it). See `delivery-reverify.ts:EPISODE_PREDICATE_MAX_IDS` and the measured table in its header comment.
   - `stats.strict_ready_episode_current` DOES prune on `episode_id_string` — chunk at `ID_CHUNK = 20,000`.
   - `stats.episode_fact_current` — chunk at `ID_CHUNK = 20,000`.

5. **Report the four buckets separately** (never fold them together — the operator has to be able to see each):
   - `exclusiveConflicts` — `state.exclusive == true` (re-delivery is a hard conflict).
   - `unknownExclusivity` — delivered with no recorded exclusivity verdict (`any_unknown == 1`, fail-closed = treated as exclusive).
   - `deliveredOverlap` (OTS) — delivered non-exclusively (informational).
   - `notDelivered` — absent from the delivery fact.
   Plus `notStrictReady` (dropped since pick) and `rejected` (QA state now REJECTED).

6. **Bulk-run telemetry.** Log count, elapsed time, and throughput per query (`{count:,} rows in {elapsed:.1f}s = {count/elapsed:,.0f} eps/s`). If `delivery_event_fact_current` returns notably fewer rows than the ~80-90M full-scan baseline, verify the query — you might have accidentally chunked.

## Silent-Wrong-Answer Traps

- **Query only the ClickHouse fact, skip the Mongo probe** → misses records the ClickHouse mirror is missing / lags on. Always cross-check.
- **Probe only ObjectId OR only string on `delivered.episode_id`** → silently misses half the collection. One `$in` with BOTH forms.
- **Chunk `delivery_event_fact_current` at 20,000** → 20x the rows read for the same answer. Send the whole batch (up to 50k) in one query.
- **Trust `tierSnapshots.delivery.handedness.segments` non-empty as "delivered"** → it is a labeling-pipeline snapshot, not a delivery record. It coexists with un-delivered episodes.
- **Trust the hosted `delivery-suite/qa-check` UI as complete** → it drifts from the Python skill (SWE-152). Hosted was missing banned businesses/tasks/users, CV pass, `isExclusive`, not-in-delivered as of 2026-08-13. If reproducibility matters, run the skill.
- **Report "approved" as license-safe** → QA approval is only one of the three checks. Also verify `isExclusive != true` and `delivered_to != <partner>`.
- **Case-insensitive destination regex** in `delivered_to` → absorbs neighboring destinations. Use explicit `{"delivered_to": {"$in": [...]}}`.

## Related Skills

- [[mongo-episode-query-discovery]] — general query patterns, BSON gotchas, index catalog.

## When Called

Trigger phrases include: "is this list clean", "check delivery readiness", "exclusivity check", "already delivered", "shipping this candidate list", "cross-client conflict", "QA gate", "delivery-suite/qa-check", "isExclusive", "strict-ready", "safe to ship", "vet a parent pool", "final ship check".
