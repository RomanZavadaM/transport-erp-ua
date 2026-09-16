"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";

type Vehicle = {
  id: string;
  fleet_number: string;
  registration_number: string;
  make: string;
  model: string;
  lifecycle_status: string;
};

type Defect = {
  id: string;
  reported_at: string;
  reported_by: string | null;
  source: string;
  severity: "MINOR" | "MAJOR" | "CRITICAL";
  description: string;
  blocks_release: boolean;
  status: string;
  note: string | null;
  resolved_at: string | null;
};

type RepairItem = {
  id: string;
  item_type: "WORK" | "PART" | "MATERIAL";
  description: string;
  part_number: string | null;
  quantity: number;
  unit: string;
  unit_price: number | null;
  amount: number | null;
};

type RepairOrder = {
  id: string;
  defect_id: string | null;
  number: string;
  status: string;
  blocks_operation: boolean;
  opened_at: string;
  started_at: string | null;
  completed_at: string | null;
  closed_at: string | null;
  closed_by: string | null;
  provider: string | null;
  odometer_km: number | null;
  description: string;
  verification_comment: string | null;
  total_cost: number;
  items: RepairItem[];
};

type RepairSummary = {
  vehicle_id: string;
  defects: Defect[];
  repair_orders: RepairOrder[];
};

async function apiError(response: Response, fallback: string): Promise<string> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  return body?.detail ?? fallback;
}

export default function RepairsPage() {
  const [vehicleId, setVehicleId] = useState("");
  const [vehicle, setVehicle] = useState<Vehicle | null>(null);
  const [summary, setSummary] = useState<RepairSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [defectDescription, setDefectDescription] = useState("");
  const [defectSeverity, setDefectSeverity] = useState<"MINOR" | "MAJOR" | "CRITICAL">("MINOR");
  const [defectBlocks, setDefectBlocks] = useState(false);
  const [defectSource, setDefectSource] = useState("TECHNICAL");
  const [defectReporter, setDefectReporter] = useState("");
  const [defectNote, setDefectNote] = useState("");

  const [orderNumber, setOrderNumber] = useState("");
  const [orderDefectId, setOrderDefectId] = useState("");
  const [orderDescription, setOrderDescription] = useState("");
  const [orderProvider, setOrderProvider] = useState("");
  const [orderBlocks, setOrderBlocks] = useState(true);
  const [orderOdometer, setOrderOdometer] = useState("");

  const [selectedOrderId, setSelectedOrderId] = useState("");
  const [itemType, setItemType] = useState<"WORK" | "PART" | "MATERIAL">("WORK");
  const [itemDescription, setItemDescription] = useState("");
  const [itemPartNumber, setItemPartNumber] = useState("");
  const [itemQuantity, setItemQuantity] = useState("1");
  const [itemUnit, setItemUnit] = useState("шт");
  const [itemPrice, setItemPrice] = useState("");

  const [closedBy, setClosedBy] = useState("");
  const [verificationComment, setVerificationComment] = useState("");

  const load = useCallback(async (id: string) => {
    const [vehicleResponse, repairsResponse] = await Promise.all([
      fetch(`/api/vehicles/${encodeURIComponent(id)}/details`, { cache: "no-store" }),
      fetch(`/api/vehicles/${encodeURIComponent(id)}/repairs`, { cache: "no-store" }),
    ]);
    if (!vehicleResponse.ok) throw new Error("Не вдалося завантажити автобус.");
    if (!repairsResponse.ok) throw new Error(await apiError(repairsResponse, "Не вдалося завантажити ремонти."));
    setVehicle((await vehicleResponse.json()) as Vehicle);
    const data = (await repairsResponse.json()) as RepairSummary;
    setSummary(data);
    setSelectedOrderId((current) =>
      data.repair_orders.some((item) => item.id === current)
        ? current
        : data.repair_orders.find((item) => !["CLOSED", "CANCELLED"].includes(item.status))?.id ?? "",
    );
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

  async function createDefect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!vehicleId) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const response = await fetch(`/api/vehicles/${encodeURIComponent(vehicleId)}/defects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: defectDescription,
          severity: defectSeverity,
          blocks_release: defectBlocks,
          source: defectSource,
          reported_by: defectReporter.trim() || null,
          note: defectNote.trim() || null,
        }),
      });
      if (!response.ok) {
        setError(await apiError(response, "Не вдалося зареєструвати дефект."));
        return;
      }
      setDefectDescription("");
      setDefectSeverity("MINOR");
      setDefectBlocks(false);
      setDefectNote("");
      setMessage("Дефект зареєстровано.");
      await load(vehicleId);
    } finally {
      setBusy(false);
    }
  }

  async function createOrder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!vehicleId) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const response = await fetch(`/api/vehicles/${encodeURIComponent(vehicleId)}/repair-orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          number: orderNumber,
          defect_id: orderDefectId || null,
          description: orderDescription,
          provider: orderProvider.trim() || null,
          blocks_operation: orderBlocks,
          odometer_km: orderOdometer.trim() ? Number(orderOdometer) : null,
        }),
      });
      if (!response.ok) {
        setError(await apiError(response, "Не вдалося створити ремонтний наряд."));
        return;
      }
      const created = (await response.json()) as RepairOrder;
      setSelectedOrderId(created.id);
      setOrderNumber("");
      setOrderDefectId("");
      setOrderDescription("");
      setOrderProvider("");
      setOrderOdometer("");
      setMessage("Ремонтний наряд створено.");
      await load(vehicleId);
    } finally {
      setBusy(false);
    }
  }

  async function addItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedOrderId || !vehicleId) return;
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(`/api/repair-orders/${encodeURIComponent(selectedOrderId)}/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          item_type: itemType,
          description: itemDescription,
          part_number: itemPartNumber.trim() || null,
          quantity: Number(itemQuantity),
          unit: itemUnit,
          unit_price: itemPrice.trim() ? Number(itemPrice) : null,
        }),
      });
      if (!response.ok) {
        setError(await apiError(response, "Не вдалося додати роботу/запчастину."));
        return;
      }
      setItemDescription("");
      setItemPartNumber("");
      setItemQuantity("1");
      setItemPrice("");
      setMessage("Позицію додано до ремонтного наряду.");
      await load(vehicleId);
    } finally {
      setBusy(false);
    }
  }

  async function action(orderId: string, actionName: "start" | "complete") {
    if (!vehicleId) return;
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(`/api/repair-orders/${encodeURIComponent(orderId)}/${actionName}`, { method: "POST" });
      if (!response.ok) {
        setError(await apiError(response, "Не вдалося змінити стан ремонту."));
        return;
      }
      setMessage(actionName === "start" ? "Ремонт розпочато." : "Роботи позначено виконаними.");
      await load(vehicleId);
    } finally {
      setBusy(false);
    }
  }

  async function closeOrder(orderId: string) {
    if (!vehicleId) return;
    if (!closedBy.trim() || !verificationComment.trim()) {
      setError("Для закриття вкажіть хто перевірив ремонт і результат перевірки.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(`/api/repair-orders/${encodeURIComponent(orderId)}/close`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ closed_by: closedBy, verification_comment: verificationComment }),
      });
      if (!response.ok) {
        setError(await apiError(response, "Не вдалося закрити ремонт."));
        return;
      }
      setClosedBy("");
      setVerificationComment("");
      setMessage("Ремонт закрито і технічний результат зафіксовано.");
      await load(vehicleId);
    } finally {
      setBusy(false);
    }
  }

  if (!vehicle || !summary) {
    return <main className="app-page">{error ? <p className="notice error">{error}</p> : <p className="muted">Завантаження…</p>}</main>;
  }

  const openDefects = summary.defects.filter((item) => ["OPEN", "IN_REPAIR"].includes(item.status));
  const selectedOrder = summary.repair_orders.find((item) => item.id === selectedOrderId) ?? null;

  return (
    <main className="app-page">
      <div className="page-toolbar">
        <div>
          <p className="eyebrow">Технічна служба · ремонт</p>
          <h1>{vehicle.fleet_number} · {vehicle.registration_number}</h1>
          <p className="subtitle">{vehicle.make} {vehicle.model} · стан {vehicle.lifecycle_status}</p>
        </div>
        <div className="page-toolbar-actions">
          <Link className="button" href={`/stoir/?id=${encodeURIComponent(vehicle.id)}`}>СТОІР</Link>
          <Link className="button secondary" href="/technical/">Технічна служба</Link>
        </div>
      </div>

      {message ? <p className="notice success">{message}</p> : null}
      {error ? <p className="notice error">{error}</p> : null}

      <section className="panel">
        <h2>Зареєструвати дефект</h2>
        <form onSubmit={createDefect}>
          <div className="form-grid">
            <div className="form-field"><label>Опис дефекту</label><input required value={defectDescription} onChange={(e) => setDefectDescription(e.target.value)} /></div>
            <div className="form-field"><label>Критичність</label><select value={defectSeverity} onChange={(e) => setDefectSeverity(e.target.value as typeof defectSeverity)}><option value="MINOR">Незначний</option><option value="MAJOR">Суттєвий</option><option value="CRITICAL">Критичний</option></select></div>
            <div className="form-field"><label>Джерело</label><input value={defectSource} onChange={(e) => setDefectSource(e.target.value)} /></div>
            <div className="form-field"><label>Повідомив</label><input value={defectReporter} onChange={(e) => setDefectReporter(e.target.value)} /></div>
            <div className="form-field"><label>Примітка</label><input value={defectNote} onChange={(e) => setDefectNote(e.target.value)} /></div>
            <label className="form-field"><span>Експлуатацію заборонити</span><input type="checkbox" checked={defectBlocks} onChange={(e) => setDefectBlocks(e.target.checked)} /></label>
          </div>
          <div className="form-actions"><button className="button" disabled={busy} type="submit">Зареєструвати дефект</button></div>
        </form>
      </section>

      <section className="panel">
        <h2>Дефекти</h2>
        <div className="table-wrap"><table><thead><tr><th>Дата</th><th>Опис</th><th>Критичність</th><th>Блокує</th><th>Стан</th></tr></thead><tbody>
          {summary.defects.length === 0 ? <tr><td colSpan={5} className="muted">Дефектів немає.</td></tr> : summary.defects.map((item) => (
            <tr key={item.id}><td>{new Date(item.reported_at).toLocaleString("uk-UA")}</td><td>{item.description}</td><td>{item.severity}</td><td>{item.blocks_release ? "ТАК" : "ні"}</td><td>{item.status}</td></tr>
          ))}
        </tbody></table></div>
      </section>

      <section className="panel">
        <h2>Новий ремонтний наряд</h2>
        <form onSubmit={createOrder}>
          <div className="form-grid">
            <div className="form-field"><label>Номер</label><input required value={orderNumber} onChange={(e) => setOrderNumber(e.target.value)} placeholder="РН-0001" /></div>
            <div className="form-field"><label>Пов’язаний дефект</label><select value={orderDefectId} onChange={(e) => setOrderDefectId(e.target.value)}><option value="">Без дефекту</option>{openDefects.map((item) => <option key={item.id} value={item.id}>{item.description}</option>)}</select></div>
            <div className="form-field"><label>Опис ремонту</label><input required value={orderDescription} onChange={(e) => setOrderDescription(e.target.value)} /></div>
            <div className="form-field"><label>Виконавець / СТО</label><input value={orderProvider} onChange={(e) => setOrderProvider(e.target.value)} /></div>
            <div className="form-field"><label>Одометр, км</label><input min="0" type="number" value={orderOdometer} onChange={(e) => setOrderOdometer(e.target.value)} /></div>
            <label className="form-field"><span>Автобус не експлуатувати</span><input type="checkbox" checked={orderBlocks} onChange={(e) => setOrderBlocks(e.target.checked)} /></label>
          </div>
          <div className="form-actions"><button className="button" disabled={busy} type="submit">Створити ремонтний наряд</button></div>
        </form>
      </section>

      <section className="panel">
        <h2>Ремонтні наряди</h2>
        <div className="table-wrap"><table><thead><tr><th>№</th><th>Опис</th><th>СТО</th><th>Стан</th><th>Сума</th><th>Дії</th></tr></thead><tbody>
          {summary.repair_orders.length === 0 ? <tr><td colSpan={6} className="muted">Ремонтних нарядів немає.</td></tr> : summary.repair_orders.map((order) => (
            <tr key={order.id}><td><strong>{order.number}</strong></td><td>{order.description}</td><td>{order.provider ?? "—"}</td><td>{order.status}</td><td>{order.total_cost.toLocaleString("uk-UA")} грн</td><td><div className="form-actions compact-actions"><button className="button secondary" type="button" onClick={() => setSelectedOrderId(order.id)}>Позиції</button>{order.status === "OPEN" ? <button className="button secondary" type="button" onClick={() => action(order.id, "start")}>Розпочати</button> : null}{["OPEN", "IN_PROGRESS"].includes(order.status) ? <button className="button secondary" type="button" onClick={() => action(order.id, "complete")}>Виконано</button> : null}</div></td></tr>
          ))}
        </tbody></table></div>
      </section>

      {selectedOrder ? (
        <section className="panel">
          <h2>Наряд {selectedOrder.number}</h2>
          <div className="table-wrap"><table><thead><tr><th>Тип</th><th>Робота / запчастина</th><th>№ деталі</th><th>К-сть</th><th>Ціна</th><th>Сума</th></tr></thead><tbody>
            {selectedOrder.items.length === 0 ? <tr><td colSpan={6} className="muted">Позицій ще немає.</td></tr> : selectedOrder.items.map((item) => <tr key={item.id}><td>{item.item_type}</td><td>{item.description}</td><td>{item.part_number ?? "—"}</td><td>{item.quantity} {item.unit}</td><td>{item.unit_price ?? "—"}</td><td>{item.amount ?? "—"}</td></tr>)}
          </tbody></table></div>

          {!(["CLOSED", "CANCELLED"].includes(selectedOrder.status)) ? (
            <form onSubmit={addItem}>
              <div className="form-grid">
                <div className="form-field"><label>Тип</label><select value={itemType} onChange={(e) => setItemType(e.target.value as typeof itemType)}><option value="WORK">Робота</option><option value="PART">Запчастина</option><option value="MATERIAL">Матеріал</option></select></div>
                <div className="form-field"><label>Опис</label><input required value={itemDescription} onChange={(e) => setItemDescription(e.target.value)} /></div>
                <div className="form-field"><label>Каталожний №</label><input value={itemPartNumber} onChange={(e) => setItemPartNumber(e.target.value)} /></div>
                <div className="form-field"><label>Кількість</label><input min="0.001" step="0.001" type="number" required value={itemQuantity} onChange={(e) => setItemQuantity(e.target.value)} /></div>
                <div className="form-field"><label>Одиниця</label><input required value={itemUnit} onChange={(e) => setItemUnit(e.target.value)} /></div>
                <div className="form-field"><label>Ціна</label><input min="0" step="0.01" type="number" value={itemPrice} onChange={(e) => setItemPrice(e.target.value)} /></div>
              </div>
              <div className="form-actions"><button className="button" disabled={busy} type="submit">Додати позицію</button></div>
            </form>
          ) : null}

          {selectedOrder.status === "COMPLETED" ? (
            <div className="form-grid">
              <div className="form-field"><label>Перевірив</label><input value={closedBy} onChange={(e) => setClosedBy(e.target.value)} /></div>
              <div className="form-field"><label>Результат технічної перевірки після ремонту</label><input value={verificationComment} onChange={(e) => setVerificationComment(e.target.value)} /></div>
              <div className="form-actions"><button className="button" type="button" onClick={() => closeOrder(selectedOrder.id)}>Закрити ремонт і допустити</button></div>
            </div>
          ) : null}
        </section>
      ) : null}
    </main>
  );
}
