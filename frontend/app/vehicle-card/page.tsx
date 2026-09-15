"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";

type DocumentItem = {
  id: string;
  document_type: string;
  number: string;
  valid_until: string | null;
  note: string | null;
};

type OdometerItem = {
  id: string;
  reading_km: number;
  recorded_at: string;
  note: string | null;
};

type VehicleDetails = {
  id: string;
  fleet_number: string;
  registration_number: string;
  vin: string | null;
  make: string;
  model: string;
  year: number | null;
  lifecycle_status: string;
  documents: DocumentItem[];
  odometer: OdometerItem[];
};

function getId(): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get("id");
}

export default function VehicleCardPage() {
  const [vehicleId, setVehicleId] = useState<string | null>(null);
  const [vehicle, setVehicle] = useState<VehicleDetails | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [documentType, setDocumentType] = useState("");
  const [documentNumber, setDocumentNumber] = useState("");
  const [validUntil, setValidUntil] = useState("");
  const [documentNote, setDocumentNote] = useState("");
  const [readingKm, setReadingKm] = useState("");
  const [odometerNote, setOdometerNote] = useState("");

  const load = useCallback(async (id: string) => {
    const response = await fetch(`/api/vehicles/${id}/details`, { cache: "no-store" });
    if (!response.ok) throw new Error("Не вдалося завантажити картку автобуса.");
    setVehicle((await response.json()) as VehicleDetails);
  }, []);

  useEffect(() => {
    const id = getId();
    setVehicleId(id);
    if (!id) {
      setError("Не вказано автобус.");
      return;
    }
    load(id).catch((reason) =>
      setError(reason instanceof Error ? reason.message : "Невідома помилка"),
    );
  }, [load]);

  async function addDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!vehicleId) return;
    setError(null);
    setMessage(null);
    const response = await fetch(`/api/vehicles/${vehicleId}/documents`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        document_type: documentType,
        number: documentNumber,
        valid_until: validUntil || null,
        note: documentNote.trim() || null,
      }),
    });
    if (!response.ok) {
      const body = (await response.json().catch(() => null)) as { detail?: string } | null;
      setError(body?.detail ?? "Не вдалося додати документ.");
      return;
    }
    setDocumentType("");
    setDocumentNumber("");
    setValidUntil("");
    setDocumentNote("");
    setMessage("Документ додано.");
    await load(vehicleId);
  }

  async function addOdometer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!vehicleId) return;
    setError(null);
    setMessage(null);
    const response = await fetch(`/api/vehicles/${vehicleId}/odometer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        reading_km: Number(readingKm),
        note: odometerNote.trim() || null,
      }),
    });
    if (!response.ok) {
      const body = (await response.json().catch(() => null)) as { detail?: string } | null;
      setError(body?.detail ?? "Не вдалося додати показання одометра.");
      return;
    }
    setReadingKm("");
    setOdometerNote("");
    setMessage("Показання одометра додано.");
    await load(vehicleId);
  }

  return (
    <main className="app-page">
      <div className="page-toolbar">
        <div>
          <p className="eyebrow">Парк</p>
          <h1>Картка автобуса</h1>
          {vehicle ? (
            <p className="subtitle">
              {vehicle.fleet_number} · {vehicle.registration_number} · {vehicle.make} {vehicle.model}
            </p>
          ) : null}
        </div>
        <Link className="button secondary" href="/vehicles/">До списку автобусів</Link>
      </div>

      {message ? <p className="notice success">{message}</p> : null}
      {error ? <p className="notice error">{error}</p> : null}

      {vehicle ? (
        <>
          <section className="panel">
            <h2>Основні дані</h2>
            <div className="info-grid">
              <div className="info-item"><strong>Гаражний номер</strong><span>{vehicle.fleet_number}</span></div>
              <div className="info-item"><strong>Державний номер</strong><span>{vehicle.registration_number}</span></div>
              <div className="info-item"><strong>Автобус</strong><span>{vehicle.make} {vehicle.model}</span></div>
              <div className="info-item"><strong>Рік</strong><span>{vehicle.year ?? "—"}</span></div>
              <div className="info-item"><strong>VIN</strong><span>{vehicle.vin ?? "—"}</span></div>
              <div className="info-item"><strong>Стан</strong><span>{vehicle.lifecycle_status}</span></div>
            </div>
          </section>

          <section className="panel">
            <h2>Одометр</h2>
            <form onSubmit={addOdometer}>
              <div className="form-grid">
                <div className="form-field">
                  <label htmlFor="reading-km">Показання, км</label>
                  <input id="reading-km" min="0" required type="number" value={readingKm} onChange={(event) => setReadingKm(event.target.value)} />
                </div>
                <div className="form-field">
                  <label htmlFor="odometer-note">Примітка</label>
                  <input id="odometer-note" value={odometerNote} onChange={(event) => setOdometerNote(event.target.value)} />
                </div>
              </div>
              <div className="form-actions"><button className="button" type="submit">Додати показання</button></div>
            </form>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Дата</th><th>Показання</th><th>Примітка</th></tr></thead>
                <tbody>
                  {vehicle.odometer.map((item) => (
                    <tr key={item.id}><td>{new Date(item.recorded_at).toLocaleString("uk-UA")}</td><td>{item.reading_km.toLocaleString("uk-UA")} км</td><td>{item.note ?? "—"}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel">
            <h2>Документи</h2>
            <form onSubmit={addDocument}>
              <div className="form-grid">
                <div className="form-field"><label htmlFor="document-type">Тип документа</label><input id="document-type" required value={documentType} onChange={(event) => setDocumentType(event.target.value)} /></div>
                <div className="form-field"><label htmlFor="document-number">Номер</label><input id="document-number" required value={documentNumber} onChange={(event) => setDocumentNumber(event.target.value)} /></div>
                <div className="form-field"><label htmlFor="valid-until">Дійсний до</label><input id="valid-until" type="date" value={validUntil} onChange={(event) => setValidUntil(event.target.value)} /></div>
                <div className="form-field"><label htmlFor="document-note">Примітка</label><input id="document-note" value={documentNote} onChange={(event) => setDocumentNote(event.target.value)} /></div>
              </div>
              <div className="form-actions"><button className="button" type="submit">Додати документ</button></div>
            </form>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Документ</th><th>Номер</th><th>Дійсний до</th><th>Примітка</th></tr></thead>
                <tbody>
                  {vehicle.documents.map((item) => (
                    <tr key={item.id}><td>{item.document_type}</td><td>{item.number}</td><td>{item.valid_until ? new Date(`${item.valid_until}T00:00:00`).toLocaleDateString("uk-UA") : "—"}</td><td>{item.note ?? "—"}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ) : null}
    </main>
  );
}
