# TransportERP-UA — Deutsch

Übersetzungsstatus: `current`  
Kanonische Quelle: [`README.md`](../../../README.md)

**Die kanonische Projektsprache ist Ukrainisch.** Wenn diese Übersetzung von der ukrainischen Fassung abweicht, gilt der ukrainische Text.

TransportERP-UA ist ein webbasiertes System für ein ukrainisches Verkehrsunternehmen. Es unterstützt die Verwaltung von Bussen und Fahrern, Linien und Fahrplänen, Fahrtplanung, operative Dienste, Freigabe zum Linieneinsatz, Vorabkontrollen, Fahrtenblätter, tatsächliche Bewegung, Kilometerleistung, Kraftstoff, Wartung und Reparaturen, Dokumente, Berichte, Rollen und Audit.

## Architektur-Baseline

Aktuelle Version: **v1.4**.

Wesentliche Entscheidungen:

- modularer Monolith für die ersten Produktionsversionen;
- PostgreSQL als transaktionale Quelle der Wahrheit;
- `Trip` und `Duty` sind getrennte Domänenkonzepte;
- ein Duty kann mehrere Trips enthalten;
- Release gehört zu Duty;
- Waybill basiert auf Duty und kann mehrere Trips abdecken;
- Plan- und Ist-Daten werden getrennt gespeichert;
- abgeschlossene Historie und Dokumentversionen sind unveränderlich;
- Korrekturen erzeugen neue Versionen statt die Historie zu überschreiben;
- kritische Statusänderungen verwenden explizite Geschäftskommandos;
- Audit und operative Ereignisse sind append-only;
- PostgreSQL schützt Ressourcenzuweisungen bei konkurrierenden Vorgängen;
- die Lokalisierung unterstützt `uk/en/es/fr/de`, wobei Ukrainisch Standard- und kanonische Sprache ist.

Die vollständige kanonische Dokumentation wird auf Ukrainisch unter [`/docs`](../../) gepflegt.
