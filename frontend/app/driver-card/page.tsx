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

type DriverDetails = {
  id: string;
  personnel_number: string;
  last_name: string;
  first_name: string;
  middle_name: string | null;
  phone: string | null;
  employment_status: string;
  documents: DocumentItem[];
};

function getId(): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get("id");
}

export default function DriverCardPage() {
  const [driverId, setDriverId] = useState<string | null>(null);
  const [driver, setDriver] = useState<DriverDetails | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [documentType, setDocumentType] = useState("");
  const [documentNumber, setDocumentNumber] = useState("");
  const [validUntil, setValidUntil] = useState("");
  const [documentNote, setDocumentNote] = useState("");

  const load = useCallback(async (id: string) => {
    const response = await fetch(`/api/drivers/${id}/details`, { cache: "no-store" });
    if (!response.ok) throw new Error("Не вдалося завантажити картку водія.");
    setDriver((await response.json()) as DriverDetails);
  }, []);

  useEffect(() => {
    const id = getId();
    setDriverId(id);
    if (!id) {
      setError("Не вказано водія.");
      return;
    }
    load(id).catch((reason) =>
      setError(reason instanceof Error ? reason.message : "Невідома помилка"),
    );
  }, [load]);

  async function addDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!driverId) return;
    setError(null);
    setMessage(null);
    const response = await fetch(`/api/drivers/${driverId}/documents`, {
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
    await load(driverId);
  }

  return (
    <main className="app-page">
      <div className="page-toolbar">
        <div>
          <p className="eyebrow">Персонал</p>
          <h1>Картка водія</h1>
          {driver ? (
            <p className="subtitle">
              {driver.last_name} {driver.first_name} {driver.middle_name ?? ""}
            </p>
          ) : null}
        </div>
        <Link className="button secondary" href="/drivers/">До списку водіїв</Link>
      </div>

      {message ? <p className="notice success">{message}</p> : null}
      {error ? <p className="notice error">{error}</p> : null}

      {driver ? (
        <>
          <section className="panel">
            <h2>Основні дані</h2>
            <div className="info-grid">
              <div className="info-item"><strong>Табельний номер</strong><span>{driver.personnel_number}</span></div>
              <div className="info-item"><strong>Статус</strong><span>{driver.employment_status}</span></div>
              <div className="info-item"><strong>ПІБ</strong><span>{[driver.last_name, driver.first_name, driver.middle_name].filter(Boolean).join(" ")}</span></div>
              <div className="info-item"><strong>Телефон</strong><span>{driver.phone ?? "—"}</span></div>
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
            {driver.documents.length === 0 ? <p className="muted">Документів ще немає.</p> : (
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Документ</th><th>Номер</th><th>Дійсний до</th><th>Примітка</th></tr></thead>
                  <tbody>
                    {driver.documents.map((item) => (
                      <tr key={item.id}><td>{item.document_type}</td><td>{item.number}</td><td>{item.valid_until ? new Date(`${item.valid_until}T00:00:00`).toLocaleDateString("uk-UA") : "—"}</td><td>{item.note ?? "—"}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      ) : null}
    </main>
  );
}
