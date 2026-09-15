# ADR-0003 — Duty Aggregate

Status: Accepted.

Decision: `Duty` is a separate aggregate from `Trip`.

Reason: one operational duty can contain multiple trips. Release and waybill workflows operate at duty level.
