"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";

type VehicleStatus = "ACTIVE" | "SUSPENDED" | "REPAIR" | "DECOMMISSIONED";

type Vehicle = {
  id: string;
  fleet_number: string;
  registration_number: string;
  vin: string | null;
  make: string;
  model: string;
  year: number | null;
  lifecycle_status: VehicleStatus;
  row_version: number;
};

type VehicleForm = {
  fleet_number: string;
  registration_number: string;
  vin: string;
  make: string;
  model: string;
  year: string;
  lifecycle_status: VehicleStatus;
};

const emptyForm: VehicleForm = {
  fleet_number: "",
  registration_number: "",
  vin: "",
  make: "",
  model: "",
  year: "",
  lifecycle_status: "ACTIVE",
};

const statusLabels: Record<VehicleStatus, string> = {
  ACTIVE: "Активний",
  SUSPENDED: "Призупинений",
  REPAIR: "Ремонт",
  DECOMMISSIONED: "Списаний",
};

export default function VehiclesPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [form, setForm] = useState<VehicleForm>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const loadVehicles = useCallback(async () => {
    const response = await fetch("/api/vehicles", { cache: "no-store" });
    if (!response.ok) throw new Error("Не вдалося завантажити парк автобусів.");
    setVehicles((await response.json()) as Vehicle[]);
  }, []);

  useEffect(() => {
    loadVehicles().catch((reason) =>
      setError(reason instanceof Error ? reason.message : "Невідома помилка"),
    );
  }, [loadVehicles]);

  function edit(vehicle: Vehicle) {
    setEditingId(vehicle.id);
    setForm({
      fleet_number: vehicle.fleet_number,
      registration_number: vehicle.registration_number,
      vin: vehicle.vin ?? "",
      make: vehicle.make,
      model: vehicle.model,
      year: vehicle.year?.toString() ?? "",
      lifecycle_status: vehicle.lifecycle_status,
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
        vin: form.vin.trim() || null,
        year: form.year.trim() ? Number(form.year) : null,
      };
      const response = await fetch(editingId ? `/api/vehicles/${editingId}` : "/api/vehicles", {
        method: editingId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(body?.detail ?? "Не вдалося зберегти автобус.");
      }
      setMessage(editingId ? "Дані автобуса оновлено." : "Автобус додано до парку.");
      setEditingId(null);
      setForm(emptyForm);
      await loadVehicles();
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
          <p className="eyebrow">Парк</p>
          <h1>Автобуси</h1>
          <p className="subtitle">Картотека автобусів підприємства</p>
        </div>
        <div className="page-toolbar-actions">
          <button className="button secondary" onClick={resetForm} type="button">
            Новий автобус
          </button>
          <Link className="button secondary" href="/">
            На головну
          </Link>
        </div>
      </div>

      <section className="panel">
        <h2>{editingId ? "Редагування автобуса" : "Додати автобус"}</h2>
        {message ? <p className="notice success">{message}</p> : null}
        {error ? <p className="notice error">{error}</p> : null}
        <form onSubmit={submit}>
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="fleet-number">Гаражний номер</label>
              <input
                id="fleet-number"
                onChange={(event) => setForm({ ...form, fleet_number: event.target.value })}
                required
                value={form.fleet_number}
              />
            </div>
            <div className="form-field">
              <label htmlFor="registration-number">Державний номер</label>
              <input
                id="registration-number"
                onChange={(event) => setForm({ ...form, registration_number: event.target.value })}
                required
                value={form.registration_number}
              />
            </div>
            <div className="form-field">
              <label htmlFor="make">Марка</label>
              <input
                id="make"
                onChange={(event) => setForm({ ...form, make: event.target.value })}
                required
                value={form.make}
              />
            </div>
            <div className="form-field">
              <label htmlFor="model">Модель</label>
              <input
                id="model"
                onChange={(event) => setForm({ ...form, model: event.target.value })}
                required
                value={form.model}
              />
            </div>
            <div className="form-field">
              <label htmlFor="vin">VIN</label>
              <input
                id="vin"
                onChange={(event) => setForm({ ...form, vin: event.target.value })}
                value={form.vin}
              />
            </div>
            <div className="form-field">
              <label htmlFor="year">Рік випуску</label>
              <input
                id="year"
                max="2100"
                min="1950"
                onChange={(event) => setForm({ ...form, year: event.target.value })}
                type="number"
                value={form.year}
              />
            </div>
            <div className="form-field full">
              <label htmlFor="vehicle-status">Стан</label>
              <select
                id="vehicle-status"
                onChange={(event) =>
                  setForm({ ...form, lifecycle_status: event.target.value as VehicleStatus })
                }
                value={form.lifecycle_status}
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
              {saving ? "Збереження..." : editingId ? "Зберегти зміни" : "Додати автобус"}
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
        <h2>Парк автобусів — {vehicles.length}</h2>
        {vehicles.length === 0 ? (
          <p className="muted">Автобусів ще немає. Додайте перший автобус вище.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Гаражний</th>
                  <th>Держ. номер</th>
                  <th>Автобус</th>
                  <th>Рік</th>
                  <th>Стан</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {vehicles.map((vehicle) => (
                  <tr key={vehicle.id}>
                    <td><strong>{vehicle.fleet_number}</strong></td>
                    <td>{vehicle.registration_number}</td>
                    <td>{vehicle.make} {vehicle.model}</td>
                    <td>{vehicle.year ?? "—"}</td>
                    <td>{statusLabels[vehicle.lifecycle_status]}</td>
                    <td>
                      <div className="page-toolbar-actions">
                        <Link className="button secondary" href={`/vehicle-card/?id=${vehicle.id}`}>
                          Картка
                        </Link>
                        <button className="button secondary" onClick={() => edit(vehicle)} type="button">
                          Редагувати
                        </button>
                      </div>
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
