# Матриця простежуваності

Мета: пов'язати бізнес-вимогу з реалізацією та автоматичним тестом.

| Business Rule | API / Command | DB protection | Acceptance Test |
|---|---|---|---|
| BR-DISPATCH-001 | assign vehicle to duty | GiST EXCLUDE по vehicle + period | AT-DISPATCH-001 |
| BR-DISPATCH-002 | assign driver to duty | GiST EXCLUDE по driver + period | AT-DISPATCH-002 |
| BR-DISPATCH-003 | add trip to duty | partial UNIQUE active membership | AT-DISPATCH-003 |
| BR-RELEASE-001 | authorize release | transaction guard + check history | AT-RELEASE-001 |
| BR-RELEASE-002 | authorize release | compliance evaluations | AT-RELEASE-002 |
| BR-WAYBILL-001 | issue waybill | UNIQUE number + locked number sequence | AT-WAYBILL-001 |
| BR-WAYBILL-002 | correct waybill | immutable versions | AT-WAYBILL-002 |
| BR-HISTORY-001 | close trip | immutable actual snapshot | AT-HISTORY-001 |
| BR-HISTORY-002 | correct closed trip | correction case + new snapshot | AT-HISTORY-002 |
| BR-CONCURRENCY-001 | critical updates | row_version / If-Match | AT-CONCURRENCY-001 |
| BR-CONCURRENCY-002 | critical POST command | Idempotency-Key | AT-CONCURRENCY-002 |
| BR-I18N-001 | documentation governance | canonical source policy | AT-I18N-001 |
| BR-I18N-002 | API/UI localization | stable codes / locale resources | AT-I18N-002 |

Матриця доповнюється разом із OpenAPI та DDL. Жодне критичне business rule не вважається готовим до production, доки не має автоматизованого acceptance test.
