# TransportERP-UA — Español

Estado de la traducción: `current`  
Fuente canónica: [`README.md`](../../../README.md)

**El idioma canónico del proyecto es el ucraniano.** Si esta traducción difiere de la versión ucraniana, prevalece el texto ucraniano.

TransportERP-UA es un sistema web para una empresa de transporte de Ucrania. Está diseñado para gestionar autobuses y conductores, rutas y horarios, planificación de viajes, turnos operativos, autorización de salida, controles previos, hojas de ruta, movimiento real, kilometraje, combustible, mantenimiento y reparaciones, documentos, informes, roles y auditoría.

## Línea base de arquitectura

Versión actual: **v1.4**.

Decisiones principales:

- monolito modular para las primeras versiones de producción;
- PostgreSQL como fuente transaccional de verdad;
- `Trip` y `Duty` son conceptos de dominio separados;
- un Duty puede contener varios Trips;
- Release pertenece a Duty;
- Waybill se basa en Duty y puede cubrir varios Trips;
- planificación y datos reales se almacenan por separado;
- el historial cerrado y las versiones de documentos son inmutables;
- las correcciones crean nuevas versiones en lugar de reescribir el historial;
- los cambios críticos de estado usan comandos de negocio explícitos;
- auditoría y eventos operativos son append-only;
- PostgreSQL protege las asignaciones de recursos bajo concurrencia;
- la localización admite `uk/en/es/fr/de`, con ucraniano como idioma predeterminado y canónico.

La documentación canónica completa se mantiene en ucraniano en [`/docs`](../../).
