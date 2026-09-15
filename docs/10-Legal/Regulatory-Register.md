# Реєстр нормативних вимог

Статус: **перевірено 15.09.2026 для M0 Architecture Freeze**

Цей реєстр пов'язує нормативні джерела з business rules та архітектурними рішеннями. Канонічний опис ведеться українською.

## Правила ведення

1. Для кожного джерела фіксуються назва, офіційний ідентифікатор/посилання, дата review та affected domains.
2. Нормативний текст не копіюється в код як неструктурована логіка.
3. Нормативно залежні rules мають version/effective-period semantics там, де зміна джерела може змінити результат.
4. Зміна джерела створює запис у Regulatory Change Log і impact review.
5. Перед production release із regulatory-impact changes джерело перевіряється повторно.

## REG-001 — Закон України «Про автомобільний транспорт»

- Ідентифікатор: №2344-III.
- Офіційне джерело: `https://zakon.rada.gov.ua/go/2344-14`
- Review: 15.09.2026.
- Domains: passenger transport, documents, carrier/driver evidence, routes.
- Affected rules: `BR-COMPLIANCE-001`, `BR-COMPLIANCE-002`, `BR-WAYBILL-003`.

Зафіксовано для системи:

- document requirements залежать від виду перевезення;
- carrier-level та driver/vehicle evidence не змішуються;
- історична згадка «дорожній лист» не використовується як підстава для універсального blocking rule.

## REG-002 — Положення про медичний огляд кандидатів у водії та водіїв транспортних засобів

- Наказ МОЗ/МВС №65/80 від 31.01.2013.
- Реєстраційний ідентифікатор: `z0308-13`.
- Офіційне джерело: `https://zakon.rada.gov.ua/go/z0308-13`
- Review: 15.09.2026.
- Domains: pre-trip/post-trip medical checks.
- Affected rules: `BR-RELEASE-001`, `BR-RELEASE-004`.

Зафіксовано:

- щозмінний передрейсовий/післярейсовий контроль;
- normalized M0 result `FIT` / `UNFIT`;
- `UNFIT` блокує Release.

## REG-003 — Порядок перевірки технічного стану транспортних засобів автомобільними перевізниками

- Наказ №974 від 05.08.2008.
- Реєстраційний ідентифікатор: `z0794-08`.
- Офіційне джерело: `https://zakon.rada.gov.ua/go/z0794-08`
- Review: 15.09.2026.
- Domains: technical checks, defects, maintenance, release.
- Affected rules: `BR-RELEASE-005`, `BR-RELEASE-006`.

Зафіксовано:

- qualified/authorized technical personnel, а не одна жорстко названа посада в domain model;
- окремий driver pre-departure technical check/evidence;
- blocking technical nonconformity не допускає Release.

## REG-004 — Положення про робочий час і час відпочинку водіїв колісних транспортних засобів

- Наказ №340.
- Реєстраційний ідентифікатор: `z0811-10`.
- Офіційне джерело: `https://zakon.rada.gov.ua/go/z0811-10`
- Review: 15.09.2026.
- Враховано нову редакцію/зміни 2025–2026 років.
- Domains: driver work/rest, crew, schedules, future compliance.
- Affected rules: `BR-CREW-001`, `BR-CREW-002`, `BR-CREW-003`.

Зафіксовано:

- crew driving підтримує щонайменше двох водіїв;
- Duty не може мати модель «рівно один водій»;
- майбутній work/rest engine має відрізняти driving, other work, breaks, readiness і rest.

## REG-005 — Порядок організації перевезень пасажирів та багажу автомобільним транспортом

- Наказ Мінрозвитку №1473 від 09.10.2025.
- Реєстраційний ідентифікатор: `z1924-25`.
- Офіційне джерело: `https://zakon.rada.gov.ua/go/z1924-25`
- Чинність для нового механізму: з 13.07.2026.
- Review: 15.09.2026.
- Domains: routes, route passports, schedules, future government integration.

Зафіксовано:

- route passport формується через державний Єдиний комплекс;
- internal `Route/RouteVersion/Schedule` лишаються структурованими aggregates;
- future integration потребує external identifier/reference/sync metadata;
- державний реєстр не дублюється як внутрішнє source of truth.

## REG-006 — Перелік типових документів із зазначенням строків зберігання

- Наказ Мін'юсту №578/5.
- Реєстраційний ідентифікатор: `z0571-12`.
- Офіційне джерело: `https://zakon.rada.gov.ua/go/z0571-12`
- Review: 15.09.2026.
- Domains: retention/archive.
- Affected rules: `BR-RETENTION-001`, `BR-RETENTION-002`, `BR-RETENTION-003`.

Архітектурний наслідок: retention задається за класом документа, а не одним global number.

## REG-007 — Податковий кодекс України, стаття 44

- Закон №2755-VI.
- Офіційне джерело: `https://zakon.rada.gov.ua/go/2755-17`
- Review: 15.09.2026.
- Domains: primary accounting/tax document retention.
- Affected rules: `BR-RETENTION-001`, `BR-RETENTION-002`.

Для відповідної категорії первинних документів юридичних осіб review враховує мінімальний строк 1825 днів, якщо не застосовується довший строк або продовження за законом.

## Пов'язані документи проєкту

- [`Regulatory-Review-2026-09.md`](Regulatory-Review-2026-09.md)
- [`MR-Decision-Register.md`](MR-Decision-Register.md)
- [`Regulatory-Change-Log.md`](Regulatory-Change-Log.md)
- [`../02-Data/schema/09-Migration-Readiness.md`](../02-Data/schema/09-Migration-Readiness.md)
- [`../11-Traceability/Traceability-Matrix.md`](../11-Traceability/Traceability-Matrix.md)
