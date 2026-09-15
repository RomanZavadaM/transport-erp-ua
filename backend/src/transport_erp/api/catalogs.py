from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from transport_erp.config import get_settings
from transport_erp.local_runtime import ensure_local_storage

router = APIRouter(prefix="/api", tags=["Company & Routes"])


class CompanyInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    edrpou: str | None = Field(default=None, max_length=20)


class CompanyResponse(CompanyInput):
    id: str


class StopInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    locality: str | None = Field(default=None, max_length=200)
    active: bool = True


class StopResponse(StopInput):
    id: str


class RouteInput(BaseModel):
    number: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    active: bool = True
    stop_ids: list[str] = Field(min_length=2)


class RouteStopResponse(BaseModel):
    id: str
    name: str
    locality: str | None
    position: int


class RouteResponse(BaseModel):
    id: str
    number: str
    name: str
    active: bool
    stops: list[RouteStopResponse]


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    if settings.deployment_profile != "local":
        raise HTTPException(status_code=404, detail="Local catalog API is disabled")
    ensure_local_storage(settings)
    connection = sqlite3.connect(settings.local_database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _company_id(connection: sqlite3.Connection) -> str:
    row = connection.execute("SELECT value FROM app_meta WHERE key = 'company_id'").fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="Підприємство не ініціалізоване.")
    return str(row["value"])


def _stop_from_row(row: sqlite3.Row) -> StopResponse:
    return StopResponse(
        id=str(row["id"]),
        name=str(row["name"]),
        locality=str(row["locality"]) if row["locality"] is not None else None,
        active=bool(row["active"]),
    )


def _load_route(connection: sqlite3.Connection, company_id: str, route_id: str) -> RouteResponse:
    route = connection.execute(
        "SELECT id, number, name, active FROM routes WHERE id = ? AND company_id = ?",
        (route_id, company_id),
    ).fetchone()
    if route is None:
        raise HTTPException(status_code=404, detail="Маршрут не знайдено.")
    stops = connection.execute(
        """
        SELECT s.id, s.name, s.locality, rs.position
        FROM route_stops rs
        JOIN stops s ON s.id = rs.stop_id
        WHERE rs.route_id = ?
        ORDER BY rs.position
        """,
        (route_id,),
    ).fetchall()
    return RouteResponse(
        id=str(route["id"]),
        number=str(route["number"]),
        name=str(route["name"]),
        active=bool(route["active"]),
        stops=[
            RouteStopResponse(
                id=str(stop["id"]),
                name=str(stop["name"]),
                locality=str(stop["locality"]) if stop["locality"] is not None else None,
                position=int(stop["position"]),
            )
            for stop in stops
        ],
    )


def _replace_route_stops(
    connection: sqlite3.Connection, company_id: str, route_id: str, stop_ids: list[str]
) -> None:
    if len(set(stop_ids)) != len(stop_ids):
        raise HTTPException(status_code=400, detail="Зупинка не може повторюватися в маршруті.")
    placeholders = ",".join("?" for _ in stop_ids)
    count = connection.execute(
        f"SELECT COUNT(*) FROM stops WHERE company_id = ? AND active = 1 AND id IN ({placeholders})",
        (company_id, *stop_ids),
    ).fetchone()
    if count is None or int(count[0]) != len(stop_ids):
        raise HTTPException(status_code=400, detail="Одна або кілька зупинок недоступні.")

    connection.execute("DELETE FROM route_stops WHERE route_id = ?", (route_id,))
    connection.executemany(
        "INSERT INTO route_stops(route_id, stop_id, position) VALUES (?, ?, ?)",
        [(route_id, stop_id, position) for position, stop_id in enumerate(stop_ids, start=1)],
    )


@router.get("/company", response_model=CompanyResponse)
def get_company() -> CompanyResponse:
    with _connection() as connection:
        company_id = _company_id(connection)
        row = connection.execute(
            "SELECT id, name, edrpou FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Підприємство не знайдено.")
    return CompanyResponse(
        id=str(row["id"]),
        name=str(row["name"]),
        edrpou=str(row["edrpou"]) if row["edrpou"] is not None else None,
    )


@router.put("/company", response_model=CompanyResponse)
def update_company(payload: CompanyInput) -> CompanyResponse:
    with _connection() as connection:
        company_id = _company_id(connection)
        connection.execute(
            "UPDATE companies SET name = ?, edrpou = ? WHERE id = ?",
            (payload.name.strip(), payload.edrpou.strip() if payload.edrpou else None, company_id),
        )
        row = connection.execute(
            "SELECT id, name, edrpou FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Підприємство не знайдено.")
    return CompanyResponse(
        id=str(row["id"]),
        name=str(row["name"]),
        edrpou=str(row["edrpou"]) if row["edrpou"] is not None else None,
    )


@router.get("/stops", response_model=list[StopResponse])
def list_stops() -> list[StopResponse]:
    with _connection() as connection:
        company_id = _company_id(connection)
        rows = connection.execute(
            """
            SELECT id, name, locality, active
            FROM stops WHERE company_id = ?
            ORDER BY active DESC, name COLLATE NOCASE
            """,
            (company_id,),
        ).fetchall()
    return [_stop_from_row(row) for row in rows]


@router.post("/stops", response_model=StopResponse, status_code=201)
def create_stop(payload: StopInput) -> StopResponse:
    stop_id = str(uuid4())
    try:
        with _connection() as connection:
            company_id = _company_id(connection)
            connection.execute(
                "INSERT INTO stops(id, company_id, name, locality, active) VALUES (?, ?, ?, ?, ?)",
                (
                    stop_id,
                    company_id,
                    payload.name.strip(),
                    payload.locality.strip() if payload.locality else None,
                    int(payload.active),
                ),
            )
            row = connection.execute(
                "SELECT id, name, locality, active FROM stops WHERE id = ?", (stop_id,)
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Така зупинка вже існує.") from exc
    if row is None:
        raise HTTPException(status_code=500, detail="Зупинку не створено.")
    return _stop_from_row(row)


@router.put("/stops/{stop_id}", response_model=StopResponse)
def update_stop(stop_id: str, payload: StopInput) -> StopResponse:
    try:
        with _connection() as connection:
            company_id = _company_id(connection)
            cursor = connection.execute(
                """
                UPDATE stops SET name = ?, locality = ?, active = ?
                WHERE id = ? AND company_id = ?
                """,
                (
                    payload.name.strip(),
                    payload.locality.strip() if payload.locality else None,
                    int(payload.active),
                    stop_id,
                    company_id,
                ),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Зупинку не знайдено.")
            row = connection.execute(
                "SELECT id, name, locality, active FROM stops WHERE id = ?", (stop_id,)
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Така зупинка вже існує.") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="Зупинку не знайдено.")
    return _stop_from_row(row)


@router.get("/routes", response_model=list[RouteResponse])
def list_routes() -> list[RouteResponse]:
    with _connection() as connection:
        company_id = _company_id(connection)
        rows = connection.execute(
            "SELECT id FROM routes WHERE company_id = ? ORDER BY number COLLATE NOCASE",
            (company_id,),
        ).fetchall()
        return [_load_route(connection, company_id, str(row["id"])) for row in rows]


@router.post("/routes", response_model=RouteResponse, status_code=201)
def create_route(payload: RouteInput) -> RouteResponse:
    route_id = str(uuid4())
    try:
        with _connection() as connection:
            company_id = _company_id(connection)
            connection.execute(
                "INSERT INTO routes(id, company_id, number, name, active) VALUES (?, ?, ?, ?, ?)",
                (route_id, company_id, payload.number.strip(), payload.name.strip(), int(payload.active)),
            )
            _replace_route_stops(connection, company_id, route_id, payload.stop_ids)
            return _load_route(connection, company_id, route_id)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Маршрут з таким номером уже існує.") from exc


@router.put("/routes/{route_id}", response_model=RouteResponse)
def update_route(route_id: str, payload: RouteInput) -> RouteResponse:
    try:
        with _connection() as connection:
            company_id = _company_id(connection)
            cursor = connection.execute(
                """
                UPDATE routes SET number = ?, name = ?, active = ?
                WHERE id = ? AND company_id = ?
                """,
                (payload.number.strip(), payload.name.strip(), int(payload.active), route_id, company_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Маршрут не знайдено.")
            _replace_route_stops(connection, company_id, route_id, payload.stop_ids)
            return _load_route(connection, company_id, route_id)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Маршрут з таким номером уже існує.") from exc
