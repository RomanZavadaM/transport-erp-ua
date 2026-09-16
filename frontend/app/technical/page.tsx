"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { useEffect, useState } from "react";

type Vehicle = {
  id: string;
  fleet_number: string;
  registration_number: string;
  make: string;
  model: string;
  lifecycle_status: string;
};

export default function TechnicalPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/vehicles", { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("Не вдалося завантажити парк.");
        return response.json() as Promise<Vehicle[]>;
      })
      .then(setVehicles)
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Невідома помилка"));
  }, []);

  return (
    <main className="app-page">
      <div className="page-toolbar">
        <div>
          <p className="eyebrow">Технічна служба</p>
          <h1>СТОІР, дефекти і ремонти</h1>
          <p className="subtitle">Технічний стан парку, планове ТО та ремонтна історія</p>
        </div>
        <Link className="button secondary" href="/">На головну</Link>
      </div>

      {error ? <p className="notice error">{error}</p> : null}

      <section className="panel">
        <h2>Парк — {vehicles.length}</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Гаражний №</th>
                <th>Держ. номер</th>
                <th>Автобус</th>
                <th>Стан</th>
                <th>Технічні дії</th>
              </tr>
            </thead>
            <tbody>
              {vehicles.length === 0 ? (
                <tr><td colSpan={5} className="muted">Автобусів ще немає.</td></tr>
              ) : vehicles.map((vehicle) => (
                <tr key={vehicle.id}>
                  <td><strong>{vehicle.fleet_number}</strong></td>
                  <td>{vehicle.registration_number}</td>
                  <td>{vehicle.make} {vehicle.model}</td>
                  <td>{vehicle.lifecycle_status}</td>
                  <td>
                    <div className="form-actions compact-actions">
                      <Link className="button secondary" href={`/stoir/?id=${encodeURIComponent(vehicle.id)}`}>СТОІР</Link>
                      <Link className="button secondary" href={`/repairs/?id=${encodeURIComponent(vehicle.id)}`}>Дефекти / ремонти</Link>
                      <Link className="button secondary" href={`/vehicle-card/?id=${encodeURIComponent(vehicle.id)}`}>Картка</Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
