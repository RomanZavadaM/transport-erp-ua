# 10 — Нормативна база / Regulatory

Канонічна мова: українська.

## M0 baseline

- [Regulatory Register](Regulatory-Register.md)
- [Regulatory Review — 15.09.2026](Regulatory-Review-2026-09.md)
- [MR Policy Decision Register](MR-Decision-Register.md)
- [Regulatory Change Log](Regulatory-Change-Log.md)

## Пов'язані документи

- [Migration Readiness](../02-Data/schema/09-Migration-Readiness.md)
- [Business Rules](../01-Architecture/Business-Rules/README.md)
- [Traceability Matrix](../11-Traceability/Traceability-Matrix.md)
- [Acceptance Criteria](../06-Testing/Acceptance-Criteria.md)

## Принцип

Нормативне джерело не перетворюється безпосередньо на hardcoded application logic. Шлях має бути простежуваним:

```text
Regulatory source
→ approved interpretation / MR decision
→ BR-*
→ API / compliance rule / DB policy
→ AT-*
```

Для rules, зміст яких може змінюватися з часом, використовуються version/effective-period semantics, щоб історичне рішення можна було відтворити за правилами, чинними на момент події.
