"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

type Route = { id: string; number: string; name: string; active: boolean };
type Schedule = {
  id: string;
  route_id: string;
  route_number: string;
  route_name: string;
  departure_time: string;
  arrival_time: string;
  active: boolean;
};
type Vehicle = {
  id: string;
  fleet_number: string;
  registration_number: string;
  lifecycle_status: string;
};
type Driver = {
  id: string;
  personnel_number: string;
  last_name: string;
  first_name: string;
  middle_name: string | null;
  employment_status: string;
};
type Trip = {
  id: string;
  route_number: string;
  route_name: string;
  planned_departure: string;
  planned_arrival: string;
  status: string;
  duty_id: string | null;
  duty_number: string | null;
};
type DutyTrip = {
  id: string;
  route_number: string;
  route_name: string;
  planned_departure: string;
  planned_arrival: string;
};
type Duty = {
  id: string;
  duty_number: string;
  vehicle_label: string;
  driver_label: string;
  status: string;
  trips: DutyTrip[];
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

export default function OperationsPage() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [serviceDate, setServiceDate] = useState(todayLocal());
  const [trips, setTrips] = useState<Trip[]>([]);
  const [duties, setDuties] = useState<Duty[]>([]);
  const [scheduleRouteId, setScheduleRouteId] = useState("");
  const [departureTime, setDepartureTime] = useState("06:00");
  const [arrivalTime, setArrivalTime] = useState("07:00");
  const [selectedTripIds, setSelectedTripIds] = useState<string[]>([]);
  const [dutyNumber, setDutyNumber] = useState("");
  const [vehicleId, setVehicleId] = useState("");
  const [driverId, setDriverId] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadCatalogs = useCallback(async () => {
    const [routesResponse, schedulesResponse, vehiclesResponse, driversResponse] = await Promise.all([
      fetch("/api/routes", { cache: "no-store" }),
      fetch("/api/schedules", { cache: "no-store" }),
      fetch("/api/vehicles", { cache: "no-store" }),
      fetch("/api/drivers", { cache: "no-store" }),
    ]);
    if (![routesResponse, schedulesResponse, vehiclesResponse, driversResponse].every((item) => item.ok)) {
      throw new Error("Не вдалося завантажити оперативні довідники.");
    }
    setRoutes((await routesResponse.json()) as Route[]);
    setSchedules((await schedulesResponse.json()) as Schedule[]);
    setVehicles((await vehiclesResponse.json()) as Vehicle[]);
    setDrivers((await driversResponse.json()) as Driver[]);
  }, []);

  const loadDay = useCallback(async (dateValue: string) => {
    const encoded = encodeURIComponent(dateValue);
    const [tripsResponse, dutiesResponse] = await Promise.all([
      fetch(`/api/trips?service_date=${encoded}`, { cache: "no-store" }),
      fetch(`/api/duties?service_date=${encoded}`, { cache: "no-store" }),
    ]);
    if (!tripsResponse.ok || !dutiesResponse.ok) throw new Error("Не вдалося завантажити роботу на дату.");
    setTrips((await tripsResponse.json()) as Trip[]);
    setDuties((await dutiesResponse.json()) as Duty[]);
  }, []);

  useEffect(() => {
    loadCatalogs().catch((reason) => setError(reason instanceof Error ? reason.message : "Невідома помилка"));
  }, [loadCatalogs]);

  useEffect(() => {
    setSelectedTripIds([]);
    loadDay(serviceDate).catch((reason) => setError(reason instanceof Error ? reason.message : "Невідома помилка"));
  }, [loadDay, serviceDate]);

  const activeRoutes = useMemo(() => routes.filter((route) => route.active), [routes]);
  const activeVehicles = useMemo(
    () => vehicles.filter((vehicle) => vehicle.lifecycle_status === "ACTIVE"),
    [vehicles],
  );
  const activeDrivers = useMemo(
    () => drivers.filter((driver) => driver.employment_status === "ACTIVE"),
    [drivers],
  );

  async function addSchedule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    const response = await fetch("/api/schedules", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        route_id: scheduleRouteId,
        departure_time: departureTime,
        arrival_time: arrivalTime,
        active: true,
      }),
    });
    if (!response.ok) {
      setError(await apiError(response, "Не вдалося додати рейс до розкладу."));
      return;
    }
    setMessage("Рейс додано до розкладу.");
    await loadCatalogs();
  }

  async function generateTrips() {
    setError(null);
    setMessage(null);
    const response = await fetch("/api/trips/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ service_date: serviceDate }),
    });
    if (!response.ok) {
      setError(await apiError(response, "Не вдалося сформувати рейси."));
      return;
    }
    setMessage("Рейси на дату сформовано/оновлено.");
    setSelectedTripIds([]);
    await loadDay(serviceDate);
  }

  function toggleTrip(tripId: string) {
    setSelectedTripIds((current) =>
      current.includes(tripId) ? current.filter((item) => item !== tripId) : [...current, tripId],
    );
  }

  async function createDuty(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    if (selectedTripIds.length === 0) {
      setError("Виберіть хоча б один рейс для наряду.");
      return;
    }
    const response = await fetch("/api/duties", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        service_date: serviceDate,
        duty_number: dutyNumber,
        vehicle_id: vehicleId,
        driver_id: driverId,
        trip_ids: selectedTripIds,
      }),
    });
    if (!response.ok) {
      setError(await apiError(response, "Не вдалося створити наряд."));
      return;
    }
    setDutyNumber("");
    setSelectedTripIds([]);
    setMessage("Наряд створено.");
    await loadDay(serviceDate);
  }

  return (
    <main className="app-page">
      <div className="page-toolbar">
        <div>
          <p className="eyebrow">Диспетчерська</p>
          <h1>Наряди і рейси</h1>
        </div>
        <Link className="button secondary" href="/">На головну</Link>
      </div>

      {message ? <p className="notice success">{message}</p> : null}
      {error ? <p className="notice error">{error}</p> : null}

      <section className="panel">
        <div className="page-toolbar">
          <div>
            <h2>Робоча дата</h2>
            <p className="muted">Виберіть день, сформуйте рейси та призначте наряди.</p>
          </div>
          <div className="form-field">
            <label htmlFor="service-date">Дата</label>
            <input id="service-date" type="date" value={serviceDate} onChange={(event) => setServiceDate(event.target.value)} />
          </div>
        </div>
      </section>

      <section className="panel">
        <h2>Розклад рейсів</h2>
        <form onSubmit={addSchedule}>
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="schedule-route">Маршрут</label>
              <select id="schedule-route" required value={scheduleRouteId} onChange={(event) => setScheduleRouteId(event.target.value)}>
                <option value="">Виберіть маршрут</option>
                {activeRoutes.map((route) => <option key={route.id} value={route.id}>№ {route.number} — {route.name}</option>)}
              </select>
            </div>
            <div className="form-field">
              <label htmlFor="departure-time">Виїзд</label>
              <input id="departure-time" type="time" required value={departureTime} onChange={(event) => setDepartureTime(event.target.value)} />
            </div>
            <div className="form-field">
              <label htmlFor="arrival-time">Прибуття</label>
              <input id="arrival-time" type="time" required value={arrivalTime} onChange={(event) => setArrivalTime(event.target.value)} />
            </div>
          </div>
          <div className="form-actions"><button className="button" type="submit">Додати до розкладу</button></div>
        </form>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Маршрут</th><th>Виїзд</th><th>Прибуття</th></tr></thead>
            <tbody>
              {schedules.map((schedule) => <tr key={schedule.id}><td><strong>№ {schedule.route_number}</strong> — {schedule.route_name}</td><td>{schedule.departure_time}</td><td>{schedule.arrival_time}</td></tr>)}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="page-toolbar">
          <div><h2>Рейси на {serviceDate}</h2><p className="muted">Відмітьте рейси, які мають увійти до одного наряду.</p></div>
          <button className="button" type="button" onClick={generateTrips}>Сформувати рейси</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th></th><th>Час</th><th>Маршрут</th><th>Стан</th><th>Наряд</th></tr></thead>
            <tbody>
              {trips.length === 0 ? <tr><td colSpan={5} className="muted">На цю дату рейси ще не сформовані.</td></tr> : trips.map((trip) => {
                const available = trip.status === "PLANNED" && !trip.duty_id;
                return <tr key={trip.id}>
                  <td><input type="checkbox" aria-label={`Вибрати рейс ${trip.route_number} ${trip.planned_departure}`} disabled={!available} checked={selectedTripIds.includes(trip.id)} onChange={() => toggleTrip(trip.id)} /></td>
                  <td><strong>{trip.planned_departure}</strong>–{trip.planned_arrival}</td>
                  <td>№ {trip.route_number} — {trip.route_name}</td>
                  <td>{trip.status === "ASSIGNED" ? "Призначено" : "Заплановано"}</td>
                  <td>{trip.duty_number ?? "—"}</td>
                </tr>;
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Створити наряд</h2>
        <form onSubmit={createDuty}>
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="duty-number">Номер наряду</label>
              <input id="duty-number" required value={dutyNumber} onChange={(event) => setDutyNumber(event.target.value)} placeholder="Напр. Н-001" />
            </div>
            <div className="form-field">
              <label htmlFor="duty-vehicle">Автобус</label>
              <select id="duty-vehicle" required value={vehicleId} onChange={(event) => setVehicleId(event.target.value)}>
                <option value="">Виберіть автобус</option>
                {activeVehicles.map((vehicle) => <option key={vehicle.id} value={vehicle.id}>{vehicle.fleet_number} — {vehicle.registration_number}</option>)}
              </select>
            </div>
            <div className="form-field">
              <label htmlFor="duty-driver">Водій</label>
              <select id="duty-driver" required value={driverId} onChange={(event) => setDriverId(event.target.value)}>
                <option value="">Виберіть водія</option>
                {activeDrivers.map((driver) => <option key={driver.id} value={driver.id}>{driver.last_name} {driver.first_name}{driver.middle_name ? ` ${driver.middle_name}` : ""}</option>)}
              </select>
            </div>
          </div>
          <p className="muted">Вибрано рейсів: <strong>{selectedTripIds.length}</strong></p>
          <div className="form-actions"><button className="button" type="submit">Створити наряд</button></div>
        </form>
      </section>

      <section className="panel">
        <h2>Наряди на {serviceDate} — {duties.length}</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Наряд</th><th>Автобус</th><th>Водій</th><th>Рейси</th><th>Стан</th></tr></thead>
            <tbody>
              {duties.length === 0 ? <tr><td colSpan={5} className="muted">Нарядів ще немає.</td></tr> : duties.map((duty) => <tr key={duty.id}>
                <td><strong>{duty.duty_number}</strong></td>
                <td>{duty.vehicle_label}</td>
                <td>{duty.driver_label}</td>
                <td>{duty.trips.map((trip) => `${trip.planned_departure} №${trip.route_number}`).join(", ")}</td>
                <td>{duty.status === "ASSIGNED" ? "Призначено" : duty.status}</td>
              </tr>)}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
