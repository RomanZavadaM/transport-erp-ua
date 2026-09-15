# Матриця простежуваності

Мета: пов'язати бізнес-вимогу з реалізацією, DB protection/policy та автоматичним тестом.

| Business Rule | API / Command | DB / Policy protection | Acceptance Test |
|---|---|---|---|
| BR-DISPATCH-001 | assign vehicle to duty | GiST EXCLUDE по vehicle + period | AT-DISPATCH-001 |
| BR-DISPATCH-002 | assign driver to duty | GiST EXCLUDE по driver + period | AT-DISPATCH-002 |
| BR-DISPATCH-003 | add trip to duty | partial UNIQUE active membership | AT-DISPATCH-003 |
| BR-RELEASE-001 | authorize release | transaction guard + check history | AT-RELEASE-001 |
| BR-RELEASE-002 | authorize release | compliance evaluations | AT-RELEASE-002 |
| BR-RELEASE-003 | authorize release | fresh evaluation in same transaction | AT-RELEASE-003 |
| BR-RELEASE-004 | medical check / authorize release | `FIT/UNFIT` result + effective check guard | AT-RELEASE-004 |
| BR-RELEASE-005 | technical check / authorize release | technical evidence + blocking defect checks | AT-RELEASE-005 |
| BR-RELEASE-006 | technical check perform | permission/qualified-actor policy | AT-RELEASE-006 |
| BR-COMPLIANCE-001 | evaluate/authorize release | versioned context-aware compliance rules | AT-COMPLIANCE-001 |
| BR-COMPLIANCE-002 | compliance evidence | separate carrier/driver/vehicle evidence domains | AT-COMPLIANCE-002 |
| BR-COMPLIANCE-003 | evaluate release | effective-period/versioned rule evaluation snapshot | AT-COMPLIANCE-003 |
| BR-CREW-001 | assign/replace drivers; actual usage | multiple driver assignments + usage periods | AT-CREW-001 |
| BR-CREW-002 | duty crew mode | explicit crew policy separate from internal role label | AT-CREW-002 |
| BR-CREW-003 | assign driver | GiST EXCLUDE remains global | AT-CREW-003 |
| BR-WAYBILL-001 | issue waybill | UNIQUE number + locked number sequence | AT-WAYBILL-001 |
| BR-WAYBILL-002 | correct waybill | immutable versions | AT-WAYBILL-002 |
| BR-WAYBILL-003 | create/issue waybill | configurable document role/type + policy | AT-WAYBILL-003 |
| BR-SERVICE-DATE-001 | create/generate trip/duty | immutable explicit `service_date` | AT-SERVICE-DATE-001 |
| BR-RETENTION-001 | retention jobs/policy | retention class matrix | AT-RETENTION-001 |
| BR-RETENTION-002 | purge/archive process | no automatic delete of CLOSED evidence; legal-hold guard | AT-RETENTION-002 |
| BR-RETENTION-003 | object retention | configured object-lock/retention class | AT-RETENTION-003 |
| BR-HISTORY-001 | close trip | immutable actual snapshot | AT-HISTORY-001 |
| BR-HISTORY-002 | correct closed trip | correction case + new snapshot | AT-HISTORY-002 |
| BR-AUDIT-001 | critical commands | audit write in transaction/application workflow | AT-AUDIT-001 |
| BR-AUDIT-002 | history/audit storage | append-only grants/triggers | AT-AUDIT-002 |
| BR-CONCURRENCY-001 | critical updates | row_version / If-Match | AT-CONCURRENCY-001 |
| BR-CONCURRENCY-002 | critical POST command | Idempotency-Key | AT-CONCURRENCY-002 |
| BR-I18N-001 | documentation governance | canonical source policy | AT-I18N-001 |
| BR-I18N-002 | API/UI localization | stable codes / locale resources | AT-I18N-002 |

## Regulatory source linkage

Актуальний legal/business mapping ведеться в:

- `docs/10-Legal/Regulatory-Review-2026-09.md`;
- `docs/10-Legal/MR-Decision-Register.md`;
- `docs/10-Legal/Regulatory-Register.md`.

Критичне rule не вважається production-ready, доки не має acceptance test. Нормативно залежне rule додатково повинно мати version/effective-period semantics там, де законодавча зміна може змінити результат у майбутньому.
