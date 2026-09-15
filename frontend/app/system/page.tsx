"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

type LocalStatus = {
  profile: string;
  database_path: string;
  documents_path: string;
  backup_path: string;
  database_size_bytes: number;
  integrity: string;
};

type Backup = {
  path: string;
  size_bytes: number;
  created_at: string;
};

function formatBytes(value: number): string {
  if (value < 1024) return `${value} Б`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} КБ`;
  return `${(value / (1024 * 1024)).toFixed(1)} МБ`;
}

export default function SystemPage() {
  const [status, setStatus] = useState<LocalStatus | null>(null);
  const [backups, setBackups] = useState<Backup[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [creatingBackup, setCreatingBackup] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const [statusResponse, backupsResponse] = await Promise.all([
        fetch("/api/local/status", { cache: "no-store" }),
        fetch("/api/local/backups", { cache: "no-store" }),
      ]);
      if (!statusResponse.ok || !backupsResponse.ok) {
        throw new Error("Не вдалося отримати стан локальної системи.");
      }
      setStatus((await statusResponse.json()) as LocalStatus);
      setBackups((await backupsResponse.json()) as Backup[]);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Невідома помилка");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function createBackup() {
    try {
      setCreatingBackup(true);
      setMessage(null);
      setError(null);
      const response = await fetch("/api/local/backup", { method: "POST" });
      if (!response.ok) {
        throw new Error("Не вдалося створити резервну копію.");
      }
      const backup = (await response.json()) as Backup;
      setMessage(`Резервну копію створено: ${backup.path}`);
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Невідома помилка");
    } finally {
      setCreatingBackup(false);
    }
  }

  return (
    <main className="app-page">
      <div className="page-toolbar">
        <div>
          <p className="eyebrow">Локальний застосунок</p>
          <h1>Стан системи</h1>
        </div>
        <div className="page-toolbar-actions">
          <button className="button" disabled={creatingBackup} onClick={createBackup} type="button">
            {creatingBackup ? "Створення..." : "Створити резервну копію"}
          </button>
          <Link className="button secondary" href="/">
            На головну
          </Link>
        </div>
      </div>

      {message ? <p className="notice success">{message}</p> : null}
      {error ? <p className="notice error">{error}</p> : null}

      <section className="panel">
        <h2>Локальне сховище</h2>
        {status ? (
          <div className="info-grid">
            <div className="info-item">
              <strong>Режим</strong>
              <span>{status.profile === "local" ? "Локальний" : status.profile}</span>
            </div>
            <div className="info-item">
              <strong>Перевірка SQLite</strong>
              <span>{status.integrity === "ok" ? "Справна" : status.integrity}</span>
            </div>
            <div className="info-item">
              <strong>База даних</strong>
              <span>{status.database_path}</span>
              <span>{formatBytes(status.database_size_bytes)}</span>
            </div>
            <div className="info-item">
              <strong>Документи</strong>
              <span>{status.documents_path}</span>
            </div>
            <div className="info-item full">
              <strong>Резервні копії</strong>
              <span>{status.backup_path}</span>
            </div>
          </div>
        ) : (
          <p className="muted">Завантаження стану...</p>
        )}
      </section>

      <section className="panel">
        <h2>Останні резервні копії</h2>
        {backups.length === 0 ? (
          <p className="muted">Резервних копій ще немає.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Розмір</th>
                  <th>Файл</th>
                </tr>
              </thead>
              <tbody>
                {backups.map((backup) => (
                  <tr key={backup.path}>
                    <td>{new Date(backup.created_at).toLocaleString("uk-UA")}</td>
                    <td>{formatBytes(backup.size_bytes)}</td>
                    <td>{backup.path}</td>
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
