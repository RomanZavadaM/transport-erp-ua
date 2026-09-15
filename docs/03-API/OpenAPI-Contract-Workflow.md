# OpenAPI contract workflow

## Канонічний machine contract

Для реалізації та contract tests використовується:

`openapi-mvp-v1-consolidated.yaml`

Це детерміновано згенерований і валідований OpenAPI 3.1 contract.

## Вхідні файли

- `openapi-mvp-v1.yaml` — базовий M0 draft;
- `openapi-mvp-v1-freeze-overlay.yaml` — corrections, прийняті під час Architecture Freeze v1.5.

Вони збережені як простежувані generation inputs. Backend/frontend не повинні окремо трактувати їх як два різні API-контракти.

## Генерація

```bash
python tools/openapi/consolidate.py \
  --base docs/03-API/openapi-mvp-v1.yaml \
  --overlay docs/03-API/openapi-mvp-v1-freeze-overlay.yaml \
  --output docs/03-API/openapi-mvp-v1-consolidated.yaml
```

Після генерації:

```bash
python tools/openapi/validate.py docs/03-API/openapi-mvp-v1-consolidated.yaml
```

## CI gate

CI:

1. генерує contract повторно;
2. перевіряє OpenAPI 3.1;
3. перевіряє freeze-invariants;
4. порівнює generated output із committed consolidated file;
5. падає, якщо committed contract застарів.

У same-repository pull request CI може синхронізувати generated consolidated file в PR branch. На `main` workflow не змінює Git і працює лише як verification gate.

## Правило розвитку

Новий API change має оновити семантичну документацію та generation inputs, пройти validation і залишити `openapi-mvp-v1-consolidated.yaml` синхронізованим. Ручне редагування consolidated file як незалежного source of truth не допускається.
