from __future__ import annotations

import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4, landscape  # type: ignore[import-untyped]
from reportlab.pdfbase import pdfmetrics  # type: ignore[import-untyped]
from reportlab.pdfbase.ttfonts import TTFont  # type: ignore[import-untyped]
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]

PAGE = landscape(A4)
W, H = PAGE
INK = (0.08, 0.10, 0.13)


def _font_candidates(*, bold: bool) -> list[str]:
    if os.name == "nt":
        return [
            r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf",
        ]
    if sys.platform == "darwin":
        return [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
            if bold
            else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        ]
    return [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]


def _register_fonts() -> tuple[str, str]:
    normal = "Helvetica"
    bold_name = "Helvetica-Bold"
    for candidate in _font_candidates(bold=False):
        if os.path.exists(candidate):
            pdfmetrics.registerFont(TTFont("WB", candidate))
            normal = "WB"
            break
    for candidate in _font_candidates(bold=True):
        if os.path.exists(candidate):
            pdfmetrics.registerFont(TTFont("WB-Bold", candidate))
            bold_name = "WB-Bold"
            break
    return normal, bold_name


FONT, FONT_BOLD = _register_fonts()


def _y(top: float) -> float:
    return H - top


def _line(c: Any, x1: float, y1: float, x2: float, y2: float, width: float = 0.55) -> None:
    c.setStrokeColorRGB(*INK)
    c.setLineWidth(width)
    c.line(x1, _y(y1), x2, _y(y2))


def _box(c: Any, x: float, y: float, w: float, h: float, width: float = 0.55) -> None:
    c.setStrokeColorRGB(*INK)
    c.setLineWidth(width)
    c.rect(x, _y(y + h), w, h, stroke=1, fill=0)


def _wrap(text: str, font: str, size: float, max_width: float) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            if pdfmetrics.stringWidth(trial, font, size) <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _text(
    c: Any,
    x: float,
    y: float,
    w: float,
    h: float,
    text: Any,
    size: float = 7.2,
    *,
    bold: bool = False,
    align: str = "center",
    valign: str = "middle",
    pad: float = 2,
) -> None:
    value = str(text or "").strip()
    if not value:
        return
    font = FONT_BOLD if bold else FONT
    actual = float(size)
    lines = _wrap(value, font, actual, max(4.0, w - pad * 2))
    while actual > 4.1 and (
        len(lines) * actual * 1.13 > h - 2
        or any(pdfmetrics.stringWidth(line, font, actual) > w - pad * 2 for line in lines)
    ):
        actual -= 0.25
        lines = _wrap(value, font, actual, max(4.0, w - pad * 2))
    leading = actual * 1.13
    total = len(lines) * leading
    if valign == "top":
        baseline = _y(y + pad + actual)
    elif valign == "bottom":
        baseline = _y(y + h - pad - (len(lines) - 1) * leading)
    else:
        baseline = _y(y + (h - total) / 2 + actual)
    c.setFillColorRGB(*INK)
    c.setFont(font, actual)
    for index, line in enumerate(lines):
        yy = baseline - index * leading
        if align == "left":
            c.drawString(x + pad, yy, line)
        elif align == "right":
            c.drawRightString(x + w - pad, yy, line)
        else:
            c.drawCentredString(x + w / 2, yy, line)


def _cell(
    c: Any,
    x: float,
    y: float,
    w: float,
    h: float,
    text: Any = "",
    size: float = 6.8,
    *,
    bold: bool = False,
    align: str = "center",
    valign: str = "middle",
) -> None:
    _box(c, x, y, w, h)
    _text(c, x, y, w, h, text, size, bold=bold, align=align, valign=valign)


def _value_line(
    c: Any,
    x: float,
    y: float,
    w: float,
    label: str,
    value: Any = "",
    label_w: float | None = None,
    size: float = 7.0,
) -> None:
    width = label_w or min(w * 0.42, pdfmetrics.stringWidth(label, FONT, size) + 5)
    _text(c, x, y, width, 13, label, size, align="left")
    _line(c, x + width, y + 11, x + w, y + 11, 0.45)
    _text(c, x + width, y, w - width, 11, value, size, bold=bool(value), align="left")


def _first_nonempty(items: Sequence[Mapping[str, Any]], key: str) -> str:
    for item in items:
        value = str(item.get(key) or "").strip()
        if value:
            return value
    return ""


def _page_one(c: Any, data: Mapping[str, Any]) -> None:
    margin = 18
    right = W - margin

    _box(c, margin, 18, 160, 84, 0.8)
    _text(c, margin + 5, 24, 150, 14, "Підприємство", 6.5, align="left")
    _text(c, margin + 5, 40, 150, 38, data.get("company_name", ""), 8.0, bold=True, align="left", valign="top")
    if data.get("company_edrpou"):
        _text(c, margin + 5, 79, 150, 14, f"ЄДРПОУ {data.get('company_edrpou')}", 6.4, align="left")

    center_x = margin + 160
    center_w = 430
    _text(c, center_x, 22, center_w, 22, "ШЛЯХОВИЙ ЛИСТ АВТОБУСА", 13, bold=True)
    _text(c, center_x + 245, 48, 35, 18, "№", 9, bold=True, align="right")
    _text(c, center_x + 282, 46, 135, 20, data.get("waybill_no", ""), 11, bold=True, align="left")
    _value_line(c, center_x + 8, 68, center_w - 16, "Дата роботи", data.get("date", ""), 76, 7.4)
    _value_line(c, center_x + 8, 84, center_w - 16, "Наряд", data.get("duty_number", ""), 76, 7.4)

    right_x = center_x + center_w
    right_w = right - right_x
    _value_line(c, right_x + 4, 28, right_w - 8, "Маршрут", data.get("route", ""), 48, 6.5)
    _value_line(c, right_x + 4, 46, right_w - 8, "Автобус", data.get("vehicle", ""), 48, 6.5)
    _value_line(c, right_x + 4, 64, right_w - 8, "Гар. №", data.get("fleet_number", ""), 48, 6.5)
    _value_line(c, right_x + 4, 82, right_w - 8, "Держ. №", data.get("registration_number", ""), 48, 6.5)

    y = 112
    dep_w = 150
    driver_w = 245
    control_w = 255
    return_w = right - margin - dep_w - driver_w - control_w
    x = margin

    _cell(c, x, y, dep_w, 18, "Виїзд із підприємства", 7.2, bold=True)
    _cell(c, x, y + 18, dep_w / 2, 18, "за графіком", 6.2)
    _cell(c, x + dep_w / 2, y + 18, dep_w / 2, 18, "фактично", 6.2)
    _cell(c, x, y + 36, dep_w / 2, 70, data.get("planned_departure", ""), 9, bold=True)
    _cell(c, x + dep_w / 2, y + 36, dep_w / 2, 70, data.get("actual_departure", ""), 8, bold=bool(data.get("actual_departure")))
    x += dep_w

    _cell(c, x, y, driver_w, 18, "Водій", 7.2, bold=True)
    _cell(c, x, y + 18, 58, 18, "Таб. №", 6.2)
    _cell(c, x + 58, y + 18, driver_w - 58, 18, "Прізвище, ім’я, по батькові", 6.2)
    _cell(c, x, y + 36, 58, 70, data.get("driver_personnel_no", ""), 7, bold=True)
    _cell(c, x + 58, y + 36, driver_w - 58, 70, data.get("driver", ""), 7.2, bold=True, align="left")
    x += driver_w

    _cell(c, x, y, control_w, 18, "Передрейсовий контроль", 7.2, bold=True)
    control_rows = [
        ("Медичний контроль", data.get("doctor_1", ""), data.get("medical_checked_at", "")),
        ("Технічний контроль", data.get("mechanic_1", ""), data.get("technical_checked_at", "")),
        ("Дозвіл диспетчера", data.get("dispatcher", ""), data.get("dispatcher_checked_at", "")),
    ]
    row_h = 88 / 3
    for index, (label, person, checked_at) in enumerate(control_rows):
        yy = y + 18 + index * row_h
        _cell(c, x, yy, 95, row_h, label, 5.7, bold=True, align="left")
        _cell(c, x + 95, yy, 100, row_h, person, 5.8, bold=bool(person), align="left")
        _cell(c, x + 195, yy, 60, row_h, checked_at, 5.2)
    x += control_w

    _cell(c, x, y, return_w, 18, "Заїзд у підприємство", 7.2, bold=True)
    _cell(c, x, y + 18, return_w / 2, 18, "за графіком", 6.2)
    _cell(c, x + return_w / 2, y + 18, return_w / 2, 18, "фактично", 6.2)
    _cell(c, x, y + 36, return_w / 2, 70, data.get("planned_return", ""), 9, bold=True)
    _cell(c, x + return_w / 2, y + 36, return_w / 2, 70, data.get("actual_return", ""), 8, bold=bool(data.get("actual_return")))

    y = 226
    _text(c, margin, y - 14, right - margin, 12, "Планове завдання / рейси", 7.2, bold=True, align="left")
    widths = [60, 100, 290, 95, 95, right - margin - 640]
    headers = ["№", "Маршрут", "Найменування", "Виїзд", "Прибуття", "Примітка"]
    x = margin
    for width, header in zip(widths, headers, strict=True):
        _cell(c, x, y, width, 26, header, 6.2, bold=True)
        x += width
    trips = list(data.get("trips", []))
    for row_index in range(6):
        trip = trips[row_index] if row_index < len(trips) else {}
        values = [
            str(row_index + 1) if trip else "",
            trip.get("route_number", ""),
            trip.get("route_name", ""),
            trip.get("planned_departure", ""),
            trip.get("planned_arrival", ""),
            "",
        ]
        x = margin
        for width, value in zip(widths, values, strict=True):
            _cell(c, x, y + 26 + row_index * 24, width, 24, value, 6.2, bold=bool(value) and row_index == 0, align="left" if width >= 200 else "center")
            x += width

    y = 407
    _text(c, margin, y - 14, right - margin, 12, "Пробіг і паливо", 7.2, bold=True, align="left")
    metrics = [
        ("Спідометр при виїзді", data.get("odometer_start", ""), "км"),
        ("Спідометр при поверненні", data.get("odometer_end", ""), "км"),
        ("Пробіг плановий", data.get("planned_distance_km", ""), "км"),
        ("Пробіг фактичний", data.get("distance_km", ""), "км"),
        ("Паливо при виїзді", data.get("fuel_start", ""), "л"),
        ("Видано / заправлено", data.get("fuel_issued", ""), "л"),
        ("Паливо при поверненні", data.get("fuel_end", ""), "л"),
        ("Витрачено фактично", data.get("fuel_used", ""), "л"),
    ]
    box_w = (right - margin) / 4
    for index, (label, value, unit) in enumerate(metrics):
        col = index % 4
        row = index // 4
        xx = margin + col * box_w
        yy = y + row * 58
        _cell(c, xx, yy, box_w, 24, label, 5.8, bold=True)
        shown = f"{value} {unit}".strip() if value not in (None, "") else ""
        _cell(c, xx, yy + 24, box_w, 34, shown, 8, bold=bool(shown))

    y = 537
    _cell(c, margin, y, 240, 46, "Автобус технічно справний. Виїзд дозволено.\nМеханік: ______________________________", 6.0, align="left")
    _cell(c, margin + 240, y, 220, 46, "Водій автобус прийняв.\nПідпис: ______________________________", 6.0, align="left")
    _cell(c, margin + 460, y, 250, 46, "При поверненні: справний / несправний.\nЗдав водій: __________  Прийняв механік: __________", 5.7, align="left")
    _cell(c, margin + 710, y, right - margin - 710, 46, "Особливі відмітки", 5.8, bold=True)
    c.showPage()


def _direction_table(
    c: Any,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    rows: Sequence[Mapping[str, Any]],
) -> None:
    _cell(c, x, y, w, 20, title, 7.2, bold=True)
    name_w = w * 0.34
    small = (w - name_w) / 5
    widths = [name_w] + [small] * 5
    headers = ["Зупинка / пункт", "Приб. план", "Приб. факт", "Відпр. план", "Відпр. факт", "Відмітки"]
    xx = x
    for width, header in zip(widths, headers, strict=True):
        _cell(c, xx, y + 20, width, 42, header, 5.5, bold=True)
        xx += width
    body_y = y + 62
    row_h = (h - 62) / 15
    for index in range(15):
        row = rows[index] if index < len(rows) else {}
        values = [
            row.get("stop_name", ""),
            row.get("arrival_time", ""),
            "",
            row.get("departure_time", ""),
            "",
            row.get("note", ""),
        ]
        xx = x
        for col, (width, value) in enumerate(zip(widths, values, strict=True)):
            _cell(c, xx, body_y + index * row_h, width, row_h, value, 5.5, bold=bool(value) and col in (0, 1, 3), align="left" if col in (0, 5) else "center")
            xx += width


def _page_two(c: Any, data: Mapping[str, Any]) -> None:
    margin = 24
    table_w = (W - 2 * margin) / 2
    table_h = 428
    directions = list(data.get("directions", []))
    left = directions[0] if directions else {"title": "Маршрут / напрямок 1", "stops": []}
    right = directions[1] if len(directions) > 1 else {"title": "Маршрут / напрямок 2", "stops": []}
    _direction_table(c, margin, 20, table_w, table_h, str(left.get("title") or "Напрямок 1"), list(left.get("stops", [])))
    _direction_table(c, margin + table_w, 20, table_w, table_h, str(right.get("title") or "Напрямок 2"), list(right.get("stops", [])))

    y = 458
    widths = [135, 150, 110, 145, 145, W - 2 * margin - 685]
    headers = [
        "Відмітки медика",
        "Спідометр / пробіг",
        "Механік",
        "Дорожні відмітки",
        "Лінійний контроль",
        "Час і причина заїзду",
    ]
    x = margin
    for width, header in zip(widths, headers, strict=True):
        _cell(c, x, y, width, 30, header, 6.0, bold=True)
        x += width

    x = margin
    body_h = 96
    odometer_lines: list[str] = []
    if data.get("odometer_start") not in (None, ""):
        odometer_lines.append(f"поч. {data.get('odometer_start')} км")
    if data.get("odometer_end") not in (None, ""):
        odometer_lines.append(f"кін. {data.get('odometer_end')} км")
    if data.get("distance_km") not in (None, ""):
        odometer_lines.append(f"факт {data.get('distance_km')} км")
    if data.get("planned_distance_km") not in (None, ""):
        odometer_lines.append(f"план {data.get('planned_distance_km')} км")
    body_values = [
        f"{data.get('doctor_1', '')}\n{data.get('medical_checked_at', '')}".strip(),
        "\n".join(odometer_lines),
        f"{data.get('mechanic_1', '')}\n{data.get('technical_checked_at', '')}".strip(),
        "",
        "",
        "",
    ]
    for width, value in zip(widths, body_values, strict=True):
        _cell(c, x, y + 30, width, body_h, value, 5.8, bold=bool(value), align="left", valign="top")
        x += width
    c.showPage()


def build_waybill_pdf(output_path: Path, data: Mapping[str, Any]) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=PAGE, pageCompression=1)
    c.setTitle(f"Шляховий лист {data.get('waybill_no', '')}")
    c.setAuthor("TransportERP-UA")
    c.setSubject("Шляховий лист автобуса")
    _page_one(c, data)
    _page_two(c, data)
    c.save()
    return output_path
