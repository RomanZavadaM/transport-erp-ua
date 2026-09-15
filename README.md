# TransportERP-UA

**Основна мова проєкту — українська.**

[English](docs/i18n/en/README.md) · [Español](docs/i18n/es/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md)

TransportERP-UA — вебсистема для транспортного підприємства України, призначена для автоматизації обліку автобусів і водіїв, маршрутів і розкладів, планування рейсів, нарядів, випуску на лінію, медичного й технічного контролю, шляхових листів, фактичного руху, пробігу, пального, ТО та ремонтів, документів, звітності, ролей і аудиту.

## Архітектурний baseline

Поточна версія архітектури: **v1.3**.

Ключові рішення:

- модульний моноліт для перших production-версій;
- PostgreSQL як транзакційне джерело істини;
- `Trip != Duty`: рейс і наряд є різними доменними сутностями;
- один `Duty` може містити 1..N рейсів;
- `Release` належить `Duty`;
- `Waybill` базово належить `Duty` і може охоплювати 1..N рейсів;
- планові та фактичні дані зберігаються окремо;
- закрита операційна історія та версії документів є незмінними;
- виправлення створюють нові версії / snapshots, а не переписують історію;
- критичні зміни станів виконуються explicit business commands;
- audit та operational events — append-only;
- PostgreSQL exclusion constraints блокують часові конфлікти ресурсів;
- optimistic locking та idempotency захищають конкурентні операції;
- outbox events закладають основу для майбутніх інтеграцій;
- tenant/company isolation є частиною моделі даних.

## Мовна політика

Українська документація є **канонічною**. У разі розбіжності між перекладом та українською версією пріоритет завжди має українська.

Підтримувані мови документації:

- `uk` — українська, основна і нормативна для проєкту;
- `en` — English;
- `es` — Español;
- `fr` — Français;
- `de` — Deutsch.

Правила перекладів описані в [`docs/i18n/README.md`](docs/i18n/README.md).

## Документація

Папка `/docs` одночасно є **Obsidian Vault** і звичайною Markdown-документацією для GitHub та редакторів коду.

Основні точки входу:

- [`PROJECT_STATE.md`](PROJECT_STATE.md) — актуальний checkpoint проєкту;
- [`ARCHITECTURE_VERSION.md`](ARCHITECTURE_VERSION.md) — версія архітектурного baseline;
- [`docs/00-Project/Project-Charter.md`](docs/00-Project/Project-Charter.md) — мета та рамки проєкту;
- [`docs/01-Architecture/ADR`](docs/01-Architecture/ADR) — Architecture Decision Records;
- [`docs/02-Data`](docs/02-Data) — модель даних і DB constraints;
- [`docs/i18n`](docs/i18n) — переклади документації.

## Планована структура коду

```text
backend/     FastAPI application
frontend/    React / Next.js application
infra/       deployment and infrastructure
docs/        канонічна українська документація та Obsidian Vault
templates/   шаблони документації
```

Каталоги application source будуть додані лише після завершення Architecture Freeze та затвердження MVP-контрактів.
