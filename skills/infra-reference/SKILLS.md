---
name: infra-reference
description: Infrastructure help for MongoDB, RunPod, R2, Temporal, queries, logging, deployment, and debugging.
---

# Infrastructure Guidelines

## General

- No hardcoded config
- Use env vars
- Assume services can fail
- Log context (IDs, durations, resources)
- Prefer idempotent operations

---

## MongoDB

- Model by access patterns
- Use indexes carefully
- Avoid large documents / growing arrays
- Use projections (no full scans)
- Use explain() for slow queries

---

## RunPod

- Never hardcode pod IDs
- Handle preemption
- Shut down idle resources
- Pin image versions

---

## Cloudflare R2

- Use for large storage
- Use presigned URLs
- Never expose keys
- Use env-based credentials

---

## Temporal

- Workflows must be deterministic
- Use activities for external work
- Use retries + timeouts
- Keep workflows small and composable
