# Обмеження та інваріанти PostgreSQL

Критичні інваріанти забезпечуються PostgreSQL, а не лише application code.

## Основні механізми

- foreign keys із забороною каскадного видалення критичної бізнес-історії;
- unique constraints для бізнес-ідентифікаторів і номерів документів;
- `tstzrange` для часових періодів призначень;
- GiST exclusion constraints для заборони overlapping assignments ресурсів;
- CHECK constraints для часової та числової узгодженості;
- optimistic locking через `row_version`;
- row locks для коротких критичних транзакцій;
- immutable grants/triggers для append-only history tables;
- tenant-aware foreign keys і Row Level Security там, де це доцільно.

Часові інтервали використовують half-open модель `[from,to)`, тому два сусідні призначення можуть закінчуватися і починатися в одну мить без конфлікту.

DB constraints є останньою лінією захисту: попередня перевірка доступності у frontend або backend не скасовує повторної перевірки під час фактичної транзакції.
