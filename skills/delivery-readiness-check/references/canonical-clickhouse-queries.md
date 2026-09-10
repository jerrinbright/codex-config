# Canonical ClickHouse Queries for Delivery Readiness

Verbatim from `mecka-ai/mecka-ai-studio` `apps/delivery/src/server/analytics/clickhouse/delivery-reverify.ts` at commit 2026-08-31. Table constants from `packages/delivery-pipeline-shared/src/sql.ts`.

```
DELIVERY_EVENT_TABLE = "stats.delivery_event_fact_current"
STRICT_READY_TABLE   = "stats.strict_ready_episode_current"
EPISODE_FACT_TABLE   = "stats.episode_fact_current"
```

## 1. Delivery + Exclusivity (`getEpisodeDeliveryStates`)

Canonical **exclusive-wins** rule. Any exclusive delivery on any date wins over any non-exclusive delivery.

```sql
SELECT
  episode_id_string,
  toUInt8(max(coalesce(is_exclusive, 0))) AS any_exclusive,
  toUInt8(max(if(is_exclusive IS NULL, 1, 0))) AS any_unknown
FROM stats.delivery_event_fact_current FINAL
WHERE is_deleted = 0
  AND episode_id_string IN (...ids...)
GROUP BY episode_id_string
```

Bucketing (from the app's `EpisodeDeliveryState` type):
- Row returned AND `any_exclusive == 1` → **exclusive** (re-delivery is a hard conflict).
- Row returned AND `any_exclusive == 0` AND `any_unknown == 1` → **unknownExclusive** (delivered with no exclusivity verdict; fail-closed = treat as exclusive).
- Row returned AND neither above → **delivered / OTS overlap** (informational).
- Id absent from result → **notDelivered**.

Fail-closed guard: call `deliveryFactPopulatedRows()` first. If 0 rows and `STATS_ALLOW_EMPTY_DELIVERABLE != "1"`, throw — never silently return "nothing exclusive."

### Batch size: whole request in ONE query

`delivery_event_fact_current` is `ORDER BY delivery_id_string`. An `episode_id_string IN (...)` predicate CANNOT prune. Every query is a full scan (~80-90M rows, ~5 GiB). Measured 2026-08-20 on the 179,083-id operator list:

| batch | queries | rows read | bytes | wall |
|---|---:|---:|---:|---:|
| 20,000 | 9 | 828,928,035 | 49.4 GiB | 7.6 s |
| 45,000 | 4 | 368,412,460 | 22.0 GiB | 4.0 s |
| 179,083 | 1 | 92,103,115 | 5.5 GiB | 2.3 s |

Perfectly linear in query count. Send everything up to `EPISODE_PREDICATE_MAX_IDS = UNIVERSAL_GATE_CHECK_MAX = 50,000` in ONE query. Beyond 50k, chunk at 50k. Real ceiling is `max_query_size` (4 MiB after `buildUrl` bump → ~155,000 ids).

## 2. Strict-Ready (currently deliverable) (`verifyEpisodesStrictReady`)

```sql
SELECT episode_id_string
FROM stats.strict_ready_episode_current
WHERE snapshot_version = <pinned snapshotVersion>
  AND is_strict_ready = 1
  AND episode_id_string IN (...ids...)
  -- + appended ban/attribution clause from shipGateAttributionClause()
```

Present → still deliverable. Missing → dropped since pick (ban landed, PII gate flipped, quality regressed, etc.).

### Batch size: `ID_CHUNK = 20,000`

This table DOES prune on `episode_id_string`. Chunk at 20k.

### Snapshot pinning

`pinDeliverableSnapshot()` reads the current `snapshot_version` once at the start of a run and reuses it across every chunk — so a mid-flight fact-sync refresh cannot split verification across two snapshots. `ALLOW_EMPTY + empty snapshot ⇒ snapshotVersion null ⇒ every id is "missing"`.

## 3. Rejection Since Pick (`verifyEpisodesNotRejected`)

```sql
SELECT episode_id_string
FROM stats.episode_fact_current FINAL
WHERE is_deleted = 0
  AND episode_id_string IN (...ids...)
  AND (
    upper(status) = 'REJECTED' OR
    upper(human_status) = 'REJECTED' OR
    upper(automated_qa_status) = 'REJECTED'
  )
```

`episode_fact_current` syncs at fast (~1min) incremental cadence — much fresher than `strict_ready_episode_current` (~4h throttled fullRefresh) — so this catches a rejection that landed inside the strict-ready staleness window.

### Batch size: `ID_CHUNK = 20,000`

## Concurrency

`STATS_CLICKHOUSE_MAX_CONCURRENCY=1` — one query at a time. Concurrent passes only stretch each other's wall clock (ADR-0001).

## Full Runner Skeleton

```python
import os, requests, time
CH_URL = os.environ["STATS_CLICKHOUSE_URL"]     # e.g. https://<host>:<port>/?database=stats
CH_AUTH = (os.environ["STATS_CLICKHOUSE_USER"], os.environ["STATS_CLICKHOUSE_PASSWORD"])
CH_HEADERS = {"Content-Type": "text/plain"}     # ClickHouse expects SQL in POST body

UNIVERSAL_GATE_CHECK_MAX = 50_000
ID_CHUNK = 20_000

def _run(sql: str) -> list[dict]:
    r = requests.post(
        f"{CH_URL}&default_format=JSONEachRow&max_query_size={4*1024*1024}",
        data=sql.encode("utf-8"),
        auth=CH_AUTH, headers=CH_HEADERS, timeout=180,
    )
    r.raise_for_status()
    return [__import__("json").loads(l) for l in r.text.splitlines() if l.strip()]

def _ids_sql(ids):
    return ",".join(f"'{i}'" for i in ids)

def delivery_states(episode_ids: list[str]) -> dict:
    """Returns { id: {"delivered": bool, "exclusive": bool, "unknownExclusive": bool} }."""
    result = {i: {"delivered": False, "exclusive": False, "unknownExclusive": False} for i in episode_ids}
    # NOT chunked at ID_CHUNK — one query per gate-batch (up to 50k).
    for i in range(0, len(episode_ids), UNIVERSAL_GATE_CHECK_MAX):
        batch = episode_ids[i:i+UNIVERSAL_GATE_CHECK_MAX]
        rows = _run(f"""
SELECT
  episode_id_string,
  toUInt8(max(coalesce(is_exclusive, 0))) AS any_exclusive,
  toUInt8(max(if(is_exclusive IS NULL, 1, 0))) AS any_unknown
FROM stats.delivery_event_fact_current FINAL
WHERE is_deleted = 0
  AND episode_id_string IN ({_ids_sql(batch)})
GROUP BY episode_id_string""")
        for r in rows:
            excl = int(r["any_exclusive"]) == 1
            result[r["episode_id_string"]] = {
                "delivered": True,
                "exclusive": excl,
                "unknownExclusive": (not excl) and int(r.get("any_unknown", 0)) == 1,
            }
    return result

def strict_ready(episode_ids: list[str], snapshot_version: int) -> set[str]:
    present = set()
    for i in range(0, len(episode_ids), ID_CHUNK):
        batch = episode_ids[i:i+ID_CHUNK]
        rows = _run(f"""
SELECT episode_id_string
FROM stats.strict_ready_episode_current
WHERE snapshot_version = {snapshot_version}
  AND is_strict_ready = 1
  AND episode_id_string IN ({_ids_sql(batch)})""")
        present.update(r["episode_id_string"] for r in rows)
    return present

def rejected(episode_ids: list[str]) -> set[str]:
    bad = set()
    for i in range(0, len(episode_ids), ID_CHUNK):
        batch = episode_ids[i:i+ID_CHUNK]
        rows = _run(f"""
SELECT episode_id_string
FROM stats.episode_fact_current FINAL
WHERE is_deleted = 0
  AND episode_id_string IN ({_ids_sql(batch)})
  AND (
    upper(status) = 'REJECTED' OR
    upper(human_status) = 'REJECTED' OR
    upper(automated_qa_status) = 'REJECTED'
  )""")
        bad.update(r["episode_id_string"] for r in rows)
    return bad
```

## Also See

- `apps/delivery/src/server/delivery/qa-check.ts` — full orchestration with business bans, user bans, banned tasks, autoQA provenance (THOROUGH mode).
- `apps/delivery/src/server/delivery/qa-check-run.ts` — 50k-pass loop, sort-for-contiguity trick, why chunking `delivery_event_fact_current` is a footgun.
- `docs/DELIVERY_PLAYBOOK.md` — the three-check invariant, `--partner` semantics, when to FAST vs THOROUGH.
- `docs/adr/0001-qa-check-runs-detached-not-parallel.md` — concurrency budget = 1.
- `docs/adr/0004-…` (referenced in delivery README) — soft-rejected verdicts.
