# Production Deployment — базова топологія

Статус: **M0 production baseline**

Канонічна мова документа — українська.

## 1. Принцип

Перший production deployment не використовує Kubernetes. Базовий runtime — **Linux + Docker Compose**, але production не будується як один сервер із усіма компонентами та резервними копіями на тому самому диску.

Мінімальний production baseline має щонайменше три failure domains:

1. application node;
2. data node;
3. off-site backup/object-storage target, який не залежить від двох попередніх вузлів.

## 2. Рекомендована топологія MVP

```text
Internet / Corporate network
          |
          v
+-----------------------------+
| Application node            |
|-----------------------------|
| Reverse proxy / TLS         |
| Next.js frontend            |
| FastAPI API                 |
| background worker           |
| Redis*                      |
+--------------+--------------+
               |
        private network
               |
+--------------v--------------+
| Data node                   |
|-----------------------------|
| PostgreSQL                  |
| S3-compatible object store* |
| local backup staging        |
+--------------+--------------+
               |
       encrypted transfer
               |
+--------------v--------------+
| Off-site storage            |
|-----------------------------|
| PostgreSQL backup repo      |
| WAL archive                 |
| object-store replica/backup |
| sealed audit evidence       |
+-----------------------------+
```

`*` Redis і локальний object storage не є джерелом бізнес-цілісності. Якщо доступний надійний зовнішній S3-compatible storage, він є кращим за MinIO на data node для фінальних PDF і вкладень.

## 3. Application node

Application node виконує лише application/runtime функції:

- reverse proxy;
- HTTPS termination;
- frontend;
- FastAPI API;
- background worker;
- optional Redis;
- metrics/log shipping agents.

На application node **не зберігається єдина копія**:

- PostgreSQL data directory;
- Waybill PDF;
- вкладень;
- резервних копій;
- secrets backup.

Контейнери application layer повинні бути disposable: після втрати вузла систему можна відновити з image/version + configuration + data services.

## 4. Data node

Data node ізольований від прямого Internet access.

Дозволені network flows повинні бути мінімальними:

- PostgreSQL — тільки з application/administration network;
- object storage — тільки з application/backup services;
- SSH/administration — тільки з trusted administration network/VPN;
- backup transfer — тільки до визначеного off-site target.

PostgreSQL не публікується у public Internet.

## 5. Reverse proxy / TLS

Production підтримує тільки HTTPS.

Reverse proxy відповідає за:

- TLS termination;
- HTTP → HTTPS redirect;
- security headers;
- request/body size limits;
- rate limiting для selected public endpoints;
- access logging без secrets;
- проксіювання frontend/API;
- connection/timeouts policy.

HSTS вмикається після перевірки production HTTPS/domain setup.

## 6. Docker Compose

Production Compose поділяється щонайменше на:

- application services;
- data/backup services;
- monitoring agents.

Production Compose файли не містять secrets у plaintext.

Images використовують immutable release tags/digests. Production не розгортається з `latest`.

## 7. Release artifact

Кожний production release повинен бути ідентифікований:

- Git commit SHA;
- release/version tag;
- container image digest;
- DB migration revision;
- OpenAPI contract version;
- document-template versions.

Ці значення повинні бути доступні в internal system/version endpoint або deployment metadata.

## 8. Deployment sequence

Базовий порядок release:

1. перевірити backup/restore readiness;
2. перевірити schema migration compatibility;
3. pull immutable images;
4. виконати backward-compatible migrations;
5. запустити/оновити API + worker;
6. оновити frontend;
7. readiness checks;
8. smoke tests ключового operational flow;
9. зафіксувати deployment event/version.

Небезпечні destructive migrations не виконуються одночасно з application release без expand/migrate/contract procedure.

## 9. Environments

Мінімально існують:

- `development`;
- `test/CI`;
- `staging`;
- `production`.

Production data не копіюється у development/staging без контрольованої анонімізації.

Staging має бути максимально близьким до production за:

- PostgreSQL major version;
- reverse proxy;
- Compose topology;
- migrations;
- object-storage API;
- locale/document generation;
- backup restore procedure.

## 10. Network segmentation

Логічно виділяються:

- public/edge network;
- application private network;
- data network;
- administration network;
- backup destination.

Доступ між сегментами дозволяється explicit allow-list правилами.

## 11. SSH та адміністративний доступ

Рекомендовано:

- key-based authentication;
- password SSH login disabled;
- root login disabled;
- окремі named administrator accounts;
- MFA/VPN/bastion там, де це доступно;
- журналювання адміністративних входів;
- регулярна ротація доступів після зміни персоналу.

## 12. PostgreSQL connection policy

FastAPI не використовує database superuser.

Окремі DB roles:

- migration role;
- application runtime role;
- reporting/read-only role;
- backup role.

Connection pool має верхню межу; кількість connections не масштабується безконтрольно разом із web workers.

## 13. Object storage

Файли зберігаються поза container filesystem.

Для Waybill PDF та історично важливих документів рекомендовані:

- bucket versioning;
- encryption at rest;
- SHA-256 metadata у PostgreSQL;
- off-site replication/backup;
- retention/object-lock після юридичного підтвердження policy.

## 14. Redis

Redis може використовуватися для:

- short-lived cache;
- rate limiting;
- job queue;
- transient synchronization.

Redis **не може бути єдиним джерелом**:

- business status;
- assignment;
- idempotency truth для фінальних critical commands, якщо їх втрата порушить consistency;
- audit;
- document numbering.

## 15. Single-host fallback

Для тимчасового pilot deployment допускається один production host лише якщо:

- PostgreSQL і object storage мають незалежний off-site backup;
- WAL archiving працює поза цим host;
- restore drill перевірений;
- application і data volumes розділені;
- цей режим формально позначений як `pilot`, а не target production topology.

Це не є цільовою архітектурою після стабілізації MVP.

## 16. Масштабування

Перші кроки масштабування без переходу на Kubernetes:

1. окремий PostgreSQL node;
2. кілька API containers за reverse proxy;
3. окремі worker instances;
4. external S3-compatible object storage;
5. read replica для важких reports — лише коли profiling доведе потребу.

Перехід на Kubernetes не є milestone сам по собі і розглядається лише при реальній операційній потребі.
