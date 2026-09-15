"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";

type DriverStatus = "ACTIVE" | "LEAVE" | "SICK" | "SUSPENDED" | "TERMINATED";

type Driver = {
  id: string;
  personnel_number: string;
  last_name: string;
  first_name: string;
  middle_name: string | null;
  phone: string | null;
  employment_status: DriverStatus;
  row_version: number;
};

type DriverForm = {
  personnel_number: string;
  last_name: string;
  first_name: string;
  middle_name: string;
  phone: string;
  employment_status: DriverStatus;
};

const emptyForm: DriverForm = {
  personnel_number: "",
  last_name: "",
  first_name: "",
  middle_name: "",
  phone: "",
  employment_status: "ACTIVE",
};

const statusLabels: Record<DriverStatus, string> = {
  ACTIVE: "Працює",
  LEAVE: "Відпустка",
  SICK: "Лікарняний",
  SUSPENDED: "Відсторонений",
  TERMINATED: "Звільнений",
};

export default function DriversPage() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [form, setForm] = useState<DriverForm>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const loadDrivers = useCallback(async () => {
    const response = await fetch("/drivers", { cache: "no-store" });
    if (!response.ok) throw new Error("Не вдалося завантажити список водіїв.");
    setDrivers((await response.json()) as Driver[]);
  }, []);

  useEffect(() => {
    loadDrivers().catch((reason) =>
      setError(reason instanceof Error ? reason.message : "Невідома помилка"),
    );
  }, [loadDrivers]);

  function edit(driver: Driver) {
    setEditingId(driver.id);
    setForm({
      personnel_number: driver.personnel_number,
      last_name: driver.last_name,
      first_name: driver.first_name,
      middle_name: driver.middle_name ?? "",
      phone: driver.phone ?? "",
      employment_status: driver.employment_status,
    });
    setMessage(null);
    setError(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function resetForm() {
    setEditingId(null);
    setForm(emptyForm);
    setError(null);
    setMessage(null);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const payload = {
        ...form,
        middle_name: form.middle_name.trim() || null,
        phone: form.phone.trim() || null,
      };
      const response = await fetch(editingId ? `/drivers/${editingId}` : "/drivers", {
        method: editingId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(body?.detail ?? "Не вдалося зберегти водія.");
      }
      setMessage(editingId ? "Дані водія оновлено." : "Водія додано.");
      setEditingId(null);
      setForm(emptyForm);
      await loadDrivers();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Невідома помилка");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="app-page">
      <div className="page-toolbar">
        <div>
          <p className="eyebrow">Персонал</p>
          <h1>Водії</h1>
          <p className="subtitle">Картотека водіїв підприємства</p>
        </div>
        <div className="page-toolbar-actions">
          <button className="button secondary" onClick={resetForm} type="button">
            Новий водій
          </button>
          <Link className="button secondary" href="/">
            На головну
          </Link>
        </div>
      </div>

      <section className="panel">
        <h2>{editingId ? "Редагування водія" : "Додати водія"}</h2>
        {message ? <p className="notice success">{message}</p> : null}
        {error ? <p className="notice error">{error}</p> : null}
        <form onSubmit={submit}>
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="personnel-number">Табельний номер</label>
              <input
                id="personnel-number"
                onChange={(event) => setForm({ ...form, personnel_number: event.target.value })}
                required
                value={form.personnel_number}
              />
            </div>
            <div className="form-field">
              <label htmlFor="phone">Телефон</label>
              <input
                id="phone"
                onChange={(event) => setForm({ ...form, phone: event.target.value })}
                value={form.phone}
              />
            </div>
            <div className="form-field">
              <label htmlFor="last-name">Прізвище</label>
              <input
                id="last-name"
                onChange={(event) => setForm({ ...form, last_name: event.target.value })}
                required
                value={form.last_name}
              />
            </div>
            <div className="form-field">
              <label htmlFor="first-name">Ім’я</label>
              <input
                id="first-name"
                onChange={(event) => setForm({ ...form, first_name: event.target.value })}
                required
                value={form.first_name}
              />
            </div>
            <div className="form-field">
              <label htmlFor="middle-name">По батькові</label>
              <input
                id="middle-name"
                onChange={(event) => setForm({ ...form, middle_name: event.target.value })}
                value={form.middle_name}
              />
            </div>
            <div className="form-field">
              <label htmlFor="driver-status">Статус</label>
              <select
                id="driver-status"
                onChange={(event) =>
                  setForm({ ...form, employment_status: event.target.value as DriverStatus })
                }
                value={form.employment_status}
              >
                {Object.entries(statusLabels).map(([code, label]) => (
                  <option key={code} value={code}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="form-actions">
            <button className="button" disabled={saving} type="submit">
              {saving ? "Збереження..." : editingId ? "Зберегти зміни" : "Додати водія"}
            </button>
            {editingId ? (
              <button className="button secondary" onClick={resetForm} type="button">
                Скасувати
              </button>
            ) : null}
          </div>
        </form>
      </section>

      <section className="panel">
        <h2>Водії — {drivers.length}</h2>
        {drivers.length === 0 ? (
          <p className="muted">Водіїв ще немає. Додайте першого водія вище.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Табельний</th>
                  <th>ПІБ</th>
                  <th>Телефон</th>
                  <th>Статус</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {drivers.map((driver) => (
                  <tr key={driver.id}>
                    <td><strong>{driver.personnel_number}</strong></td>
                    <td>{[driver.last_name, driver.first_name, driver.middle_name].filter(Boolean).join(" ")}</td>
                    <td>{driver.phone ?? "—"}</td>
                    <td>{statusLabels[driver.employment_status]}</td>
                    <td>
                      <button className="button secondary" onClick={() => edit(driver)} type="button">
                        Редагувати
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
