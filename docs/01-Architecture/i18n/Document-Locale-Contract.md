# Document Locale Contract

Статус: **M0 i18n contract**

## 1. Принцип

Юридично значимий документ не локалізується простим підставленням UI translations.

Документ використовує explicit template version з власною locale.

## 2. Template identity

Логічно документ визначається через:

```text
template_code
version_no
locale
valid_from / valid_until
```

Наприклад український і німецький template є різними template versions, навіть якщо мають однакову структуру.

## 3. Український deployment

Для українського транспортного підприємства `uk` є первинною locale нормативних документів, якщо конкретне regulatory/business правило не визначає інше.

Перекладена форма не замінює українську юридично значиму форму автоматично.

## 4. Snapshot

Waybill/document snapshot зберігає фактичні values, що були використані при формуванні конкретної версії документа.

Зміна user locale після створення PDF не змінює:

- snapshot;
- template_version_id;
- PDF;
- PDF hash;
- historical version.

## 5. Regeneration

`Regenerate` не перезаписує вже issued/closed historical PDF.

Якщо business workflow дозволяє нову версію, створюється новий `waybill_version` або відповідна document version із:

- новим version number;
- explicit template version;
- locale;
- snapshot;
- hashes;
- reason/previous_version link де потрібно.

## 6. Print

Print завжди друкує конкретну selected document version.

Зміна UI locale не повинна автоматично друкувати іншу мовну форму historical document.

## 7. Preview

Preview показує locale та template version документа.

Користувач має розуміти, яку саме version він переглядає/друкує.

## 8. Translated supporting copies

У майбутньому може бути додано поняття informational translated copy.

Така copy:

- не замінює canonical document version;
- має explicit locale;
- повинна бути позначена як translation/informational copy, якщо це потрібно policy;
- не змінює underlying business state.

Це не входить у MVP без окремої business requirement.

## 9. Formatting у документах

Template locale контролює:

- labels;
- month names;
- date/time presentation;
- number formatting;
- explanatory text.

Domain numeric/date values залишаються типізованими у snapshot/schema.

## 10. Template validation

Перед activation template version перевіряється:

- required fields present;
- snapshot schema compatible;
- pagination/print layout;
- locale-specific labels;
- no clipped critical fields;
- PDF generation reproducible enough for operational use.

## 11. Historical reproducibility

Для document version зберігаються:

- `document_template_version_id`;
- `snapshot_schema_version`;
- snapshot;
- snapshot SHA-256;
- PDF object reference;
- PDF SHA-256;
- locale.

Оригінальний PDF не перегенеровується після upgrade rendering engine.

## 12. Template lifecycle

Template version може бути:

- draft;
- active;
- retired.

Вже використана historical version не видаляється.

Нова regulatory форма означає нову template version, а не редагування старої.
