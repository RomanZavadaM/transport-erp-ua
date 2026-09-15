# Версія архітектури

Поточний baseline: **architecture-v1.5**

Статус: **M0 Architecture Freeze — FROZEN**

## Зміст v1.5

`v1.5` завершує M0 та фіксує узгоджений production-oriented baseline:

- Modular Monolith + PostgreSQL source of truth;
- `Trip != Duty`, Release→Duty, versioned Waybill;
- Plan != Fact та immutable CLOSED history;
- PostgreSQL conflict constraints, tenant isolation, RLS;
- command-oriented REST API, optimistic locking, idempotency;
- повний MVP/UX/permissions/testing/operations package;
- українська (`uk`) як канонічна мова, `en/es/fr/de` як похідні локалі;
- regulatory/business review `MR-001..MR-007` завершено;
- physical schema та API синхронізовані з фінальними review-рішеннями;
- machine API contract: base OpenAPI + freeze overlay.

Після merge цього baseline в `main` створюється tag `architecture-v1.5`, після чого стартує M1 Foundation.

Фундаментальні зміни core aggregate boundaries, immutable-history model, resource-conflict invariants, Release workflow або tenant model потребують нового ADR та impact analysis.
