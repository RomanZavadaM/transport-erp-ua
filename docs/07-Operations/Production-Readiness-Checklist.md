# Production Readiness Checklist

Статус: **M0 production baseline**

Цей checklist є gate перед першим production запуском і перед значними infrastructure changes.

## 1. Architecture / release

- [ ] production release має Git SHA/tag;
- [ ] container images pinned immutable tags/digests;
- [ ] OpenAPI contract version відомий;
- [ ] Alembic revision відомий;
- [ ] document-template versions відомі;
- [ ] production configuration review пройдений.

## 2. Security

- [ ] HTTPS працює;
- [ ] HTTP redirect policy перевірена;
- [ ] production cookies `Secure`/`HttpOnly` та відповідний `SameSite`;
- [ ] production secrets відсутні в Git history;
- [ ] runtime/migration/backup credentials розділені;
- [ ] DB application user не superuser;
- [ ] SSH/admin access обмежений;
- [ ] log redaction перевірений;
- [ ] default/test credentials відсутні;
- [ ] rate limiting/login throttling перевірені.

## 3. Database

- [ ] migrations пройшли на staging copy;
- [ ] schema revision відповідає release;
- [ ] tenant-aware constraints/RLS enabled according to design;
- [ ] GiST exclusion constraints перевірені;
- [ ] immutable tables protected;
- [ ] critical indexes створені;
- [ ] DB connection pool limits задані;
- [ ] slow-query/statistics monitoring працює.

## 4. Backup

- [ ] full/base backup успішний;
- [ ] WAL archiving працює;
- [ ] off-site repository доступний;
- [ ] backup encryption перевірене;
- [ ] object-storage backup/replication працює;
- [ ] backup monitoring/alerts активні;
- [ ] retention policy налаштована.

## 5. Restore / DR

- [ ] full restore drill виконаний;
- [ ] measured DB restore вкладається у погоджений RTO або risk accepted;
- [ ] measured RPO відповідає target;
- [ ] historical Waybill PDF відкривається після restore;
- [ ] integrity checker пройдений після restore;
- [ ] recovery secrets доступні через documented procedure;
- [ ] DR roles/contacts визначені;
- [ ] maintenance/read-only verification procedure перевірена.

## 6. Object storage / documents

- [ ] object storage не залежить від ephemeral container filesystem;
- [ ] bucket versioning увімкнений там, де передбачено;
- [ ] SHA-256 metadata працює;
- [ ] final Waybill PDF зберігається як immutable versioned artifact;
- [ ] DB↔object integrity checks працюють;
- [ ] sample restore PDF/attachments перевірений.

## 7. Application

- [ ] `/health/live` працює;
- [ ] `/health/ready` працює;
- [ ] fail-fast configuration validation працює;
- [ ] critical business command idempotency перевірена;
- [ ] ETag/If-Match conflicts перевірені;
- [ ] concurrent assignment tests пройшли;
- [ ] release authorization fresh-evaluation tests пройшли;
- [ ] audit/outbox transaction tests пройшли.

## 8. Worker / outbox

- [ ] worker запускається окремо від web API;
- [ ] queue depth/age monitoring працює;
- [ ] retries bounded;
- [ ] failed jobs observable;
- [ ] outbox backlog monitoring працює;
- [ ] stuck outbox alert перевірений.

## 9. UX operational smoke

- [ ] Dispatcher Board readable на цільовому desktop resolution;
- [ ] horizontal overflow/scroll доступний;
- [ ] blocking reason показується текстом;
- [ ] stale/concurrent change UI протестований;
- [ ] Release Workspace проходить happy/blocked scenarios;
- [ ] Waybill preview/print/history працює;
- [ ] mechanic/medic workspaces працюють із мінімальним числом переходів;
- [ ] keyboard/copy-paste basics перевірені.

## 10. i18n

- [ ] `uk` є default locale;
- [ ] EN/ES/FR/DE ресурси не ламають UI layout;
- [ ] API status/error codes не локалізуються;
- [ ] date/time/number formatting перевірено;
- [ ] Ukrainian legal/document templates мають correct locale/version.

## 11. Observability

- [ ] structured logs;
- [ ] request/correlation IDs;
- [ ] current release visible;
- [ ] API latency/error dashboard;
- [ ] DB health dashboard;
- [ ] backup/WAL dashboard;
- [ ] worker/outbox dashboard;
- [ ] integrity alerts dashboard;
- [ ] disk/storage alerts;
- [ ] TLS expiry alert;
- [ ] last successful restore drill visible.

## 12. Integrity

- [ ] full integrity scan пройшов;
- [ ] немає CRITICAL alerts;
- [ ] CLOSED Trip snapshots complete;
- [ ] CLOSED Waybill versions/PDF complete;
- [ ] Release authorizations consistent;
- [ ] number sequences sane;
- [ ] object hashes valid for critical sample/set;
- [ ] audit partition/seal state acceptable.

## 13. Documentation

- [ ] `PROJECT_STATE.md` актуальний;
- [ ] deployment topology актуальна;
- [ ] backup/DR docs актуальні;
- [ ] secrets/config docs актуальні;
- [ ] operator contacts актуальні;
- [ ] rollback/recovery decision path відомий;
- [ ] known risks задокументовані.

## 14. Go / No-Go

Production запуск можливий лише після явного `GO` від:

- technical owner;
- operational/business owner;
- responsible administrator/DR role.

Будь-який unresolved пункт у категоріях Security, Backup, Restore/DR або Integrity повинен або бути закритий, або мати формально прийнятий risk exception із власником та строком усунення.
