"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

type Company = {
  id: string;
  name: string;
  edrpou: string | null;
};

export default function SettingsPage() {
  const [name, setName] = useState("");
  const [edrpou, setEdrpou] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/company", { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("Не вдалося завантажити дані підприємства.");
        return (await response.json()) as Company;
      })
      .then((company) => {
        setName(company.name);
        setEdrpou(company.edrpou ?? "");
      })
      .catch((reason) =>
        setError(reason instanceof Error ? reason.message : "Невідома помилка"),
      );
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const response = await fetch("/api/company", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, edrpou: edrpou.trim() || null }),
      });
      if (!response.ok) throw new Error("Не вдалося зберегти дані підприємства.");
      const company = (await response.json()) as Company;
      setName(company.name);
      setEdrpou(company.edrpou ?? "");
      setMessage("Дані підприємства збережено.");
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
          <p className="eyebrow">Налаштування</p>
          <h1>Підприємство</h1>
          <p className="subtitle">Основні реквізити локальної бази</p>
        </div>
        <Link className="button secondary" href="/">
          На головну
        </Link>
      </div>

      <section className="panel">
        <h2>Основні дані</h2>
        {message ? <p className="notice success">{message}</p> : null}
        {error ? <p className="notice error">{error}</p> : null}
        <form onSubmit={submit}>
          <div className="form-grid">
            <div className="form-field full">
              <label htmlFor="company-name">Назва підприємства</label>
              <input
                id="company-name"
                onChange={(event) => setName(event.target.value)}
                required
                value={name}
              />
            </div>
            <div className="form-field">
              <label htmlFor="edrpou">ЄДРПОУ</label>
              <input
                id="edrpou"
                inputMode="numeric"
                onChange={(event) => setEdrpou(event.target.value)}
                value={edrpou}
              />
            </div>
          </div>
          <div className="form-actions">
            <button className="button" disabled={saving} type="submit">
              {saving ? "Збереження..." : "Зберегти"}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
