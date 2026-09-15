# Стратегія тестування

## Рівні

- unit tests для domain logic;
- integration tests із реальною PostgreSQL;
- constraint tests для FK/UNIQUE/CHECK/EXCLUDE;
- concurrency tests для одночасних диспетчерських операцій;
- state-machine transition tests;
- API contract tests;
- RBAC/tenant isolation tests;
- audit/outbox tests;
- PDF semantic та visual regression tests;
- backup/restore tests;
- security tests.

SQLite не використовується як заміна PostgreSQL для тестів критичних DB invariants.

Кожне критичне Business Rule ID має мати Acceptance Test ID і відображатися у traceability matrix.
