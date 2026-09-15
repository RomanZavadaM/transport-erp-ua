# Database Constraints

Critical invariants are enforced in PostgreSQL, not only in application code.

## Key mechanisms

- foreign keys with restrictive delete policy for business history;
- unique constraints for business identifiers and document numbers;
- `tstzrange` for assignment periods;
- GiST exclusion constraints for overlapping resource assignments;
- check constraints for time and numeric consistency;
- optimistic locking through `row_version`;
- row locks for short critical transactions;
- immutable grants/triggers for append-only history tables;
- tenant-aware foreign keys / row-level security where appropriate.

Half-open periods `[from,to)` allow adjacent assignments without overlap.
