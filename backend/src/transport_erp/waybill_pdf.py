# -*- coding: utf-8 -*-
# ruff: noqa
# mypy: ignore-errors
"""Векторне відтворення двосторонньої автобусної шляхівки форми № 1-АП.

Скан користувача є еталоном структури, але не друкується фоном: лінії та
написи будуються заново. Renderer перенесено з Taxo без спрощення макета.
TransportERP підставляє відомі планові дані; порожні клітинки залишаються
для фактичних відміток під час рейсу.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta
import os
import sys

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


PAGE = landscape(A4)
W, H = PAGE
INK = (0.08, 0.10, 0.13)


def _font_candidates(bold=False):
    if os.name == "nt":
        return [r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
                r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf"]
    if sys.platform == "darwin":
        return ["/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf"]
    return ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]


def _register_fonts():
    found = []
    for name, bold in (("WB", False), ("WB-Bold", True)):
        for candidate in _font_candidates(bold):
            if os.path.exists(candidate):
                pdfmetrics.registerFont(TTFont(name, candidate))
                found.append(name)
                break
    return ("WB" if "WB" in found else "Helvetica",
            "WB-Bold" if "WB-Bold" in found else "Helvetica-Bold")


FONT, FONT_BOLD = _register_fonts()


def _y(top):
    return H - top


def _line(c, x1, y1, x2, y2, width=0.55):
    c.setStrokeColorRGB(*INK); c.setLineWidth(width)
    c.line(x1, _y(y1), x2, _y(y2))


def _box(c, x, y, w, h, width=0.55):
    c.setStrokeColorRGB(*INK); c.setLineWidth(width)
    c.rect(x, _y(y + h), w, h, stroke=1, fill=0)


def _wrap(text, font, size, max_width):
    lines = []
    for para in str(text or "").split("\n"):
        words = para.split()
        if not words:
            lines.append(""); continue
        current = words[0]
        for word in words[1:]:
            trial = current + " " + word
            if pdfmetrics.stringWidth(trial, font, size) <= max_width:
                current = trial
            else:
                lines.append(current); current = word
        lines.append(current)
    return lines


def _text(c, x, y, w, h, text, size=7.2, *, bold=False, align="center", valign="middle", pad=2):
    text = str(text or "").strip()
    if not text:
        return
    font = FONT_BOLD if bold else FONT
    actual = float(size)
    lines = _wrap(text, font, actual, max(4, w - pad * 2))
    while actual > 4.1 and (len(lines) * actual * 1.13 > h - 2 or any(
        pdfmetrics.stringWidth(line, font, actual) > w - pad * 2 for line in lines)):
        actual -= 0.25
        lines = _wrap(text, font, actual, max(4, w - pad * 2))
    leading = actual * 1.13
    total = len(lines) * leading
    if valign == "top": baseline = _y(y + pad + actual)
    elif valign == "bottom": baseline = _y(y + h - pad - (len(lines) - 1) * leading)
    else: baseline = _y(y + (h - total) / 2 + actual)
    c.setFillColorRGB(*INK); c.setFont(font, actual)
    for i, line in enumerate(lines):
        yy = baseline - i * leading
        if align == "left": c.drawString(x + pad, yy, line)
        elif align == "right": c.drawRightString(x + w - pad, yy, line)
        else: c.drawCentredString(x + w / 2, yy, line)


def _vtext(c, x, y, w, h, text, size=6.2, bold=False):
    text=str(text or "").replace("\n"," ").strip()
    if not text: return
    font=FONT_BOLD if bold else FONT
    actual=min(float(size),max(4.1,w-3))
    while actual>4.1 and pdfmetrics.stringWidth(text,font,actual)>h-4: actual-=.2
    c.saveState(); c.translate(x+w/2,_y(y+h/2)); c.rotate(90)
    c.setFillColorRGB(*INK); c.setFont(font,actual); c.drawCentredString(0,-actual*.34,text)
    c.restoreState()


def _cell(c, x, y, w, h, text="", size=6.8, *, bold=False, align="center", valign="middle", width=0.55):
    _box(c, x, y, w, h, width)
    _text(c, x, y, w, h, text, size, bold=bold, align=align, valign=valign)


def _value_line(c, x, y, w, label, value="", label_w=None, size=7.0):
    label_w = label_w or min(w * .42, pdfmetrics.stringWidth(label, FONT, size) + 5)
    _text(c, x, y, label_w, 13, label, size, align="left")
    _line(c, x + label_w, y + 11, x + w, y + 11, .45)
    _text(c, x + label_w, y, w - label_w, 11, value, size, bold=bool(value), align="left")


def _scaled_widths(widths, total):
    scale = float(total) / sum(widths)
    return [value * scale for value in widths]


def _page_one(c, data):
    m, right = 18, W - 18
    _box(c, m, 18, 145, 92, .8)
    _text(c, m + 4, 23, 137, 18, "Місце для штампа\nавтопідприємства", 7, align="left", valign="top")
    _text(c, m + 4, 51, 137, 48, data.get("company_name", ""), 7, bold=True, align="left", valign="top")

    cx, cw = m + 145, 438
    _text(c, cx, 19, cw, 16, "Міністерство автомобільного транспорту України", 9, bold=True)
    _text(c, cx, 36, cw, 20, "ДОРОЖНІЙ ЛИСТ", 13, bold=True)
    _text(c, cx + 272, 37, 42, 18, "№", 9, bold=True, align="right")
    _text(c, cx + 314, 35, 116, 22, data.get("waybill_no", ""), 11.5, bold=True, align="left")
    _text(c, cx + 18, 58, 185, 14, data.get("date", ""), 8, bold=True)
    _text(c, cx + 212, 58, 110, 14, f"Серія {data.get('waybill_series','АААТ')}", 8, bold=True)
    _value_line(c, cx + 8, 77, cw - 16, "Маршрут (замовник)", data.get("route", ""), 92, 7.2)
    endpoints=""
    if data.get("start_location") or data.get("end_location"):
        endpoints=f"Початок роботи: {data.get('start_location','')}  →  завершення: {data.get('end_location','')}"
    _text(c,cx+10,91,cw-20,15,endpoints,5.8,bold=bool(endpoints),align="left")

    rx, rw = cx + cw, right - (cx + cw)
    _text(c, rx, 18, rw, 12, "Форма № 1-АП", 6.6, bold=True, align="right")
    _text(c, rx, 29, rw, 13, "Затверджено Міністерством автотранспорту України 17.06.1980 р. № 185", 4.8, align="right")
    _value_line(c, rx + 4, 46, rw - 66, "Колона", data.get("transport_column", ""), 34, 6.4)
    _value_line(c, rx + 4, 61, rw - 66, "Бригада", data.get("brigade", ""), 34, 6.4)
    _value_line(c, rx + 4, 76, rw - 66, "Автобус", data.get("vehicle", ""), 34, 6.4)
    _text(c, rx + 37, 89, rw - 103, 11, "марка, держ №, гар. №", 5.1)
    bx = right - 62
    for i in range(3):
        _cell(c, bx, 43 + i * 18, 16, 18, str(i + 1), 6.5, bold=True)
        _cell(c, bx + 16, 43 + i * 18, 46, 18)

    y, x = 110, m
    dep_w, driver_w, trainee_w, return_w = 158, 240, 240, right - m - 158 - 240 - 240
    _cell(c, x, y, dep_w, 16, "Виїзд із АТП", 7.3, bold=True)
    _cell(c, x, y + 16, dep_w / 2, 14, "фактично", 6.4); _cell(c, x + dep_w / 2, y + 16, dep_w / 2, 14, "за графіком", 6.4)
    for j, label in enumerate(("I зм.", "II зм.", "I зм.", "II зм.")):
        _cell(c, x + j * dep_w / 4, y + 30, dep_w / 4, 14, label, 5.8)
    for j in range(4):
        val = data.get("planned_departure", "") if j == 2 else ""
        _cell(c, x + j * dep_w / 4, y + 44, dep_w / 4, 64, val, 8.2, bold=bool(val))
    x += dep_w
    _cell(c, x, y, driver_w, 16, "Водій", 7.3, bold=True)
    sub = [30, driver_w - 96, 66]
    xx = x
    for ww, label in zip(sub, ("зм/7", "Прізвище, ім’я, по батькові", "Таб. №")):
        _cell(c, xx, y + 16, ww, 16, label, 5.9); xx += ww
    for row, shift in enumerate(("I", "II")):
        yy = y + 32 + row * 18
        _cell(c, x, yy, sub[0], 18, shift, 6.3)
        _cell(c, x + sub[0], yy, sub[1], 18, data.get("driver", "") if row == 0 else "", 6.4, bold=row == 0, align="left")
        _cell(c, x + sub[0] + sub[1], yy, sub[2], 18, data.get("driver_personnel_no", "") if row == 0 else "", 6.3)
    _cell(c, x, y + 68, driver_w, 14, "Кондуктор", 6.8, bold=True)
    for row, shift in enumerate(("I", "II")):
        yy = y + 82 + row * 13
        _cell(c, x, yy, 30, 13, shift, 5.8); _cell(c, x + 30, yy, driver_w - 96, 13); _cell(c, x + driver_w - 66, yy, 66, 13)
    x += driver_w
    _cell(c, x, y, trainee_w, 16, "Стажер", 7.3, bold=True)
    sub2 = [30, trainee_w - 94, 64]
    xx = x
    for ww, label in zip(sub2, ("зм.", "Прізвище, ім’я, по батькові", "Таб. №")):
        _cell(c, xx, y + 16, ww, 16, label, 5.9); xx += ww
    for row, shift in enumerate(("I", "II")):
        yy = y + 32 + row * 18
        _cell(c, x, yy, sub2[0], 18, shift, 6.3); _cell(c, x + sub2[0], yy, sub2[1], 18); _cell(c, x + sub2[0] + sub2[1], yy, sub2[2], 18)
    _box(c, x, y + 68, trainee_w, 40)
    _text(c, x + 3, y + 68, trainee_w - 6, 11, "Автомобіль технічно справний", 5.7, align="left")
    _text(c, x + 3, y + 79, 115, 11, "Виїзд дозволено, механік", 5.5, align="left")
    _text(c, x + 115, y + 79, trainee_w - 118, 11, data.get("mechanic_1", ""), 5.4, bold=bool(data.get("mechanic_1")), align="left")
    _text(c, x + 3, y + 90, trainee_w - 6, 9, "Автомобіль прийняв, підпис водія __________________", 5.2, align="left")
    _text(c, x + 3, y + 99, trainee_w - 6, 9, "При поверненні: справний / несправний; здав водій ______ механік ______", 4.9, align="left")
    x += trainee_w
    _cell(c, x, y, return_w, 16, "Заїзд в АТП", 7.3, bold=True)
    _cell(c, x, y + 16, return_w / 2, 14, "за графіком", 6.2); _cell(c, x + return_w / 2, y + 16, return_w / 2, 14, "фактично", 6.2)
    for j, label in enumerate(("I зм.", "II зм.", "I зм.", "II зм.")):
        _cell(c, x + j * return_w / 4, y + 30, return_w / 4, 14, label, 5.6)
    for j in range(4):
        val = data.get("planned_return", "") if j == 0 else ""
        _cell(c, x + j * return_w / 4, y + 44, return_w / 4, 64, val, 8.2, bold=bool(val))

    y = 218
    widths = _scaled_widths([42,27,27,39,35,42,34,31,34,34,34,36,55,27,31,31,38,39,29,44,30,30,30,30,30], right-m)
    labels = ["Шифр маршруту (замовника)","Графік","Зміна","на маршруті","з розривом","на обслуговуванні - всього","у т.ч. підготовчий простій","резерв робочого часу","простій за техн. несправн.","через бездоріжжя","з інших причин","в резерві","всього у наряді","нічний","к-сть повн. змін","святковий","за графіком - всього","у т.ч. у години «пік»","дні роз’їзду","план","план скорочений","факт з кондуктором","факт без кондуктора","за відомістю","до відомості"]
    x, header_h = m, 74
    for i, (ww, label) in enumerate(zip(widths, labels), 12):
        _cell(c, x, y, ww, header_h); _vtext(c, x, y + 2, ww, header_h - 17, label, 5.2); _text(c, x, y + header_h - 15, ww, 15, str(i), 5.5, bold=True); x += ww
    route_values = {12:data.get("route_code", ""),13:data.get("schedule_code", ""),14:"I",15:data.get("planned_route_time", ""),24:data.get("planned_duty_time", "")}
    for row in range(4):
        x = m
        for i, ww in enumerate(widths, 12):
            _cell(c, x, y + header_h + row * 20, ww, 20, route_values.get(i, "") if row == 0 else "", 5.8, bold=row == 0 and i in route_values); x += ww

    y = y + header_h + 85
    cols = _scaled_widths([28,34,40,43,42,48,43,30,32,37,37,37,34,34,35,35,35,35,35,35,35,35,35,35,37,37,37], right-m)
    heads = ["№ зміни","загальний","з пасажирами","на обслуговуванні","нульовий та інші","Пасажири","Пасажиро-км","задано","всього","за графіком","з них у години «пік»","в талонах","натурою","за талонами","натурою I","натурою II","в талонах","натурою","фактично","за нормою","економія","перевитрата","талони","натурою","в талонах","в натурі","контрольна сума"]
    _text(c,m+28,y-12,sum(cols[1:5]),12,"Пробіг",6.5,bold=True); _text(c,m+sum(cols[:5]),y-12,sum(cols[5:7]),12,"Пасажири",6.5,bold=True); _text(c,m+sum(cols[:7]),y-12,sum(cols[7:11]),12,"Рейси",6.5,bold=True); _text(c,m+sum(cols[:11]),y-12,sum(cols[11:]),12,"Рух пального",6.5,bold=True)
    x = m
    for j,(ww,head) in enumerate(zip(cols,heads)):
        _cell(c,x,y,ww,62); _vtext(c,x,y+1,ww,47,head,4.9); _text(c,x,y+47,ww,15,"А" if j==0 else str(36+j),5.1,bold=True); x+=ww
    for row in range(4):
        x=m
        for j,ww in enumerate(cols):
            val="I" if row==0 and j==0 else "II" if row==2 and j==0 else ""
            if row==0 and j==1 and data.get("planned_distance_km") is not None:
                val=str(int(data["planned_distance_km"]))
            _cell(c,x,y+62+row*18,ww,18,val,5.8,bold=bool(val)); x+=ww
    sig_y=y+134; _line(c,m,sig_y,right,sig_y,.8)
    for xx,ww,label in ((m+390,70,"підпис механіка"),(m+470,80,"підпис заправника"),(m+557,70,"підпис механіка"),(m+676,110,"підпис відповідальної особи")):
        _text(c,xx,sig_y,ww,17,label,5)
    c.showPage()


def _route_date(data, day_offset):
    raw=(data.get("work_date") or "").strip()
    if raw:
        base=datetime.strptime(raw,"%Y-%m-%d").date()
    else:
        first=(data.get("date") or "").split(" - ",1)[0].strip()
        base=datetime.strptime(first,"%d.%m.%Y").date()
    return (base+timedelta(days=int(day_offset or 0))).strftime("%d.%m.%Y")


def _direction_table(c, x, y, w, h, title, rows, data):
    _cell(c,x,y,w,18,title,7.2,bold=True)
    name_w=w*.27; small=(w-name_w)/6; widths=[name_w]+[small]*6
    heads=["найменування,\nномер маршруту,\nштамп автостанції","прибуття\nза графіком","прибуття\nфактично","відправлення\nза графіком","відправлення\nфактично","підпис","особливі\nвідмітки"]
    xx=x
    for ww,head in zip(widths,heads): _cell(c,xx,y+18,ww,47,head,5.5,bold=True); xx+=ww
    body_y=y+65; row_h=(h-65)/15
    for i in range(15):
        row=rows[i] if i<len(rows) else {}
        if row:
            arrival_day=int(row.get("arrival_day_offset",row.get("day_offset",0)) or 0)
            departure_day=int(row.get("departure_day_offset",row.get("day_offset",0)) or 0)
            point_type=(row.get("point_type","") or "").strip()
            if row.get("arrival_time") and row.get("departure_time") and arrival_day!=departure_day:
                prefix=f"{_route_date(data,arrival_day)} - {_route_date(data,departure_day)}"
            elif row.get("arrival_time"):
                prefix=_route_date(data,arrival_day)
            else:
                prefix=_route_date(data,departure_day)
            if point_type: prefix+=f" · {point_type}"
            stop_label=f"{prefix}\n{row.get('stop_name','')}".strip()
        else:
            stop_label=""
        vals=[stop_label,row.get("arrival_time",""),"",row.get("departure_time",""),"","",row.get("note","")]
        xx=x
        for j,(ww,val) in enumerate(zip(widths,vals)):
            _cell(c,xx,body_y+i*row_h,ww,row_h,val,5.6,bold=bool(val) and j in (0,1,3),align="left" if j in (0,6) else "center"); xx+=ww


def _page_two(c,data):
    m=24; table_w=(W-2*m)/2; table_h=432
    start_direction=data.get("start_direction","outbound")
    out_title="Прямий напрямок"+(" — ПОЧАТОК РОБОТИ" if start_direction=="outbound" else "")
    ret_title="Зворотний напрямок"+(" — ПОЧАТОК РОБОТИ" if start_direction=="return" else "")
    _direction_table(c,m,20,table_w,table_h,out_title,data.get("outbound_stops",[]),data)
    _direction_table(c,m+table_w,20,table_w,table_h,ret_title,data.get("return_stops",[]),data)
    y=458; widths=_scaled_widths([125,125,70,145,165,165],W-2*m)
    heads=["Відмітки лікаря","Спідометр,\nпочаток зміни / кінець зміни","Підпис\nмеханіка","Зауваження ДАІ\nта служби руху","Відмітки лінійного контролю","Час і причина заїзду\nв гараж"]
    x=m
    for ww,head in zip(widths,heads): _cell(c,x,y,ww,30,head,6,bold=True); x+=ww
    x=m; body_h=94
    for idx,ww in enumerate(widths):
        _cell(c,x,y+30,ww,body_h)
        if idx==0:
            _line(c,x+ww/2,y+30,x+ww/2,y+30+body_h); _text(c,x,y+30,ww/2,14,"I",5.8,bold=True); _text(c,x+ww/2,y+30,ww/2,14,"II",5.8,bold=True)
            _text(c,x+2,y+44,ww/2-4,body_h-16,data.get("doctor_1",""),5.6,bold=bool(data.get("doctor_1")),valign="top")
            _text(c,x+ww/2+2,y+44,ww/2-4,body_h-16,data.get("doctor_2",""),5.6,bold=bool(data.get("doctor_2")),valign="top")
        elif idx==1:
            _line(c,x+28,y+30,x+28,y+30+body_h); _line(c,x,y+30+body_h/2,x+ww,y+30+body_h/2)
            _text(c,x,y+30,28,body_h/2,"I",5.8,bold=True); _text(c,x,y+30+body_h/2,28,body_h/2,"II",5.8,bold=True)
            odometer_lines=[]
            if data.get("odometer_start") is not None:
                odometer_lines.append(f"поч. {int(data['odometer_start'])} км")
            if data.get("odometer_end") is not None:
                odometer_lines.append(f"кін. {int(data['odometer_end'])} км")
            if data.get("distance_km") is not None:
                odometer_lines.append(f"пробіг {int(data['distance_km'])} км (факт)")
            if data.get("planned_distance_km") is not None:
                odometer_lines.append(f"план {int(data['planned_distance_km'])} км")
            _text(c,x+30,y+32,ww-32,body_h/2-4,"\n".join(odometer_lines),5.9,
                  bold=bool(odometer_lines),align="left",valign="top")
        elif idx==2:
            _line(c,x,y+30+body_h/2,x+ww,y+30+body_h/2)
            _text(c,x+2,y+34,ww-4,body_h/2-6,data.get("mechanic_1",""),5.2,bold=bool(data.get("mechanic_1")),valign="top")
            _text(c,x+2,y+32+body_h/2,ww-4,body_h/2-6,data.get("mechanic_2",""),5.2,bold=bool(data.get("mechanic_2")),valign="top")
        x+=ww
    c.showPage()


def build_waybill_pdf(template_path, output_path, data):
    """Створити двосторінкову A4-шляхівку; template_path лишено для сумісності."""
    output_path=Path(output_path); output_path.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(output_path),pagesize=PAGE,pageCompression=1)
    c.setTitle(f"Шляхівка {data.get('waybill_no','')}"); c.setAuthor("TransportERP-UA / Taxo")
    c.setSubject("Шляхівка автобуса, сформована з планового графіка")
    _page_one(c,data); _page_two(c,data); c.save(); return output_path
