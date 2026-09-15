"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

type Stop = { id: string; name: string; locality: string | null; active: boolean };
type RouteStop = { id: string; name: string; locality: string | null; position: number };
type Route = { id: string; number: string; name: string; active: boolean; stops: RouteStop[] };

export default function RoutesPage() {
  const [stops, setStops] = useState<Stop[]>([]);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [stopName, setStopName] = useState("");
  const [stopLocality, setStopLocality] = useState("");
  const [routeNumber, setRouteNumber] = useState("");
  const [routeName, setRouteName] = useState("");
  const [routeStopIds, setRouteStopIds] = useState<string[]>([]);
  const [selectedStopId, setSelectedStopId] = useState("");
  const [editingRouteId, setEditingRouteId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [stopsResponse, routesResponse] = await Promise.all([
      fetch("/api/stops", { cache: "no-store" }),
      fetch("/api/routes", { cache: "no-store" }),
    ]);
    if (!stopsResponse.ok || !routesResponse.ok) throw new Error("Не вдалося завантажити маршрути.");
    setStops((await stopsResponse.json()) as Stop[]);
    setRoutes((await routesResponse.json()) as Route[]);
  }, []);

  useEffect(() => {
    load().catch((reason) => setError(reason instanceof Error ? reason.message : "Невідома помилка"));
  }, [load]);

  const activeStops = useMemo(() => stops.filter((stop) => stop.active), [stops]);
  const stopById = useMemo(() => new Map(stops.map((stop) => [stop.id, stop])), [stops]);

  async function addStop(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    const response = await fetch("/api/stops", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: stopName, locality: stopLocality.trim() || null, active: true }),
    });
    if (!response.ok) {
      const body = (await response.json().catch(() => null)) as { detail?: string } | null;
      setError(body?.detail ?? "Не вдалося додати зупинку.");
      return;
    }
    setStopName("");
    setStopLocality("");
    setMessage("Зупинку додано.");
    await load();
  }

  function appendStop() {
    if (!selectedStopId || routeStopIds.includes(selectedStopId)) return;
    setRouteStopIds([...routeStopIds, selectedStopId]);
    setSelectedStopId("");
  }

  function moveStop(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= routeStopIds.length) return;
    const next = [...routeStopIds];
    [next[index], next[target]] = [next[target], next[index]];
    setRouteStopIds(next);
  }

  function editRoute(route: Route) {
    setEditingRouteId(route.id);
    setRouteNumber(route.number);
    setRouteName(route.name);
    setRouteStopIds(route.stops.map((stop) => stop.id));
    setMessage(null);
    setError(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function resetRoute() {
    setEditingRouteId(null);
    setRouteNumber("");
    setRouteName("");
    setRouteStopIds([]);
    setSelectedStopId("");
  }

  async function saveRoute(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    if (routeStopIds.length < 2) {
      setError("Маршрут повинен містити щонайменше дві зупинки.");
      return;
    }
    const response = await fetch(editingRouteId ? `/api/routes/${editingRouteId}` : "/api/routes", {
      method: editingRouteId ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ number: routeNumber, name: routeName, active: true, stop_ids: routeStopIds }),
    });
    if (!response.ok) {
      const body = (await response.json().catch(() => null)) as { detail?: string } | null;
      setError(body?.detail ?? "Не вдалося зберегти маршрут.");
      return;
    }
    setMessage(editingRouteId ? "Маршрут оновлено." : "Маршрут створено.");
    resetRoute();
    await load();
  }

  return (
    <main className="app-page">
      <div className="page-toolbar">
        <div><p className="eyebrow">Планування</p><h1>Маршрути і зупинки</h1></div>
        <Link className="button secondary" href="/">На головну</Link>
      </div>
      {message ? <p className="notice success">{message}</p> : null}
      {error ? <p className="notice error">{error}</p> : null}

      <section className="panel">
        <h2>{editingRouteId ? "Редагувати маршрут" : "Новий маршрут"}</h2>
        <form onSubmit={saveRoute}>
          <div className="form-grid">
            <div className="form-field"><label htmlFor="route-number">Номер</label><input id="route-number" required value={routeNumber} onChange={(event) => setRouteNumber(event.target.value)} /></div>
            <div className="form-field"><label htmlFor="route-name">Назва</label><input id="route-name" required value={routeName} onChange={(event) => setRouteName(event.target.value)} /></div>
          </div>
          <div className="route-builder">
            <div className="route-add-stop">
              <select value={selectedStopId} onChange={(event) => setSelectedStopId(event.target.value)}>
                <option value="">Виберіть зупинку</option>
                {activeStops.filter((stop) => !routeStopIds.includes(stop.id)).map((stop) => <option key={stop.id} value={stop.id}>{stop.name}{stop.locality ? ` — ${stop.locality}` : ""}</option>)}
              </select>
              <button className="button secondary" type="button" onClick={appendStop}>Додати до маршруту</button>
            </div>
            {routeStopIds.length === 0 ? <p className="muted">Додайте зупинки у порядку руху.</p> : (
              <ol className="route-stop-list">
                {routeStopIds.map((id, index) => {
                  const stop = stopById.get(id);
                  return <li key={id}><span><strong>{stop?.name ?? id}</strong>{stop?.locality ? ` — ${stop.locality}` : ""}</span><div className="inline-actions"><button type="button" className="mini-button" onClick={() => moveStop(index, -1)} disabled={index === 0}>↑</button><button type="button" className="mini-button" onClick={() => moveStop(index, 1)} disabled={index === routeStopIds.length - 1}>↓</button><button type="button" className="mini-button danger" onClick={() => setRouteStopIds(routeStopIds.filter((item) => item !== id))}>×</button></div></li>;
                })}
              </ol>
            )}
          </div>
          <div className="form-actions"><button className="button" type="submit">{editingRouteId ? "Зберегти зміни" : "Створити маршрут"}</button>{editingRouteId ? <button className="button secondary" type="button" onClick={resetRoute}>Скасувати</button> : null}</div>
        </form>
      </section>

      <section className="panel">
        <h2>Маршрути — {routes.length}</h2>
        <div className="table-wrap"><table><thead><tr><th>№</th><th>Назва</th><th>Зупинки</th><th></th></tr></thead><tbody>{routes.map((route) => <tr key={route.id}><td><strong>{route.number}</strong></td><td>{route.name}</td><td>{route.stops.map((stop) => stop.name).join(" → ")}</td><td><button className="button secondary" type="button" onClick={() => editRoute(route)}>Редагувати</button></td></tr>)}</tbody></table></div>
      </section>

      <section className="panel">
        <h2>Довідник зупинок — {stops.length}</h2>
        <form onSubmit={addStop}>
          <div className="form-grid"><div className="form-field"><label htmlFor="stop-name">Назва зупинки</label><input id="stop-name" required value={stopName} onChange={(event) => setStopName(event.target.value)} /></div><div className="form-field"><label htmlFor="stop-locality">Населений пункт</label><input id="stop-locality" value={stopLocality} onChange={(event) => setStopLocality(event.target.value)} /></div></div>
          <div className="form-actions"><button className="button" type="submit">Додати зупинку</button></div>
        </form>
        <div className="table-wrap"><table><thead><tr><th>Зупинка</th><th>Населений пункт</th></tr></thead><tbody>{stops.map((stop) => <tr key={stop.id}><td>{stop.name}</td><td>{stop.locality ?? "—"}</td></tr>)}</tbody></table></div>
      </section>
    </main>
  );
}
