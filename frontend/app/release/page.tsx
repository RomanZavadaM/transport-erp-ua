"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

type ReleaseItem = {
  duty_id: string;
  service_date: string;
  duty_number: string;
  vehicle_label: string;
  driver_label: string;
  trip_count: number;
  planned_departure: string;
  planned_arrival: string;
  medical_result: string;
  medical_checked_by: string | null;
  medical_note: string | null;
  technical_result: string;
  technical_checked_by: string | null;
  technical_note: string | null;
  dispatcher_result: string;
  dispatcher_checked_by: string | null;
  dispatcher_note: string | null;
  released_at: string | null;
  ready_to_release: boolean;
};

type StaffDraft = {
  medicalBy: string;
  technicalBy: string;
  dispatcherBy: string;
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

function resultLabel(value: string): string {
  if (value === "PASSED") return "Допущено";
  if (value === "FAILED") return "Не допущено";
  if (value === "APPROVED") return "Дозволено";
  if (value === "REJECTED") return "Заборонено";
  return "Очікує";
}

export default function ReleasePage() {
  const [serviceDate, setServiceDate] = useState(todayLocal());
  const [items, setItems] = useState<ReleaseItem[]>([]);
  const [drafts, setDrafts] = useState<Record<string, StaffDraft>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (dateValue: string) => {
    const response = await fetch(
      `/api/release-controls?service_date=${encodeURIComponent(dateValue)}`,
      { cache: "no-store" },
    );
    if (!response.ok) throw new Error(await apiError(response, "Не вдалося завантажити випуск."));
    const loaded = (await response.json()) as ReleaseItem[];
    setItems(loaded);
    setDrafts((current) => {
      const next = { ...current };
      for (const item of loaded) {
        next[item.duty_id] ??= {
          medicalBy: item.medical_checked_by ?? "",
          technicalBy: item.technical_checked_by ?? "",
          dispatcherBy: item.dispatcher_checked_by ?? "",
        };
      }
      return next;
    });
  }, []);

  useEffect(() => {
    setMessage(null);
    setError(null);
    load(serviceDate).catch((reason) =>
      setError(reason instanceof Error ? reason.message : "Невідома помилка"),
    );
  }, [load, serviceDate]);

  function draft(dutyId: string): StaffDraft {
    return drafts[dutyId] ?? { medicalBy: "", technicalBy: "", dispatcherBy: "" };
  }

  function setDraft(dutyId: string, field: keyof StaffDraft, value: string) {
    setDrafts((current) => ({
      ...current,
      [dutyId]: { ...draft(dutyId), [field]: value },
    }));
  }

  async function saveCheck(
    dutyId: string,
    kind: "medical" | "technical",
    result: "PASSED" | "FAILED",
  ) {
    const checkedBy = kind === "medical" ? draft(dutyId).medicalBy : draft(dutyId).technicalBy;
    if (!checkedBy.trim()) {
      setError(kind === "medical" ? "Вкажіть медика." : "Вкажіть механіка.");
      return;
    }
    setError(null);
    setMessage(null);
    const response = await fetch(`/api/release-controls/${dutyId}/${kind}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ result, checked_by: checkedBy, note: null }),
    });
    if (!response.ok) {
      setError(await apiError(response, "Не вдалося зберегти контроль."));
      return;
    }
    setMessage(kind === "medical" ? "Медичний контроль збережено." : "Технічний контроль збережено.");
    await load(serviceDate);
  }

  async function saveDispatcher(dutyId: string, result: "APPROVED" | "REJECTED") {
    const checkedBy = draft(dutyId).dispatcherBy;
    if (!checkedBy.trim()) {
      setError("Вкажіть диспетчера.");
      return;
    }
    setError(null);
    setMessage(null);
    const response = await fetch(`/api/release-controls/${dutyId}/dispatcher`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ result, checked_by: checkedBy, note: null }),
    });
    if (!response.ok) {
      setError(await apiError(response, "Не вдалося зберегти рішення диспетчера."));
      return;
    }
    setMessage("Рішення диспетчера збережено.");
    await load(serviceDate);
  }

  async function releaseDuty(dutyId: string) {
    setError(null);
    setMessage(null);
    const response = await fetch(`/api/release-controls/${dutyId}/release`, { method: "POST" });
    if (!response.ok) {
      setError(await apiError(response, "Не вдалося випустити наряд на лінію."));
      return;
    }
    setMessage("Наряд випущено на лінію.");
    await load(serviceDate);
  }

  return (
    <main className="app-page">
      <div className="page-toolbar">
        <div>
          <p className="eyebrow">Диспетчерська</p>
          <h1>Випуск на лінію</h1>
        </div>
        <div className="page-toolbar-actions">
          <Link className="button secondary" href="/operations/">Наряди і рейси</Link>
          <Link className="button secondary" href="/">На головну</Link>
        </div>
      </div>

      {message ? <p className="notice success">{message}</p> : null}
      {error ? <p className="notice error">{error}</p> : null}

      <section className="panel">
        <div className="page-toolbar">
          <div>
            <h2>Робоча дата</h2>
            <p className="muted">Показуються наряди, сформовані на вибраний день.</p>
          </div>
          <div className="form-field">
            <label htmlFor="release-date">Дата</label>
            <input
              id="release-date"
              type="date"
              value={serviceDate}
              onChange={(event) => setServiceDate(event.target.value)}
            />
          </div>
        </div>
      </section>

      {items.length === 0 ? (
        <section className="panel">
          <p className="muted">На цю дату немає нарядів для випуску.</p>
        </section>
      ) : (
        items.map((item) => {
          const locked = item.released_at !== null;
          const current = draft(item.duty_id);
          return (
            <section className="panel" key={item.duty_id}>
              <div className="page-toolbar">
                <div>
                  <p className="eyebrow">Наряд {item.duty_number}</p>
                  <h2>{item.vehicle_label} · {item.driver_label}</h2>
                  <p className="muted">
                    {item.planned_departure}–{item.planned_arrival} · рейсів: {item.trip_count}
                  </p>
                </div>
                <span className={`status-pill ${locked ? "ready" : ""}`}>
                  {locked ? "Випущено" : item.ready_to_release ? "Готовий до випуску" : "Контроль"}
                </span>
              </div>

              <div className="module-grid compact">
                <div className="module-card">
                  <h3>Медичний контроль</h3>
                  <p><strong>{resultLabel(item.medical_result)}</strong></p>
                  <div className="form-field">
                    <label htmlFor={`medical-${item.duty_id}`}>Медик</label>
                    <input
                      id={`medical-${item.duty_id}`}
                      disabled={locked}
                      value={current.medicalBy}
                      onChange={(event) => setDraft(item.duty_id, "medicalBy", event.target.value)}
                    />
                  </div>
                  <div className="inline-actions">
                    <button className="button" disabled={locked} type="button" onClick={() => saveCheck(item.duty_id, "medical", "PASSED")}>Допущено</button>
                    <button className="button secondary" disabled={locked} type="button" onClick={() => saveCheck(item.duty_id, "medical", "FAILED")}>Не допущено</button>
                  </div>
                </div>

                <div className="module-card">
                  <h3>Технічний контроль</h3>
                  <p><strong>{resultLabel(item.technical_result)}</strong></p>
                  <div className="form-field">
                    <label htmlFor={`technical-${item.duty_id}`}>Механік</label>
                    <input
                      id={`technical-${item.duty_id}`}
                      disabled={locked}
                      value={current.technicalBy}
                      onChange={(event) => setDraft(item.duty_id, "technicalBy", event.target.value)}
                    />
                  </div>
                  <div className="inline-actions">
                    <button className="button" disabled={locked} type="button" onClick={() => saveCheck(item.duty_id, "technical", "PASSED")}>Допущено</button>
                    <button className="button secondary" disabled={locked} type="button" onClick={() => saveCheck(item.duty_id, "technical", "FAILED")}>Не допущено</button>
                  </div>
                </div>

                <div className="module-card">
                  <h3>Диспетчер</h3>
                  <p><strong>{resultLabel(item.dispatcher_result)}</strong></p>
                  <div className="form-field">
                    <label htmlFor={`dispatcher-${item.duty_id}`}>Диспетчер</label>
                    <input
                      id={`dispatcher-${item.duty_id}`}
                      disabled={locked}
                      value={current.dispatcherBy}
                      onChange={(event) => setDraft(item.duty_id, "dispatcherBy", event.target.value)}
                    />
                  </div>
                  <div className="inline-actions">
                    <button className="button" disabled={locked} type="button" onClick={() => saveDispatcher(item.duty_id, "APPROVED")}>Дозволити</button>
                    <button className="button secondary" disabled={locked} type="button" onClick={() => saveDispatcher(item.duty_id, "REJECTED")}>Заборонити</button>
                  </div>
                </div>
              </div>

              <div className="form-actions">
                <button
                  className="button"
                  type="button"
                  disabled={!item.ready_to_release || locked}
                  onClick={() => releaseDuty(item.duty_id)}
                >
                  {locked ? "Випущено на лінію" : "Випустити на лінію"}
                </button>
              </div>
            </section>
          );
        })
      )}
    </main>
  );
}
