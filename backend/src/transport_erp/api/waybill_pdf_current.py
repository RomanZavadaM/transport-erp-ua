from __future__ import annotations

import sqlite3
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import FileResponse

from transport_erp.api.waybills import (
    _build_pdf_data,
    _company_id,
    _connection,
    _load_waybill,
    _safe_pdf_name,
)
from transport_erp.config import get_settings
from transport_erp.waybill_pdf import build_waybill_pdf

router = APIRouter(prefix="/api", tags=["Waybill PDF"])


def _actual_pdf_values(connection: sqlite3.Connection, waybill_id: str) -> dict[str, object]:
    try:
        row = connection.execute(
            """
            SELECT actual_departure, actual_return,
                   odometer_start, odometer_end,
                   fuel_start_liters, fuel_issued_liters, fuel_end_liters
            FROM waybill_actuals
            WHERE waybill_id = ?
            """,
            (waybill_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        return {}
    if row is None:
        return {}

    odometer_start = int(row["odometer_start"]) if row["odometer_start"] is not None else None
    odometer_end = int(row["odometer_end"]) if row["odometer_end"] is not None else None
    distance = (
        odometer_end - odometer_start
        if odometer_start is not None and odometer_end is not None
        else None
    )
    fuel_start = float(row["fuel_start_liters"]) if row["fuel_start_liters"] is not None else None
    fuel_issued = (
        float(row["fuel_issued_liters"]) if row["fuel_issued_liters"] is not None else None
    )
    fuel_end = float(row["fuel_end_liters"]) if row["fuel_end_liters"] is not None else None
    fuel_consumed = (
        round(fuel_start + fuel_issued - fuel_end, 2)
        if fuel_start is not None and fuel_issued is not None and fuel_end is not None
        else None
    )

    actual_departure = ""
    actual_return = ""
    if row["actual_departure"]:
        actual_departure = datetime.fromisoformat(str(row["actual_departure"])).strftime("%H:%M")
    if row["actual_return"]:
        actual_return = datetime.fromisoformat(str(row["actual_return"])).strftime("%H:%M")

    return {
        "actual_departure": actual_departure,
        "actual_return": actual_return,
        "odometer_start": odometer_start,
        "odometer_end": odometer_end,
        "distance_km": distance,
        "fuel_start_liters": fuel_start,
        "fuel_issued_liters": fuel_issued,
        "fuel_end_liters": fuel_end,
        "fuel_consumed_liters": fuel_consumed,
    }


@router.get("/waybills/{waybill_id}/pdf-current", response_class=FileResponse)
def get_current_waybill_pdf(waybill_id: str) -> FileResponse:
    settings = get_settings()
    with _connection() as connection:
        waybill = _load_waybill(connection, _company_id(connection), waybill_id)
        data = _build_pdf_data(connection, waybill)
        data.update(_actual_pdf_values(connection, waybill_id))

    work_date = datetime.strptime(waybill.service_date, "%Y-%m-%d")
    output_dir = (
        settings.resolved_documents_dir
        / "waybills"
        / work_date.strftime("%Y")
        / work_date.strftime("%m")
    )
    output_path = output_dir / f"Waybill_{_safe_pdf_name(waybill.number)}.pdf"
    build_waybill_pdf(None, output_path, data)
    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=output_path.name,
    )
