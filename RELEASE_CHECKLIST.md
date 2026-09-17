# TransportERP-UA — контрольний список релізу

Цей процес побудований за практикою Taxo: спочатку відтворюваний локальний build і ручна перевірка, потім GitHub release тієї самої версії.

1. Відгалузити нову робочу ревізію (`r9`, `r10`, ...). Старий контрольний checkpoint не змінювати.
2. Оновити `PREVIEW_VERSION.txt`, `PREVIEW_REVISION.txt`, `CHECKPOINT_CURRENT.md` і version-specific checkpoint.
3. Виконати backend checks: Ruff, mypy, pytest.
4. Виконати frontend checks: ESLint, TypeScript, production build.
5. Перевірити запуск через `START.bat` / `START_WINDOWS.bat` у Python-середовищі.
6. Перевірити, що всі змінні дані зберігаються поза папкою програми. База, документи й backup не повинні залежати від версійної папки.
7. Якщо змінювалися PDF/друковані форми — згенерувати тестові документи й візуально перевірити рендер.
8. Для executable-контрольної версії на Windows запустити `BUILD_WINDOWS.bat`, потім `BUILD_INSTALLER.bat`.
9. На macOS запускати `BUILD_MACOS.sh` окремо на Apple Silicon та Intel runner/машині.
10. Перевірити packaged preflight executable. Windows `--windowed` build повинен запускатися без console stdout/stderr.
11. Переконатися, що Portable/Setup/app bundles НЕ містять `*.db`, `*.sqlite`, `*.sqlite3`, `__pycache__`, `.pyc` або тестові дані.
12. Кожен ZIP має унікальну кореневу папку з версією та ревізією.
13. Записати SHA-256 усіх релізних файлів у version-specific `SHA256SUMS_*.txt`.
14. Дати користувачу START/Portable пакет для ручної перевірки на реальному Windows/macOS.
15. Лише після локальної перевірки позначити checkpoint як прийнятий і публікувати GitHub tag/release тієї самої версії.
16. GitHub Actions не повинен мати іншого рецепту збірки: він має повторювати `*.spec` і локальні build-скрипти.
17. Контрольні executable збірки робити приблизно раз на 5–10 робочих ревізій або на важливому milestone, а не на кожен дрібний commit.
18. Зберігати контрольний release щонайменше у двох місцях: GitHub Release + локальна/Library копія.
