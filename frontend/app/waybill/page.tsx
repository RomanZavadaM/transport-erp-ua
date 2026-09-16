"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Waybill = {
  id: string;
  number: string;
  status: string;
  created_at: string;
  service_date: string;
  duty_number: string;
  company_name: string;
  company_edrpou: string | null;
  vehicle_fleet_number: string;
  vehicle_registration_number: string;
  vehicle_make: string;
  vehicle_model: string;
  driver_personnel_number: string;
  driver_name: string;
  medical_checked_by: string | null;
  medical_checked_at: string | null;
  technical_checked_by: string | null;
  technical_checked_at: string | null;
  dispatcher_checked_by: string | null;
  dispatcher_checked_at: string | null;
  released_at: string;
  trips: {
    route_number: string;
    route_name: string;
    planned_departure: string;
    planned_arrival: string;
  }[];
};

function formatDate(value: string): string {
  const [year, month, day] = value.split("-");
  return `${day}.${month}.${year}`;
}

function formatDateTime(value: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("uk-UA");
}

export default function WaybillPage() {
  const [waybill, setWaybill] = useState<Waybill | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("id");
    if (!id) {
      setError("Не вказано шляховий лист.");
      return;
    }
    fetch(`/api/waybills/${encodeURIComponent(id)}`, { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) {
          const body = (await response.json().catch(() => null)) as { detail?: string } | null;
          throw new Error(body?.detail ?? "Не вдалося завантажити шляховий лист.");
        }
        return response.json() as Promise<Waybill>;
      })
      .then(setWaybill)
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Невідома помилка"));
  }, []);

  if (error) {
    return (
      <main className="app-page">
        <p className="notice error">{error}</p>
        <Link className="button secondary" href="/waybills/">До шляхових листів</Link>
      </main>
    );
  }

  if (!waybill) {
    return <main className="app-page"><p className="muted">Завантаження шляхового листа…</p></main>;
  }

  return (
    <main className="app-page waybill-print-page">
      <div className="page-toolbar no-print">
        <div>
          <p className="eyebrow">Попередній перегляд</p>
          <h1>Шляховий лист {waybill.number}</h1>
        </div>
        <div className="page-toolbar-actions">
          <button className="button" type="button" onClick={() => window.print()}>Друк</button>
          <Link className="button secondary" href="/waybills/">До списку</Link>
        </div>
      </div>

      <article className="waybill-sheet">
        <header className="waybill-header">
          <div>
            <p className="eyebrow">TransportERP-UA · тестова форма</p>
            <h1>ШЛЯХОВИЙ ЛИСТ</h1>
            <p><strong>№ {waybill.number}</strong></p>
          </div>
          <div className="waybill-meta">
            <p><strong>Дата:</strong> {formatDate(waybill.service_date)}</p>
            <p><strong>Наряд:</strong> {waybill.duty_number}</p>
            <p><strong>Стан:</strong> {waybill.status === "OPEN" ? "Відкритий" : "Закритий"}</p>
          </div>
        </header>

        <section className="waybill-section">
          <h2>Підприємство</h2>
          <p><strong>{waybill.company_name}</strong></p>
          <p>ЄДРПОУ: {waybill.company_edrpou ?? "—"}</p>
        </section>

        <div className="waybill-columns">
          <section className="waybill-section">
            <h2>Автобус</h2>
            <p><strong>Гаражний №:</strong> {waybill.vehicle_fleet_number}</p>
            <p><strong>Держ. номер:</strong> {waybill.vehicle_registration_number}</p>
            <p><strong>Марка/модель:</strong> {waybill.vehicle_make} {waybill.vehicle_model}</p>
          </section>

          <section className="waybill-section">
            <h2>Водій</h2>
            <p><strong>{waybill.driver_name}</strong></p>
            <p>Табельний №: {waybill.driver_personnel_number}</p>
          </section>
        </div>

        <section className="waybill-section">
          <h2>План рейсів</h2>
          <table>
            <thead><tr><th>№ маршруту</th><th>Маршрут</th><th>Виїзд</th><th>Прибуття</th></tr></thead>
            <tbody>
              {waybill.trips.map((trip, index) => (
                <tr key={`${trip.route_number}-${index}`}>
                  <td>{trip.route_number}</td>
                  <td>{trip.route_name}</td>
                  <td>{trip.planned_departure}</td>
                  <td>{trip.planned_arrival}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="waybill-section">
          <h2>Передрейсовий контроль і випуск</h2>
          <div className="waybill-control-grid">
            <div>
              <strong>Медичний контроль</strong>
              <p>{waybill.medical_checked_by ?? "—"}</p>
              <p>{formatDateTime(waybill.medical_checked_at)}</p>
            </div>
            <div>
              <strong>Технічний контроль</strong>
              <p>{waybill.technical_checked_by ?? "—"}</p>
              <p>{formatDateTime(waybill.technical_checked_at)}</p>
            </div>
            <div>
              <strong>Диспетчер</strong>
              <p>{waybill.dispatcher_checked_by ?? "—"}</p>
              <p>{formatDateTime(waybill.dispatcher_checked_at)}</p>
            </div>
          </div>
          <p><strong>Випущено на лінію:</strong> {formatDateTime(waybill.released_at)}</p>
        </section>

        <footer className="waybill-footer">
          <p>Створено в TransportERP-UA: {formatDateTime(waybill.created_at)}</p>
          <p>Тестова робоча форма — структура документа ще уточнюється під час розробки.</p>
        </footer>
      </article>
    </main>
  );
}
