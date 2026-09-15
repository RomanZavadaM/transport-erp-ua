# Permissions API

Канонічний каталог permissions перенесено до [`Permissions-Catalog.md`](Permissions-Catalog.md).

Цей файл залишено як стабільну вхідну точку для старих посилань.

Ключовий принцип: backend перевіряє **permission**, а не лише назву ролі. Технічна роль адміністратора не отримує автоматично operational permissions (`release.authorize`, `medical_check.perform`, `technical_check.perform` тощо).
