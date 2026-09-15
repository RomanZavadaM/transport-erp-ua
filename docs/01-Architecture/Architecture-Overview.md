# Architecture Overview

## Baseline

- Modular Monolith.
- FastAPI backend.
- PostgreSQL transactional source of truth.
- React / Next.js frontend.
- S3-compatible file storage.
- REST API.
- Append-only audit and operational event history.
- Outbox for future integrations.

## Core domain flow

Schedule → Trip → Duty → assignments → checks → Release → Waybill → execution → close → reporting.

`Trip` and `Duty` are deliberately separate. One Duty may contain multiple Trips.

## Integrity

Critical resource conflicts are enforced in PostgreSQL. Closed history is versioned. Plan and fact are stored separately.
