# Архітектура шляхового листа

Waybill базово прив'язаний до `Duty` та може охоплювати 1..N рейсів.

## Життєвий цикл

`DRAFT → GENERATED → ISSUED → ACTIVE → RETURNED → CLOSING → CLOSED`.

Закритий документ не редагується. Корекція створює нову `waybill_version`, пов'язану з попередньою та correction case.

## Версія документа

Зберігаються:

- version number;
- template version;
- locale;
- immutable snapshot даних;
- snapshot schema version;
- snapshot SHA-256;
- original PDF file;
- PDF SHA-256;
- previous version / correction reason.

Номер документа видається атомарно й ніколи не використовується повторно.

Для українського deployment канонічним є український шаблон. Іншомовні форми є окремими locale-версіями шаблону.
