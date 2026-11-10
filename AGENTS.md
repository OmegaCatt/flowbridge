# FlowBridge

Read the parent portfolio plan (FB-1–7), docs/PROJECT.md and docs/QA.md. Fictional orders and local test CRM only. No credentials, real customer files or external writes.

Preserve atomic event identity/hash conflict checks, target idempotency and business-key uniqueness. Retry only transient failures with persisted next-at time, three attempts per cycle, bounded replay and a lease. A stale worker must not overwrite a newer claim. Preview never writes. Keep target URL server-owned, never user-controlled.

Run Python unittest including actual HTTP/concurrency/restart, node syntax and browser QA. Use temporary databases and no external APIs. Document finite test evidence separately from production readiness. Czech-first README with accurate English summary.
