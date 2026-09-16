"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

type PlanKind = "MAINTENANCE" | "INSPECTION" | "OTK" | "CUSTOM";
type BasisSource = "MANUFACTURER" | "NORMATIVE" | "ENTERPRISE" | "CUSTOM";
type PlanState = "NEEDS_BASELINE" | "OK" | "DUE_SOON" | "OVERDUE";

type Vehicle = {
  id: string;
  fleet_number: string;
  registration_number: string;
  make: string;
  model: string;
};

type StoirPlan = {
  id: string;
  vehicle_id: string;
  plan_kind: PlanKind;
  code: string;
  name: string;
  basis_source: BasisSource;
  interval_km: number | null;
  interval_months: number | null;
  last_completed_date: string | null;
  last_completed_odometer: number | null;
  warning_km: number;
  warning_days: number;
  note: string | null;
  active: boolean;
  next_due_date: string | null;
  next_due_odometer: number | null;
  current_odometer: number | null;
  remaining_km: number | null;
  remaining_days: number | null;
  state: PlanState;
};

type StoirEvent = {
  id: string;
  plan_code: string | null;
  plan_name: string | null;
  plan_kind: string;
  completed_date: string;
  odometer_km: number | null;
  outcome: "COMPLETED" | "PASSED" | "FAILED";
  performed_by: string | null;
  provider: string | null;
  document_number: string | null;
  document_valid_until: string | null;
  comment: string | null;
};

type StoirSummary = {
  vehicle_id: string;
  current_odometer: number | null;
  plans: StoirPlan[];
  history: StoirEvent[];
};

type PlanForm = {
  plan_kind: PlanKind;
  code: string;
  name: string;
  basis_source: BasisSource;
  interval_km: string;
  interval_months: string;
  last_completed_date: string;
  last_completed_odometer: string;
  warning_km: string;
  warning_days: string;
  note: string;
};

type CompleteForm = {
  completed_date: string;
  odometer_km: string;
  outcome: "COMPLETED" | "PASSED" | "FAILED";
  performed_by: string;
  provider: string;
  document_number: string;
  document_valid_until: string;
  comment: string;
};

function todayLocal(): string {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
}

const emptyPlan: PlanForm = {
  plan_kind: "MAINTENANCE",
  code: "",
  name: "",
  basis_source: "MANUFACTURER",
  interval_km: "",
  interval_months: "",
  last_completed_date: "",
  last_completed_odometer: "",
  warning_km: "500",
  warning_days: "14",
  note: "",
};

const kindLabel: Record<PlanKind, string> = {
  MAINTENANCE: "Технічне обслуговування",
  INSPECTION: "Планова технічна перевірка",
  OTK: "Обов’язковий технічний контроль",
  CUSTOM: "Інше",
};

const sourceLabel: Record<BasisSource, string> = {
  MANUFACTURER: "Виробник",
  NORMATIVE: "Норматив",
  ENTERPRISE: "Регламент підприємства",
  CUSTOM: "Інше",
};

const stateLabel: Record<PlanState, string> = {
  NEEDS_BASELINE: "Потрібен відлік",
  OK: "В нормі",
  DUE_SOON: "Наближається",
  OVERDUE: "ПРОСТРОЧЕНО",
};

function formatDate(value: string | null): string {
  return value ? new Date(`${value}T00:00:00`).toLocaleDateString("uk-UA") : "—";
}

function nullableNumber(value: string): number | null {
  return value.trim() === "" ? null : Number(value);
}

async function errorText(response: Response, fallback: string): Promise<string> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  if (typeof body?.detail === "string") return body.detail;
  return fallback;
}

function applyPreset(preset: string, currentOdometer: number | null): PlanForm {
  if (preset === "TO1") {
    return {
      ...emptyPlan,
      code: "TO-1",
      name: "Технічне обслуговування №1",
      basis_source: "NORMATIVE",
      interval_km: "5000",
      last_completed_odometer: currentOdometer?.toString() ?? "",
      note: "Стартове значення 5000 км. Звірити з документацією виробника конкретного автобуса.",
    };
  }
  if (preset === "TO2") {
    return {
      ...emptyPlan,
      code: "TO-2",
      name: "Технічне обслуговування №2",
      basis_source: "NORMATIVE",
      interval_km: "20000",
      last_completed_odometer: currentOdometer?.toString() ?? "",
      note: "Стартове значення 20000 км. Звірити з документацією виробника конкретного автобуса.",
    };
  }
  if (preset === "SEASON") {
    return {
      ...emptyPlan,
      code: "SEASON",
      name: "Сезонне технічне обслуговування",
      basis_source: "NORMATIVE",
      interval_months: "6",
      last_completed_date: todayLocal(),
      note: "Сезонне ТО. Дату та склад робіт уточнити за регламентом підприємства/виробника.",
    };
  }
  if (preset === "QUARTER") {
    return {
      ...emptyPlan,
      plan_kind: "INSPECTION",
      code: "Q-INSP",
      name: "Щоквартальна перевірка технічного стану",
      basis_source: "NORMATIVE",
      interval_months: "3",
      last_completed_date: todayLocal(),
      warning_days: "20",
      note: "Систематична перевірка пасажирського КТЗ.",
    };
  }
  if (preset === "OTK") {
    return {
      ...emptyPlan,
      plan_kind: "OTK",
      code: "OTK",
      name: "Обов’язковий технічний контроль",
      basis_source: "NORMATIVE",
      interval_months: "12",
      last_completed_date: todayLocal(),
      warning_days: "30",
      note: "Строк наступного контролю після проходження береться зі строку дії протоколу.",
    };
  }
  return emptyPlan;
}

export default function StoirPage() {
  const [vehicleId, setVehicleId] = useState("");
  const [vehicle, setVehicle] = useState<Vehicle | null>(null);
  const [summary, setSummary] = useState<StoirSummary | null>(null);
  const [plan, setPlan] = useState<PlanForm>(emptyPlan);
  const [selectedPlan, setSelectedPlan] = useState<StoirPlan | null>(null);
  const [complete, setComplete] = useState<CompleteForm>({
    completed_date: todayLocal(),
    odometer_km: "",
    outcome: "COMPLETED",
    performed_by: "",
    provider: "",
    document_number: "",
    document_valid_until: "",
    comment: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async (id: string) => {
    const [vehicleResponse, stoirResponse] = await Promise.all([
      fetch(`/api/vehicles/${encodeURIComponent(id)}/details`, { cache: "no-store" }),
      fetch(`/api/vehicles/${encodeURIComponent(id)}/stoir`, { cache: "no-store" }),
    ]);
    if (!vehicleResponse.ok) throw new Error("Не вдалося завантажити автобус.");
    if (!stoirResponse.ok) throw new Error(await errorText(stoirResponse, "Не вдалося завантажити СТОІР."));
    setVehicle((await vehicleResponse.json()) as Vehicle);
    setSummary((await stoirResponse.json()) as StoirSummary);
  }, []);

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("id") ?? "";
    setVehicleId(id);
    if (!id) {
      setError("Не вказано автобус.");
      return;
    }
    load(id).catch((reason) => setError(reason instanceof Error ? reason.message : "Невідома помилка"));
  }, [load]);

  const overdue = useMemo(
    () => summary?.plans.filter((item) => item.state === "OVERDUE").length ?? 0,
    [summary],
  );
  const dueSoon = useMemo(
    () => summary?.plans.filter((item) => item.state === "DUE_SOON").length ?? 0,
    [summary],
  );

  function selectForCompletion(item: StoirPlan) {
    setSelectedPlan(item);
    setComplete({
      completed_date: todayLocal(),
      odometer_km: summary?.current_odometer?.toString() ?? "",
      outcome: item.plan_kind === "INSPECTION" || item.plan_kind === "OTK" ? "PASSED" : "COMPLETED",
      performed_by: "",
      provider: "",
      document_number: "",
      document_valid_until: "",
      comment: "",
    });
    setMessage(null);
    setError(null);
  }

  async function createPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!vehicleId) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const response = await fetch(`/api/vehicles/${encodeURIComponent(vehicleId)}/stoir/plans`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_kind: plan.plan_kind,
          code: plan.code,
          name: plan.name,
          basis_source: plan.basis_source,
          interval_km: nullableNumber(plan.interval_km),
          interval_months: nullableNumber(plan.interval_months),
          last_completed_date: plan.last_completed_date || null,
          last_completed_odometer: nullableNumber(plan.last_completed_odometer),
          warning_km: Number(plan.warning_km || 0),
          warning_days: Number(plan.warning_days || 0),
          note: plan.note.trim() || null,
        }),
      });
      if (!response.ok) {
        setError(await errorText(response, "Не вдалося створити план СТОІР."));
        return;
      }
      setPlan(emptyPlan);
      setMessage("План СТОІР додано.");
      await load(vehicleId);
    } finally {
      setBusy(false);
    }
  }

  async function completePlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPlan || !vehicleId) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const response = await fetch(`/api/stoir/plans/${encodeURIComponent(selectedPlan.id)}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          completed_date: complete.completed_date,
          odometer_km: nullableNumber(complete.odometer_km),
          outcome: complete.outcome,
          performed_by: complete.performed_by.trim() || null,
          provider: complete.provider.trim() || null,
          document_number: complete.document_number.trim() || null,
          document_valid_until: complete.document_valid_until || null,
          comment: complete.comment.trim() || null,
        }),
      });
      if (!response.ok) {
        setError(await errorText(response, "Не вдалося зафіксувати виконання."));
        return;
      }
      setSummary((await response.json()) as StoirSummary);
      setSelectedPlan(null);
      setMessage("Виконання зафіксовано. Наступний строк/пробіг перераховано.");
    } finally {
      setBusy(false);
    }
  }

  if (!vehicle || !summary) {
    return (
      <main className="app-page">
        {error ? <p className="notice error">{error}</p> : <p className="muted">Завантаження СТОІР…</p>}
        <Link className="button secondary" href="/vehicles/">До автобусів</Link>
      </main>
    );
  }

  return (
    <main className="app-page">
      <div className="page-toolbar">
        <div>
          <p className="eyebrow">Технічна служба · СТОІР</p>
          <h1>{vehicle.fleet_number} · {vehicle.registration_number}</h1>
          <p className="subtitle">{vehicle.make} {vehicle.model}</p>
        </div>
        <div className="page-toolbar-actions">
          <Link className="button secondary" href={`/vehicle-card/?id=${encodeURIComponent(vehicle.id)}`}>Картка автобуса</Link>
          <Link className="button secondary" href="/vehicles/">Автобуси</Link>
        </div>
      </div>

      {message ? <p className="notice success">{message}</p> : null}
      {error ? <p className="notice error">{error}</p> : null}

      <section className="panel">
        <div className="info-grid">
          <div className="info-item"><strong>Поточний одометр</strong><span>{summary.current_odometer?.toLocaleString("uk-UA") ?? "—"} км</span></div>
          <div className="info-item"><strong>Активних планів</strong><span>{summary.plans.filter((item) => item.active).length}</span></div>
          <div className="info-item"><strong>Наближається</strong><span>{dueSoon}</span></div>
          <div className="info-item"><strong>Прострочено</strong><span>{overdue}</span></div>
        </div>
      </section>

      <section className="panel">
        <div className="page-toolbar">
          <div><h2>План ТО і технічних оглядів</h2><p className="muted">Розрахунок іде від єдиного одометра автобуса та/або календарного інтервалу.</p></div>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Стан</th><th>Код / вид</th><th>Підстава</th><th>Інтервал</th><th>Останнє</th><th>Наступне</th><th>Залишилось</th><th>Дія</th></tr></thead>
            <tbody>
              {summary.plans.length === 0 ? (
                <tr><td colSpan={8} className="muted">Планів СТОІР ще немає.</td></tr>
              ) : summary.plans.map((item) => (
                <tr key={item.id}>
                  <td><strong>{stateLabel[item.state]}</strong></td>
                  <td><strong>{item.code}</strong><br />{item.name}<br /><span className="muted">{kindLabel[item.plan_kind]}</span></td>
                  <td>{sourceLabel[item.basis_source]}</td>
                  <td>{item.interval_km ? `${item.interval_km.toLocaleString("uk-UA")} км` : ""}{item.interval_km && item.interval_months ? " / " : ""}{item.interval_months ? `${item.interval_months} міс.` : ""}</td>
                  <td>{formatDate(item.last_completed_date)}<br />{item.last_completed_odometer !== null ? `${item.last_completed_odometer.toLocaleString("uk-UA")} км` : ""}</td>
                  <td>{formatDate(item.next_due_date)}<br />{item.next_due_odometer !== null ? `${item.next_due_odometer.toLocaleString("uk-UA")} км` : ""}</td>
                  <td>{item.remaining_km !== null ? `${item.remaining_km.toLocaleString("uk-UA")} км` : ""}{item.remaining_km !== null && item.remaining_days !== null ? " / " : ""}{item.remaining_days !== null ? `${item.remaining_days} дн.` : ""}</td>
                  <td><button className="button secondary" type="button" onClick={() => selectForCompletion(item)}>Виконати / огляд</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {selectedPlan ? (
        <section className="panel">
          <h2>Зафіксувати виконання: {selectedPlan.code} · {selectedPlan.name}</h2>
          <form onSubmit={completePlan}>
            <div className="form-grid">
              <div className="form-field"><label htmlFor="stoir-complete-date">Дата</label><input id="stoir-complete-date" type="date" required value={complete.completed_date} onChange={(event) => setComplete((current) => ({ ...current, completed_date: event.target.value }))} /></div>
              <div className="form-field"><label htmlFor="stoir-complete-odo">Пробіг, км</label><input id="stoir-complete-odo" type="number" min="0" value={complete.odometer_km} onChange={(event) => setComplete((current) => ({ ...current, odometer_km: event.target.value }))} /></div>
              <div className="form-field"><label htmlFor="stoir-outcome">Результат</label><select id="stoir-outcome" value={complete.outcome} onChange={(event) => setComplete((current) => ({ ...current, outcome: event.target.value as CompleteForm["outcome"] }))}><option value="COMPLETED">Виконано</option><option value="PASSED">Пройдено / справний</option><option value="FAILED">Не пройдено / несправний</option></select></div>
              <div className="form-field"><label htmlFor="stoir-performed">Виконавець / відповідальний</label><input id="stoir-performed" value={complete.performed_by} onChange={(event) => setComplete((current) => ({ ...current, performed_by: event.target.value }))} /></div>
              <div className="form-field"><label htmlFor="stoir-provider">Місце / СТО / підрозділ</label><input id="stoir-provider" value={complete.provider} onChange={(event) => setComplete((current) => ({ ...current, provider: event.target.value }))} /></div>
              <div className="form-field"><label htmlFor="stoir-doc">Документ / протокол №</label><input id="stoir-doc" value={complete.document_number} onChange={(event) => setComplete((current) => ({ ...current, document_number: event.target.value }))} /></div>
              <div className="form-field"><label htmlFor="stoir-valid">Документ дійсний до</label><input id="stoir-valid" type="date" value={complete.document_valid_until} onChange={(event) => setComplete((current) => ({ ...current, document_valid_until: event.target.value }))} /></div>
              <div className="form-field"><label htmlFor="stoir-comment">Примітка</label><input id="stoir-comment" value={complete.comment} onChange={(event) => setComplete((current) => ({ ...current, comment: event.target.value }))} /></div>
            </div>
            <div className="form-actions"><button className="button" disabled={busy} type="submit">Зафіксувати</button><button className="button secondary" type="button" onClick={() => setSelectedPlan(null)}>Скасувати</button></div>
          </form>
        </section>
      ) : null}

      <section className="panel">
        <h2>Додати план СТОІР</h2>
        <div className="form-field" style={{ maxWidth: "520px", marginBottom: "1rem" }}>
          <label htmlFor="stoir-preset">Швидкий шаблон</label>
          <select id="stoir-preset" defaultValue="" onChange={(event) => setPlan(applyPreset(event.target.value, summary.current_odometer))}>
            <option value="">— заповнити вручну —</option>
            <option value="TO1">ТО-1 · стартово 5000 км</option>
            <option value="TO2">ТО-2 · стартово 20000 км</option>
            <option value="SEASON">Сезонне ТО · 6 місяців</option>
            <option value="QUARTER">Щоквартальна технічна перевірка · 3 місяці</option>
            <option value="OTK">Обов’язковий технічний контроль</option>
          </select>
          <span className="muted">Шаблони — лише стартове заповнення. Інтервал конкретного автобуса звіряється з виробником і документами підприємства.</span>
        </div>
        <form onSubmit={createPlan}>
          <div className="form-grid">
            <div className="form-field"><label htmlFor="plan-kind">Вид</label><select id="plan-kind" value={plan.plan_kind} onChange={(event) => setPlan((current) => ({ ...current, plan_kind: event.target.value as PlanKind }))}>{Object.entries(kindLabel).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
            <div className="form-field"><label htmlFor="plan-code">Код</label><input id="plan-code" required value={plan.code} onChange={(event) => setPlan((current) => ({ ...current, code: event.target.value }))} placeholder="TO-1" /></div>
            <div className="form-field"><label htmlFor="plan-name">Назва</label><input id="plan-name" required value={plan.name} onChange={(event) => setPlan((current) => ({ ...current, name: event.target.value }))} /></div>
            <div className="form-field"><label htmlFor="plan-source">Підстава</label><select id="plan-source" value={plan.basis_source} onChange={(event) => setPlan((current) => ({ ...current, basis_source: event.target.value as BasisSource }))}>{Object.entries(sourceLabel).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
            <div className="form-field"><label htmlFor="plan-km">Інтервал, км</label><input id="plan-km" type="number" min="1" value={plan.interval_km} onChange={(event) => setPlan((current) => ({ ...current, interval_km: event.target.value }))} /></div>
            <div className="form-field"><label htmlFor="plan-months">Інтервал, місяців</label><input id="plan-months" type="number" min="1" value={plan.interval_months} onChange={(event) => setPlan((current) => ({ ...current, interval_months: event.target.value }))} /></div>
            <div className="form-field"><label htmlFor="plan-last-date">Останнє виконання / відлік від дати</label><input id="plan-last-date" type="date" value={plan.last_completed_date} onChange={(event) => setPlan((current) => ({ ...current, last_completed_date: event.target.value }))} /></div>
            <div className="form-field"><label htmlFor="plan-last-odo">Останнє виконання / відлік від пробігу</label><input id="plan-last-odo" type="number" min="0" value={plan.last_completed_odometer} onChange={(event) => setPlan((current) => ({ ...current, last_completed_odometer: event.target.value }))} /></div>
            <div className="form-field"><label htmlFor="plan-warn-km">Попереджати за, км</label><input id="plan-warn-km" type="number" min="0" value={plan.warning_km} onChange={(event) => setPlan((current) => ({ ...current, warning_km: event.target.value }))} /></div>
            <div className="form-field"><label htmlFor="plan-warn-days">Попереджати за, днів</label><input id="plan-warn-days" type="number" min="0" value={plan.warning_days} onChange={(event) => setPlan((current) => ({ ...current, warning_days: event.target.value }))} /></div>
            <div className="form-field"><label htmlFor="plan-note">Примітка / посилання на регламент</label><input id="plan-note" value={plan.note} onChange={(event) => setPlan((current) => ({ ...current, note: event.target.value }))} /></div>
          </div>
          <div className="form-actions"><button className="button" disabled={busy} type="submit">Додати до плану</button></div>
        </form>
      </section>

      <section className="panel">
        <h2>Історія ТО і технічних оглядів</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Дата</th><th>Робота / огляд</th><th>Пробіг</th><th>Результат</th><th>Виконавець</th><th>Документ</th><th>Дійсний до</th><th>Примітка</th></tr></thead>
            <tbody>
              {summary.history.length === 0 ? (
                <tr><td colSpan={8} className="muted">Історії СТОІР ще немає.</td></tr>
              ) : summary.history.map((item) => (
                <tr key={item.id}>
                  <td>{formatDate(item.completed_date)}</td>
                  <td><strong>{item.plan_code ?? "—"}</strong><br />{item.plan_name ?? item.plan_kind}</td>
                  <td>{item.odometer_km !== null ? `${item.odometer_km.toLocaleString("uk-UA")} км` : "—"}</td>
                  <td>{item.outcome}</td>
                  <td>{item.performed_by ?? "—"}<br />{item.provider ?? ""}</td>
                  <td>{item.document_number ?? "—"}</td>
                  <td>{formatDate(item.document_valid_until)}</td>
                  <td>{item.comment ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
