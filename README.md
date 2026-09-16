# TransportERP-UA

**Канонічна мова проєкту — українська.**

[English](docs/i18n/en/README.md) · [Español](docs/i18n/es/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md)

TransportERP-UA — ERP для операційної роботи транспортного підприємства.

## Product model

Базовий локальний рівень — **встановлюваний desktop-застосунок** з SQLite, локальними документами, backup/restore та можливістю передавати дані на центральний рівень.

Малий парк може повноцінно працювати на одному комп’ютері без PostgreSQL/Docker/Redis/S3 та без постійного Internet.

Якщо підприємству потрібен вищий рівень, локальні дані передаються на central після явного підтвердження локального оператора. До valid central ACK authority залишається `LOCAL`; після ACK authority=`CENTRAL`, а local copy стає read-only.

## Architecture baseline

Стабільний `main`: **architecture-v1.5**.  
Робочий review перед M1.5: **architecture-v1.6-local-first**.

Канонічні точки входу:

- [PROJECT_STATE.md](PROJECT_STATE.md)
- [ARCHITECTURE_VERSION.md](ARCHITECTURE_VERSION.md)
- [ADR-0007 Local Desktop / SQLite / Central Transfer](docs/01-Architecture/ADR/ADR-0007-Local-SQLite-and-Central-Transfer.md)
- [Architecture Overview](docs/01-Architecture/Architecture-Overview.md)
- [Local Desktop Application](docs/07-Operations/Local-Desktop-Application.md)
- [Local SQLite Foundation — M1.5](docs/02-Data/schema/10-Local-SQLite-Foundation.md)
- [Database Model](docs/02-Data/Database-Model.md)
- [Deployment](docs/07-Operations/Deployment.md)
- [Backup / DR](docs/07-Operations/Backup-and-DR.md)
- [M1.5 Issue #20](https://github.com/RomanZavadaM/transport-erp-ua/issues/20)
- [docs/_index.md](docs/_index.md)

## Незмінне доменне ядро

`Trip != Duty`, Release→Duty, versioned Waybill, Plan != Fact, immutable CLOSED history, audit і transactional business rules залишаються базовими рішеннями.
