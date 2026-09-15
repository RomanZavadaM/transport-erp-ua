# 07 — Експлуатація / Production Operations

Канонічна мова: українська.

## Production baseline

- [Production Deployment](Deployment.md)
- [Backup / Disaster Recovery Policy](Backup-and-DR.md)
- [Disaster Recovery Runbook](Disaster-Recovery-Runbook.md)
- [Secrets & Configuration](Secrets-and-Configuration.md)
- [Observability](Observability.md)
- [System Integrity Checker](Integrity-Checker.md)
- [Production Readiness Checklist](Production-Readiness-Checklist.md)

## Головні принципи

- application і data workload розділені на різні failure domains;
- off-site backup не залежить від production host;
- PostgreSQL має continuous WAL archive і PITR;
- backup вважається працездатним лише після restore drill;
- final Waybill PDF та вкладення мають versioned/object-storage backup;
- production secrets не зберігаються у Git;
- normal write mode після recovery відкривається лише після integrity/smoke checks;
- observability включає backup, restore, worker/outbox та integrity status, а не тільки HTTP uptime.
