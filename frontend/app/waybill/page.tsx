"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";

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

type Actuals = {
  waybill_id: string;
  status: string;
  actual_departure: string | null;
  actual_return: string | null;
  odometer_start: number | null;
  odometer_end: number | null;
  fuel_start_liters: number | null;
  fuel_issued_liters: number | null;
  fuel_end_liters: number | null;
  note: string | null;
  distance_km: number | null;
  fuel_consumed_liters: number | null;
  updated_at: string | null;
  closed_at: string | null;
};

type ActualForm = {
  actual_departure: string;
  actual_return: string;
  odometer_start: string;
  odometer_end: string;
  fuel_start_liters: string;
  fuel_issued_liters: string;
  fuel_end_liters: string;
  note: string;
};

const emptyActualForm: ActualForm = {
  actual_departure: "",
  actual_return: "",
  odometer_start: "",
  odometer_end: "",
  fuel_start_liters: "",
  fuel_issued_liters: "",
  fuel_end_liters: "",
  note: "",
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

function dateTimeInput(value: string | null): string {
  return value ? value.slice(0, 16) : "";
}

function numberOrNull(value: string): number | null {
  return value.trim() === "" ? null : Number(value);
}

async function apiError(response: Response, fallback: string): Promise<string> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  return body?.detail ?? fallback;
}

export default function WaybillPage() {
  const [waybillId, setWaybillId] = useState("");
  const [waybill, setWaybill] = useState<Waybill | null>(null);
  const [actuals, setActuals] = useState<Actuals | null>(null);
  const [form, setForm] = useState<ActualForm>(emptyActualForm);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const applyActuals = useCallback((data: Actuals) => {
    setActuals(data);
    setForm({
      actual_departure: dateTimeInput(data.actual_departure),
      actual_return: dateTimeInput(data.actual_return),
      odometer_start: data.odometer_start?.toString() ?? "",
      odometer_end: data.odometer_end?.toString() ?? "",
      fuel_start_liters: data.fuel_start_liters?.toString() ?? "",
      fuel_issued_liters: data.fuel_issued_liters?.toString() ?? "",
      fuel_end_liters: data.fuel_end_liters?.toString() ?? "",
      note: data.note ?? "",
    });
  }, []);

  const load = useCallback(async (id: string) => {
    const encoded = encodeURIComponent(id);
    const [waybillResponse, actualsResponse] = await Promise.all([
      fetch(`/api/waybills/${encoded}`, { cache: "no-store" }),
      fetch(`/api/waybills/${encoded}/actuals`, { cache: "no-store" }),
    ]);
    if (!waybillResponse.ok) {
      throw new Error(await apiError(waybillResponse, "Не вдалося завантажити шляховий лист."));
    }
    if (!actualsResponse.ok) {
      throw new Error(await apiError(actualsResponse, "Не вдалося завантажити фактичні дані."));
    }
    setWaybill((await waybillResponse.json()) as Waybill);
    applyActuals((await actualsResponse.json()) as Actuals);
  }, [applyActuals]);

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("id") ?? "";
    setWaybillId(id);
    if (!id) {
      setError("Не вказано шляховий лист.");
      return;
    }
    load(id).catch((reason) =>
      setError(reason instanceof Error ? reason.message : "Невідома помилка"),
    );
  }, [load]);

  function payload() {
    return {
      actual_departure: form.actual_departure || null,
      actual_return: form.actual_return || null,
      odometer_start: numberOrNull(form.odometer_start),
      odometer_end: numberOrNull(form.odometer_end),
      fuel_start_liters: numberOrNull(form.fuel_start_liters),
      fuel_issued_liters: numberOrNull(form.fuel_issued_liters),
      fuel_end_liters: numberOrNull(form.fuel_end_liters),
      note: form.note.trim() || null,
    };
  }

  async function persistActuals(showMessage = true): Promise<boolean> {
    if (!waybillId) return false;
    setBusy(true);
    setError(null);
    if (showMessage) setMessage(null);
    try {
      const response = await fetch(`/api/waybills/${encodeURIComponent(waybillId)}/actuals`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload()),
      });
      if (!response.ok) {
        setError(await apiError(response, "Не вдалося зберегти фактичні дані."));
        return false;
      }
      applyActuals((await response.json()) as Actuals);
      if (showMessage) setMessage("Фактичні дані збережено.");
      return true;
    } finally {
      setBusy(false);
    }
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await persistActuals(true);
  }

  async function closeWaybill() {
    if (!waybillId || !waybill) return;
    if (!window.confirm("Закрити шляховий лист? Після закриття фактичні дані не редагуються.")) {
      return;
    }
    const saved = await persistActuals(false);
    if (!saved) return;

    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const response = await fetch(`/api/waybills/${encodeURIComponent(waybillId)}/close`, {
        method: "POST",
      });
      if (!response.ok) {
        setError(await apiError(response, "Не вдалося закрити шляховий лист."));
        return;
      }
      applyActuals((await response.json()) as Actuals);
      await load(waybillId);
      setMessage("Шляховий лист закрито. Наряд і рейси завершено, показання одометра записано.");
    } finally {
      setBusy(false);
    }
  }

  function updateField(field: keyof ActualForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  if (error && !waybill) {
    return (
      <main className="app-page">
        <p className="notice error">{error}</p>
        <Link className="button secondary" href="/waybills/">До шляхових листів</Link>
      </main>
    );
  }

  if (!waybill || !actuals) {
    return <main className="app-page"><p className="muted">Завантаження шляхового листа…</p></main>;
  }

  const closed = waybill.status === "CLOSED" || actuals.status === "CLOSED";

  return (
    <main className="app-page waybill-print-page">
      <div className="page-toolbar no-print">
        <div>
          <p className="eyebrow">Шляховий лист</p>
          <h1>{waybill.number}</h1>
        </div>
        <div className="page-toolbar-actions">
          <a
            className="button"
            href={`/api/waybills/${encodeURIComponent(waybill.id)}/pdf`}
            target="_blank"
            rel="noreferrer"
          >PDF 1-АП</a>
          <button className="button secondary" type="button" onClick={() => window.print()}>Друк перегляду</button>
          <Link className="button secondary" href="/waybills/">До списку</Link>
        </div>
      </div>

      {message ? <p className="notice success no-print">{message}</p> : null}
      {error ? <p className="notice error no-print">{error}</p> : null}

      <section className="panel no-print">
        <div className="page-toolbar">
          <div>
            <h2>Фактичне виконання</h2>
            <p className="muted">
              {closed
                ? "Шляхівку закрито. Фактичні дані зафіксовані."
                : "Заповніть фактичний виїзд/повернення, одометр і за потреби паливо."}
            </p>
          </div>
          <strong>{closed ? "ЗАКРИТО" : "ВІДКРИТО"}</strong>
        </div>

        <form onSubmit={save}>
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="actual-departure">Фактичний виїзд</label>
              <input
                id="actual-departure"
                type="datetime-local"
                disabled={closed || busy}
                value={form.actual_departure}
                onChange={(event) => updateField("actual_departure", event.target.value)}
              />
            </div>
            <div className="form-field">
              <label htmlFor="actual-return">Фактичне повернення</label>
              <input
                id="actual-return"
                type="datetime-local"
                disabled={closed || busy}
                value={form.actual_return}
                onChange={(event) => updateField("actual_return", event.target.value)}
              />
            </div>
            <div className="form-field">
              <label htmlFor="odometer-start">Одометр при виїзді, км</label>
              <input
                id="odometer-start"
                type="number"
                min="0"
                disabled={closed || busy}
                value={form.odometer_start}
                onChange={(event) => updateField("odometer_start", event.target.value)}
              />
            </div>
            <div className="form-field">
              <label htmlFor="odometer-end">Одометр при поверненні, км</label>
              <input
                id="odometer-end"
                type="number"
                min="0"
                disabled={closed || busy}
                value={form.odometer_end}
                onChange={(event) => updateField("odometer_end", event.target.value)}
              />
            </div>
            <div className="form-field">
              <label htmlFor="fuel-start">Паливо при виїзді, л</label>
              <input
                id="fuel-start"
                type="number"
                min="0"
                step="0.01"
                disabled={closed || busy}
                value={form.fuel_start_liters}
                onChange={(event) => updateField("fuel_start_liters", event.target.value)}
              />
            </div>
            <div className="form-field">
              <label htmlFor="fuel-issued">Видано пального, л</label>
              <input
                id="fuel-issued"
                type="number"
                min="0"
                step="0.01"
                disabled={closed || busy}
                value={form.fuel_issued_liters}
                onChange={(event) => updateField("fuel_issued_liters", event.target.value)}
              />
            </div>
            <div className="form-field">
              <label htmlFor="fuel-end">Паливо при поверненні, л</label>
              <input
                id="fuel-end"
                type="number"
                min="0"
                step="0.01"
                disabled={closed || busy}
                value={form.fuel_end_liters}
                onChange={(event) => updateField("fuel_end_liters", event.target.value)}
              />
            </div>
            <div className="form-field">
              <label htmlFor="actual-note">Примітка</label>
              <input
                id="actual-note"
                disabled={closed || busy}
                value={form.note}
                onChange={(event) => updateField("note", event.target.value)}
              />
            </div>
          </div>

          <div className="waybill-control-grid" style={{ marginTop: "1rem" }}>
            <div><strong>Фактичний пробіг</strong><p>{actuals.distance_km ?? "—"} км</p></div>
            <div><strong>Фактична витрата пального</strong><p>{actuals.fuel_consumed_liters ?? "—"} л</p></div>
            <div><strong>Закрито</strong><p>{formatDateTime(actuals.closed_at)}</p></div>
          </div>

          {!closed ? (
            <div className="form-actions">
              <button className="button secondary" type="submit" disabled={busy}>Зберегти факт</button>
              <button className="button" type="button" disabled={busy} onClick={closeWaybill}>Закрити шляхівку</button>
            </div>
          ) : null}
        </form>
      </section>

      <article className="waybill-sheet">
        <header className="waybill-header">
          <div>
            <p className="eyebrow">TransportERP-UA · робочий перегляд</p>
            <h1>ШЛЯХОВИЙ ЛИСТ</h1>
            <p><strong>№ {waybill.number}</strong></p>
          </div>
          <div className="waybill-meta">
            <p><strong>Дата:</strong> {formatDate(waybill.service_date)}</p>
            <p><strong>Наряд:</strong> {waybill.duty_number}</p>
            <p><strong>Стан:</strong> {closed ? "Закритий" : "Відкритий"}</p>
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
            <div><strong>Медичний контроль</strong><p>{waybill.medical_checked_by ?? "—"}</p><p>{formatDateTime(waybill.medical_checked_at)}</p></div>
            <div><strong>Технічний контроль</strong><p>{waybill.technical_checked_by ?? "—"}</p><p>{formatDateTime(waybill.technical_checked_at)}</p></div>
            <div><strong>Диспетчер</strong><p>{waybill.dispatcher_checked_by ?? "—"}</p><p>{formatDateTime(waybill.dispatcher_checked_at)}</p></div>
          </div>
          <p><strong>Випущено на лінію:</strong> {formatDateTime(waybill.released_at)}</p>
        </section>

        <section className="waybill-section">
          <h2>Фактичне виконання</h2>
          <div className="waybill-columns">
            <div>
              <p><strong>Виїзд:</strong> {formatDateTime(actuals.actual_departure)}</p>
              <p><strong>Повернення:</strong> {formatDateTime(actuals.actual_return)}</p>
              <p><strong>Одометр:</strong> {actuals.odometer_start ?? "—"} → {actuals.odometer_end ?? "—"} км</p>
              <p><strong>Пробіг:</strong> {actuals.distance_km ?? "—"} км</p>
            </div>
            <div>
              <p><strong>Паливо на виїзді:</strong> {actuals.fuel_start_liters ?? "—"} л</p>
              <p><strong>Видано:</strong> {actuals.fuel_issued_liters ?? "—"} л</p>
              <p><strong>Залишок:</strong> {actuals.fuel_end_liters ?? "—"} л</p>
              <p><strong>Витрата:</strong> {actuals.fuel_consumed_liters ?? "—"} л</p>
            </div>
          </div>
          {actuals.note ? <p><strong>Примітка:</strong> {actuals.note}</p> : null}
        </section>

        <footer className="waybill-footer">
          <p>Створено в TransportERP-UA: {formatDateTime(waybill.created_at)}</p>
          {actuals.closed_at ? <p>Закрито: {formatDateTime(actuals.closed_at)}</p> : null}
        </footer>
      </article>
    </main>
  );
}
