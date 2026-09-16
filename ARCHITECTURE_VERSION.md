# Версія архітектури

Стабільний main baseline: **architecture-v1.5**.  
Робочий baseline: **architecture-v1.6-local-first**.

Статус v1.6: **architecture review before M1.5 implementation**.

## Чому потрібна v1.6

Architecture-v1.5 була надто server-first для реальних малих АТП: PostgreSQL, server-style deployment та object-storage assumptions робили навіть парк на 5–10 машин інфраструктурно складним.

Architecture-v1.6 змінює infrastructure baseline, але не ламає погоджену транспортну бізнес-модель.

## Основні рішення v1.6

- локальний рівень — встановлюваний desktop-застосунок, а не вкладка браузера;
- SQLite — operational DB кожного локального вузла;
- local filesystem — стандартне локальне сховище документів;
- PostgreSQL — технологія центрального/server рівня, а не вимога local;
- single-PC deployment — повноцінний production scenario;
- central є опційним вищим рівнем;
- local SQLite є source of truth, поки central не підтвердив передачу;
- передачу може підготувати оператор, запит зверху або правило, але фактичне відправлення завжди підтверджує локальний оператор;
- після central ACK передані дані локально read-only і редагуються на central;
- невдала передача не забирає local ownership;
- outbox використовується як технічна надійна доставка, без побудови складної messaging infrastructure;
- Redis, S3, Docker, Kubernetes і server-grade monitoring не є local prerequisites;
- backup/restore local SQLite + files є функцією самого застосунку.

## Доменні рішення, які не переглядаються

- Modular Monolith;
- `Trip != Duty`;
- Release належить Duty;
- versioned Waybill;
- Plan != Fact;
- immutable CLOSED history;
- audit trail;
- critical business validation у backend;
- optimistic locking/idempotency там, де це необхідно.

## Superseded decision

`ADR-0002 — PostgreSQL як транзакційне джерело істини` зберігається як історичне рішення v1.5 і позначений superseded.

Нове канонічне рішення: `ADR-0007 — Локальний застосунок, SQLite та передача даних на вищий рівень`.

## Наслідок для M1.5

M1.5 спочатку реалізує local SQLite profile, local audit, transfer approval/ACK/read-only flow, backup/restore та desktop packaging foundation. PostgreSQL-only observability/outbox mechanisms більше не визначають порядок реалізації.
