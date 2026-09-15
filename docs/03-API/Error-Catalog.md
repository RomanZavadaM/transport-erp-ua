# Каталог API помилок

Frontend не аналізує текст повідомлення. Він працює зі стабільним `error.code`.

Базові коди:

- `CONCURRENT_MODIFICATION`;
- `INVALID_STATE_TRANSITION`;
- `VEHICLE_TIME_CONFLICT`;
- `DRIVER_TIME_CONFLICT`;
- `RELEASE_NOT_READY`;
- `WAYBILL_ALREADY_ISSUED`;
- `WAYBILL_ALREADY_CLOSED`;
- `MISSING_ACTUAL_DATA`;
- `INVALID_ODOMETER`;
- `ENTITY_CLOSED`.

Код помилки не локалізується. UI повідомлення для користувача локалізуються для `uk/en/es/fr/de`.
