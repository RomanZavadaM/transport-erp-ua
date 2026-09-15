# ADR-0002-PostgreSQL-Source-of-Truth

## Status
Accepted

## Decision
PostgreSQL is the transactional source of truth and enforces critical invariants in addition to application-layer validation.

## Rationale
Concurrent dispatcher operations require guarantees stronger than UI or application checks alone.

## Consequences
Critical constraints use PostgreSQL features such as foreign keys, unique constraints, range types, exclusion constraints and row locking.
