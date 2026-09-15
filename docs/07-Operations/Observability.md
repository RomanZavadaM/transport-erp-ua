# Спостережуваність системи

Production мінімум:

- structured JSON logs;
- request / correlation IDs;
- application metrics;
- health checks;
- DB connection monitoring;
- worker / queue monitoring;
- backup monitoring;
- integrity alerts.

Паролі, tokens та чутливі персональні або медичні payload не записуються у звичайні application logs.

Health endpoints мають розрізняти liveness і readiness.
