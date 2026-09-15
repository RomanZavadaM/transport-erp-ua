# Резервне копіювання та Disaster Recovery

## PostgreSQL

Production policy має включати:

- регулярний full/base backup;
- WAL archiving для point-in-time recovery;
- окреме off-site зберігання;
- retention policy;
- шифрування backup;
- автоматичний контроль успішності;
- регулярний restore test.

Backup не вважається перевіреним, доки не виконувалося реальне відновлення у тестове середовище.

## Файли

Object storage для PDF та вкладень резервується окремо. Для історично важливих документів бажані versioning та retention/object-lock можливості.

## DR

Перед production запуском фіксуються цільові RPO/RTO, відповідальні особи та покроковий runbook відновлення.
