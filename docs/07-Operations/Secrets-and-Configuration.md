# Secrets та Configuration Policy

Статус: **M0 production baseline**

## 1. Принцип

Configuration і secrets — різні класи даних.

Configuration має бути відтворюваною й версійованою. Secrets не повинні потрапляти в Git, image layers, application logs або documentation examples.

## 2. Що зберігається у Git

Дозволено:

- Compose templates;
- reverse-proxy templates;
- список environment variables;
- `.env.example` без реальних secrets;
- migration configuration без credentials;
- monitoring/alert rules;
- backup schedule definitions;
- runbooks;
- feature/config defaults, які не є секретними.

## 3. Що заборонено зберігати у Git

- production DB passwords;
- session/JWT signing secrets;
- OAuth/client secrets;
- S3 keys;
- backup repository credentials;
- SMTP/API tokens;
- private TLS/signing keys;
- real `.env` production files;
- recovery encryption passphrases.

Навіть private repository не вважається secret manager.

## 4. Runtime secrets

Production secrets подаються контейнерам через механізм, що не вбудовує їх у image.

Допустимі варіанти:

- Docker secrets/files із контрольованими permissions;
- external secret manager;
- encrypted deployment secret store;
- system-level protected environment injection.

Звичайний plaintext `.env` допустимий тільки як тимчасовий pilot mechanism з жорсткими filesystem permissions і не є цільовим варіантом.

## 5. Least privilege

Окремі credentials для:

- FastAPI application DB role;
- Alembic migration role;
- reporting role;
- backup role;
- object-storage runtime;
- object-storage backup;
- monitoring agent.

Application credential не повинен мати DDL/superuser/backup administration rights.

## 6. Rotation

Підтримується rotation без переписування application code.

Обов'язкова ротація:

- при підозрі на compromise;
- після звільнення/зміни відповідального адміністратора, якщо він мав прямий доступ;
- після випадкового exposure;
- у межах погодженої periodic policy.

Для credentials, які важко rotate, це вважається architecture smell і має бути усунено до production.

## 7. Session/signing keys

Signing/session keys повинні мати:

- достатню entropy;
- version/key identifier;
- контрольований rotation procedure;
- можливість перехідного періоду з двома ключами, якщо protocol цього потребує;
- окремий emergency revoke procedure.

## 8. TLS

TLS private keys зберігаються поза Git.

Certificate renewal контролюється monitoring alert, а не ручною пам'яттю адміністратора.

## 9. Backup credentials

Backup credentials відокремлені від runtime credentials.

Production application не повинна мати право видаляти off-site backup repository.

Де можливо, backup destination використовує write-limited/immutable policy, що зменшує ризик ransomware/credential compromise.

## 10. Recovery secrets

Критичні recovery credentials мають encrypted emergency copy, доступну за documented break-glass procedure.

Потрібно перевіряти не тільки наявність copy, а й можливість фактичного використання під час restore drill.

## 11. Config validation

Application при старті валідовує required configuration.

Помилки типу:

- відсутній DB DSN;
- невідома environment name;
- незаданий object storage bucket;
- insecure production cookie settings;

мають приводити до fail-fast startup, а не до прихованої деградації.

## 12. Environment separation

Credentials різні для:

- development;
- CI/test;
- staging;
- production.

Production secrets ніколи не використовуються у CI/dev.

## 13. Logging/redaction

Configuration dump у logs не повинен показувати secret values.

Для sensitive keys використовуємо redacted representation:

```text
DATABASE_PASSWORD=[REDACTED]
S3_SECRET_KEY=[REDACTED]
```

## 14. Change audit

Зміни security-sensitive configuration повинні залишати операційний evidence:

- хто змінив;
- коли;
- який environment;
- config version/change reference;
- deployment, у якому зміна активована.

Secret value в audit не записується.

## 15. Production launch gate

До production:

- немає real secrets у Git history;
- secret scanning виконаний;
- runtime/migration/backup credentials розділені;
- recovery secrets перевірені;
- rotation procedure задокументована;
- application logs перевірені на redaction.
