"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";

type Candidate = {
  duty_id: string;
  duty_number: string;
  service_date: string;
  vehicle_label: string;
  driver_label: string;
  planned_departure: string;
  planned_arrival: string;
};

type Waybill = {
  id: string;
  number: string;
  status: string;
  duty_number: string;
  vehicle_fleet_number: string;
  vehicle_registration_number: string;
  driver_name: string;
  trips: { route_number: string; planned_departure: string; planned_arrival: string }[];
};

function todayLocal(): string {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
}

async function apiError(response: Response, fallback: string): Promise<string> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  return body?.detail ?? fallback;
}

export default function WaybillsPage() {
  const [serviceDate, setServiceDate] = useState(todayLocal());
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [waybills, setWaybills] = useState<Waybill[]>([]);
  const [dutyId, setDutyId] = useState("");
  const [number, setNumber] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (dateValue: string) => {
    const encoded = encodeURIComponent(dateValue);
    const [candidateResponse, waybillResponse] = await Promise.all([
      fetch(`/api/waybill-candidates?service_date=${encoded}`, { cache: "no-store" }),
      fetch(`/api/waybills?service_date=${encoded}`, { cache: "no-store" }),
    ]);
    if (!candidateResponse.ok || !waybillResponse.ok) {
      throw new Error("Не вдалося завантажити шляхові листи.");
    }
    const candidateData = (await candidateResponse.json()) as Candidate[];
    setCandidates(candidateData);
    setWaybills((await waybillResponse.json()) as Waybill[]);
    setDutyId((current) =>
      candidateData.some((item) => item.duty_id === current)
        ? current
        : candidateData[0]?.duty_id ?? "",
    );
  }, []);

  useEffect(() => {
    setError(null);
    setMessage(null);
    load(serviceDate).catch((reason) =>
      setError(reason instanceof Error ? reason.message : "Невідома помилка"),
    );
  }, [load, serviceDate]);

  async function createWaybill(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    const response = await fetch("/api/waybills", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ duty_id: dutyId, number }),
    });
    if (!response.ok) {
      setError(await apiError(response, "Не вдалося створити шляховий лист."));
      return;
    }
    setNumber("");
    setMessage("Шляховий лист створено.");
    await load(serviceDate);
  }

  return (
    <main className="app-page">
      <div className="page-toolbar">
        <div>
          <p className="eyebrow">Документи рейсу</p>
          <h1>Шляхові листи</h1>
        </div>
        <div className="page-toolbar-actions">
          <Link className="button secondary" href="/release/">Випуск на лінію</Link>
          <Link className="button secondary" href="/">На головну</Link>
        </div>
      </div>

      {message ? <p className="notice success">{message}</p> : null}
      {error ? <p className="notice error">{error}</p> : null}

      <section className="panel">
        <div className="page-toolbar">
          <div>
            <h2>Робоча дата</h2>
            <p className="muted">Шляховий лист можна створити тільки з уже випущеного наряду.</p>
          </div>
          <div className="form-field">
            <label htmlFor="waybill-date">Дата</label>
            <input
              id="waybill-date"
              type="date"
              value={serviceDate}
              onChange={(event) => setServiceDate(event.target.value)}
            />
          </div>
        </div>
      </section>

      <section className="panel">
        <h2>Створити шляховий лист</h2>
        {candidates.length === 0 ? (
          <p className="muted">Немає випущених нарядів без шляхового листа.</p>
        ) : (
          <form onSubmit={createWaybill}>
            <div className="form-grid">
              <div className="form-field">
                <label htmlFor="waybill-duty">Наряд</label>
                <select
                  id="waybill-duty"
                  required
                  value={dutyId}
                  onChange={(event) => setDutyId(event.target.value)}
                >
                  {candidates.map((candidate) => (
                    <option key={candidate.duty_id} value={candidate.duty_id}>
                      {candidate.duty_number} · {candidate.planned_departure}–{candidate.planned_arrival} · {candidate.vehicle_label} · {candidate.driver_label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-field">
                <label htmlFor="waybill-number">Номер шляхового листа</label>
                <input
                  id="waybill-number"
                  required
                  value={number}
                  onChange={(event) => setNumber(event.target.value)}
                  placeholder="Напр. ШЛ-001"
                />
              </div>
            </div>
            <div className="form-actions">
              <button className="button" type="submit">Створити шляховий лист</button>
            </div>
          </form>
        )}
      </section>

      <section className="panel">
        <h2>Шляхові листи на {serviceDate} — {waybills.length}</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Номер</th><th>Наряд</th><th>Автобус</th><th>Водій</th><th>Рейси</th><th>Дії</th></tr>
            </thead>
            <tbody>
              {waybills.length === 0 ? (
                <tr><td colSpan={6} className="muted">Шляхових листів на цю дату ще немає.</td></tr>
              ) : (
                waybills.map((waybill) => (
                  <tr key={waybill.id}>
                    <td><strong>{waybill.number}</strong></td>
                    <td>{waybill.duty_number}</td>
                    <td>{waybill.vehicle_fleet_number} — {waybill.vehicle_registration_number}</td>
                    <td>{waybill.driver_name}</td>
                    <td>{waybill.trips.map((trip) => `${trip.planned_departure} №${trip.route_number}`).join(", ")}</td>
                    <td>
                      <div className="form-actions compact-actions">
                        <Link className="button secondary" href={`/waybill/?id=${encodeURIComponent(waybill.id)}`}>Відкрити</Link>
                        <a
                          className="button secondary"
                          href={`/api/waybills/${encodeURIComponent(waybill.id)}/pdf`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          PDF 1-АП
                        </a>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
