# Модель бази даних

PostgreSQL є транзакційним джерелом істини.

## Основні групи таблиць

- організація та доступ: `companies`, `depots`, `users`, `roles`, `permissions`;
- автобуси: `vehicles`, `vehicle_documents`, `vehicle_odometer_readings`;
- водії: `drivers`, `driver_documents`;
- маршрути: `stops`, `routes`, `route_versions`, `route_stops`;
- розклад: `schedules`, `schedule_versions`, `schedule_runs`, календарі;
- рейси: `trips`, `trip_stop_plan`, `trip_actuals`, `trip_actual_snapshots`, `trip_events`;
- наряди: `duties`, `duty_trips`, призначення та фактичне використання ресурсів;
- випуск: `releases`, `pre_trip_checks`, compliance evaluations, authorizations;
- шляхові листи: `waybills`, `waybill_versions`, `waybill_trips`, `number_sequences`;
- файли: `files`, attachments;
- паливо: `fuel_operations`;
- технічний стан: `defects`, maintenance, `repair_orders`;
- корекції: `correction_cases`;
- системна історія: `audit_log`, `outbox_events`, integrity alerts.

Основні ідентифікатори використовують UUID. Моменти часу зберігаються як `timestamptz`. Оперативна модель нормалізована, а історичні представлення документів та фактів зберігаються як незмінні snapshots/versions.
