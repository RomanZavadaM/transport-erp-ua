# План розробки MVP

## M0 — Architecture Freeze
Документація, OpenAPI, ERD/DDL, UX flows, permissions, testing, deployment, backup/DR.

## M1 — Foundation
Identity, RBAC, migrations, audit foundation, logging, CI/CD, application skeleton.

## M2 — Fleet & Drivers
Автобуси, водії, документи, статуси та історія.

## M3 — Planning
Зупинки, маршрути, версії, розклад, генерація рейсів.

## M4 — Dispatch
Duty, призначення автобуса/водіїв, resource conflicts, dispatcher board.

## M5 — Release
Передрейсові перевірки, compliance, dispatcher authorization.

## M6 — Waybill
Нумерація, snapshot/version, PDF, issue/return/close/correction.

## M7 — Execution & Closing
Фактичний рух, одометр, повернення, trip/duty close.

## M8 — Reports & Production Hardening
Operational reports, security, concurrency, restore testing, performance, production readiness.

До завершення M0 application code не вважається стабільною частиною проєкту.
