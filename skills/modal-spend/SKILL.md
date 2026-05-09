---
name: modal-spend
description: "Pull Modal workspace spend for a rolling 7-day or user-specified window and break it down by environment and deployed app, with extra detail for the jerrin environment. Use when the user asks how much Modal spend was, wants jerrin/top-app cost stats, a per-env or per-app breakdown, or spend-spike investigation."
---

# Modal spend breakdown

Use the `modal billing report` CLI to fetch line-item spend, then aggregate by `Environment` and by `Description` (the app name).

## Required tools
- `modal` CLI (`modal --version` to confirm; v1.4+ has `billing report`)
- `python3` for aggregation

## Choosing the window
Map the user's phrasing to a `modal billing report` flag:
- Default / "last week" / "past week" / "this past week" / "last 7 days" / "rolling week" → compute exact rolling 7-day dates from today and use `--start YYYY-MM-DD --end YYYY-MM-DD`.
- "this week" / "week so far" → `--for "this week"`
- "yesterday", "today", "last month", "this month" → `--for "<phrase>"`
- Specific dates → `--start YYYY-MM-DD --end YYYY-MM-DD` (start inclusive, end exclusive)

If ambiguous, prefer exact rolling 7 days ending today, not Modal's calendar `--for "last week"`.
State the resolved start/end dates in the answer. Remember `--end` is exclusive; for "last 7 days through today", use tomorrow as the exclusive end date if today's partial day should be included.

## Command

```bash
START=$(date -d '7 days ago' +%F)
END=$(date -d 'tomorrow' +%F)
modal billing report --start "$START" --end "$END" --json > /tmp/modal_spend.json
```

Each row has shape:
```json
{
  "Object ID": "ap-...",
  "Description": "<app name>",
  "Environment": "<env>",
  "Interval Start": "YYYY-MM-DDT00:00:00",
  "Cost": "<decimal string>"
}
```

## Aggregation script

```bash
python3 - <<'PY'
import json
from collections import defaultdict
rows = json.load(open('/tmp/modal_spend.json'))
if not rows:
    print("no rows"); raise SystemExit
starts = sorted({r["Interval Start"][:10] for r in rows})
print(f"Range covered: {starts[0]} → {starts[-1]}  ({len(rows)} rows)\n")

per_env = defaultdict(float)
per_app = defaultdict(float)             # (env, app) -> cost
per_day = defaultdict(float)             # date -> cost
per_env_day = defaultdict(float)         # (env, date) -> cost
per_app_day = defaultdict(float)         # (env, app, date) -> cost
for r in rows:
    env = r["Environment"]
    app = r["Description"]
    day = r["Interval Start"][:10]
    cost = float(r["Cost"])
    per_env[env] += cost
    per_app[(env, app)] += cost
    per_day[day] += cost
    per_env_day[(env, day)] += cost
    per_app_day[(env, app, day)] += cost

total = sum(per_env.values())
jerrin_total = per_env.get("jerrin", 0.0)
print(f"TOTAL: ${total:,.2f}")
print(f"JERRIN TOTAL: ${jerrin_total:,.2f} ({(jerrin_total / total * 100) if total else 0:.1f}% of workspace)\n")

print("Per environment:")
for env, c in sorted(per_env.items(), key=lambda x: -x[1]):
    print(f"  {env:<20} ${c:>10,.2f}")

print("\nJerrin daily spend:")
for day in sorted(per_day):
    c = per_env_day.get(("jerrin", day), 0.0)
    print(f"  {day:<12} ${c:>10,.2f}")

jerrin_apps = [((env, app), c) for (env, app), c in per_app.items() if env == "jerrin"]
jerrin_apps.sort(key=lambda x: -x[1])
print("\nTop 10 jerrin apps:")
for i, ((env, app), c) in enumerate(jerrin_apps[:10], 1):
    days_active = sum(1 for day in starts if per_app_day.get((env, app, day), 0.0) > 0)
    peak_day, peak_cost = max(
        ((day, per_app_day.get((env, app, day), 0.0)) for day in starts),
        key=lambda x: x[1],
    )
    pct = (c / jerrin_total * 100) if jerrin_total else 0.0
    print(f"  {i:>2}. {app:<50} ${c:>10,.2f}  {pct:>5.1f}%  active_days={days_active}  peak={peak_day} ${peak_cost:,.2f}")

if len(jerrin_apps) > 10:
    tail = sum(c for _, c in jerrin_apps[10:])
    print(f"  +{len(jerrin_apps) - 10} more jerrin apps: ${tail:,.2f}")

print("\nTop apps across all envs:")
for i, ((env, app), c) in enumerate(sorted(per_app.items(), key=lambda x: -x[1])[:10], 1):
    print(f"  {i:>2}. {env:<10} {app:<50} ${c:>10,.2f}")

tiny = sum(c for c in per_app.values() if c < 0.01)
if tiny:
    print(f"  (omitted ${tiny:.4f} from apps under $0.01)")
PY
```

## Reporting back to the user
- Lead with the resolved date range and grand total.
- Show env totals as a small table (sorted descending).
- Always include a jerrin-focused section when jerrin appears:
  - jerrin total and percent of workspace total
  - top 10 jerrin apps by spend
  - each top app's percent of jerrin spend, active days, and peak spend day
  - jerrin daily spend for the window
- For per-app, group by env and show top apps; truncate the long tail.
- Include workspace-wide top 10 apps after the jerrin section when useful.
- Call out anything that looks anomalous (one app dominating an env, a new app, a 10x jump vs. prior week if the user asks).

## Variations
- **Hourly granularity** (e.g. spike investigation): add `-r h` and optionally `--tz local`. Aggregate the same way; you can also bucket by hour to find when the spike landed.
- **CSV for sharing**: swap `--json` for `--csv`.
- **Compare two windows**: run twice with different `--for` / `--start`/`--end`, then diff per-(env, app).
- **Filter to one env**: keep the same command — Modal doesn't filter server-side; filter in the Python step (`if r["Environment"] != "main": continue`).

## Gotchas
- `--end` is **exclusive**; "data reported for full intervals only", so `--for` is safer than hand-rolled dates when you want a complete window.
- The default for this skill is still exact rolling 7 days, not `--for "last week"`; use hand-rolled `--start/--end` dates and state them.
- `Cost` is a string — always `float()` it before summing.
- The report is workspace-wide; the active workspace comes from the current Modal profile (`modal profile current`). Confirm before running if the user has multiple workspaces.
