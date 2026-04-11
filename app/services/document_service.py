from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from fastapi import HTTPException, status
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.enums import OrderStatus
from app.models.order import Order


def _find_font_path(paths: list[str]) -> str | None:
    for path in paths:
        if Path(path).exists():
            return path
    return None


def _register_fonts() -> tuple[str, str]:
    regular_name = "AppFont"
    bold_name = "AppFontBold"

    registered = pdfmetrics.getRegisteredFontNames()
    if regular_name in registered and bold_name in registered:
        return regular_name, bold_name

    regular_path = _find_font_path(
        [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/Library/Fonts/Arial.ttf",
        ]
    )
    bold_path = _find_font_path(
        [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
        ]
    )

    if not regular_path:
        raise RuntimeError("Не найден TTF-шрифт с поддержкой кириллицы для PDF")

    pdfmetrics.registerFont(TTFont(regular_name, regular_path))

    if bold_path:
        pdfmetrics.registerFont(TTFont(bold_name, bold_path))
    else:
        bold_name = regular_name

    return regular_name, bold_name


def _money(value: Decimal | float | int | None) -> str:
    if value is None:
        return "—"
    return f"{Decimal(value):.2f}".replace(".", ",") + " ₽"

def _qty(value: Decimal | float | int | None) -> str:
    if value is None:
        return "—"

    value = Decimal(value)
    text = f"{value:.2f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.replace(".", ",")


def _dt(value: datetime | None) -> str:
    if not value:
        return "—"
    return value.strftime("%d.%m.%Y")


def _status_label(status_value: str) -> str:
    labels = {
        OrderStatus.new.value: "Новая",
        OrderStatus.diagnostics.value: "Диагностика",
        OrderStatus.estimate_approved.value: "Смета согласована",
        OrderStatus.in_progress.value: "В работе",
        OrderStatus.done.value: "Выполнена",
        OrderStatus.awaiting_payment.value: "Ожидание оплаты",
        OrderStatus.closed.value: "Закрыта",
    }
    return labels.get(status_value, status_value)


def _person_name(user) -> str:
    if not user:
        return "—"
    parts = [user.last_name, user.first_name, user.middle_name]
    full_name = " ".join(part for part in parts if part)
    return full_name or user.email or "—"


def _base_styles():
    font_name, bold_font_name = _register_fonts()
    sample = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "DocTitle",
            parent=sample["Heading1"],
            fontName=bold_font_name,
            fontSize=16,
            leading=20,
            spaceAfter=10,
        ),
        "subtitle": ParagraphStyle(
            "DocSubtitle",
            parent=sample["Heading2"],
            fontName=bold_font_name,
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=6,
        ),
        "normal": ParagraphStyle(
            "DocNormal",
            parent=sample["Normal"],
            fontName=font_name,
            fontSize=10,
            leading=13,
        ),
        "bold": ParagraphStyle(
            "DocBold",
            parent=sample["Normal"],
            fontName=bold_font_name,
            fontSize=10,
            leading=13,
        ),
        "small": ParagraphStyle(
            "DocSmall",
            parent=sample["Normal"],
            fontName=font_name,
            fontSize=9,
            leading=12,
        ),
    }


def _build_info_table(rows: list[list[str]], col_widths: list[float]):
    table = Table(rows, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, -1), "AppFont"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table

def _build_items_table(order: Order):
    regular_font, bold_font = _register_fonts()

    rows = [["№", "Наименование", "Кол-во", "Цена", "Сумма"]]

    if order.items:
        for index, item in enumerate(order.items, start=1):
            rows.append(
                [
                    str(index),
                    item.title or "—",
                    _qty(item.quantity),
                    _money(item.unit_price),
                    _money(item.line_total),
                ]
            )
    else:
        rows.append(
            [
                "1",
                order.title or "Работы по заявке",
                "1",
                _money(order.total_cost),
                _money(order.total_cost),
            ]
        )

    table = Table(
        rows,
        colWidths=[12 * mm, 78 * mm, 20 * mm, 28 * mm, 32 * mm],
        hAlign="LEFT",
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFF6FF")),
                ("FONTNAME", (0, 0), (-1, 0), bold_font),
                ("FONTNAME", (0, 1), (-1, -1), regular_font),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 12),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ]
        )
    )
    return table


def _paragraph(text: str, style) -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


def build_estimate_pdf(order: Order) -> bytes:
    if order.status == OrderStatus.new.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Смету можно сформировать только после начала диагностики.",
        )

    styles = _base_styles()
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    story = []

    story.append(_paragraph(f"Смета по заявке №{order.id}", styles["title"]))
    story.append(_paragraph(f"Дата формирования: {_dt(datetime.now())}", styles["normal"]))
    story.append(Spacer(1, 6))

    story.append(_paragraph("Исполнитель", styles["subtitle"]))
    story.append(_paragraph("ООО «Профсервис»", styles["normal"]))
    story.append(Spacer(1, 8))

    story.append(_paragraph("Заказчик и объект ремонта", styles["subtitle"]))
    story.append(
        _build_info_table(
            [
                ["Клиент", order.client.name if order.client else "—"],
                ["Контактное лицо", order.client.contact_person if order.client else "—"],
                ["Телефон", order.client.phone if order.client else "—"],
                ["Email", order.client.email if order.client else "—"],
                ["Оборудование", order.equipment.name if order.equipment else "—"],
                ["Модель", order.equipment.model if order.equipment else "—"],
                ["Серийный номер", order.equipment.serial_number if order.equipment else "—"],
                ["Производитель", order.equipment.manufacturer if order.equipment else "—"],
            ],
            [55 * mm, 115 * mm],
        )
    )
    story.append(Spacer(1, 10))

    story.append(_paragraph("Содержание работ", styles["subtitle"]))
    story.append(
        _build_info_table(
            [
                ["Наименование заявки", order.title or "—"],
                ["Описание", order.description or "—"],
                ["Статус", _status_label(order.status)],
                ["Ответственный инженер", _person_name(order.assignee)],
            ],
            [55 * mm, 115 * mm],
        )
    )
    story.append(Spacer(1, 10))

    story.append(_paragraph("Позиции сметы", styles["subtitle"]))
    story.append(_build_items_table(order))
    story.append(Spacer(1, 10))

    story.append(_paragraph("Итог", styles["subtitle"]))
    story.append(
        _build_info_table(
            [
                ["Итоговая сумма", _money(order.total_cost)],
            ],
            [55 * mm, 115 * mm],
        )
    )
    story.append(Spacer(1, 14))

    story.append(
        _paragraph(
            "Документ сформирован автоматически на основании данных заявки.",
            styles["small"],
        )
    )

    doc.build(story)
    return buffer.getvalue()


def build_act_pdf(order: Order) -> bytes:
    if order.status not in {
        OrderStatus.done.value,
        OrderStatus.awaiting_payment.value,
        OrderStatus.closed.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Акт можно сформировать только для выполненной заявки.",
        )

    styles = _base_styles()
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    story = []

    story.append(_paragraph(f"Акт выполненных работ №{order.id}", styles["title"]))
    story.append(_paragraph(f"Дата формирования: {_dt(datetime.now())}", styles["normal"]))
    story.append(Spacer(1, 6))

    story.append(_paragraph("Стороны", styles["subtitle"]))
    story.append(
        _build_info_table(
            [
                ["Исполнитель", "ООО «Профсервис»"],
                ["Заказчик", order.client.name if order.client else "—"],
                ["Контактное лицо", order.client.contact_person if order.client else "—"],
            ],
            [55 * mm, 115 * mm],
        )
    )
    story.append(Spacer(1, 10))

    story.append(_paragraph("Данные по заявке", styles["subtitle"]))
    story.append(
        _build_info_table(
            [
                ["Заявка", order.title or "—"],
                ["Оборудование", order.equipment.name if order.equipment else "—"],
                ["Модель", order.equipment.model if order.equipment else "—"],
                ["Серийный номер", order.equipment.serial_number if order.equipment else "—"],
                ["Исполнитель работ", _person_name(order.assignee)],
                ["Дата завершения", _dt(order.updated_at)],
            ],
            [55 * mm, 115 * mm],
        )
    )
    story.append(Spacer(1, 10))

    story.append(_paragraph("Выполненные работы", styles["subtitle"]))
    story.append(_build_items_table(order))
    story.append(Spacer(1, 10))

    story.append(
        _build_info_table(
            [
                ["Результат", "Работы выполнены в полном объёме"],
                ["Итоговая стоимость", _money(order.total_cost)],
            ],
            [55 * mm, 115 * mm],
        )
    )
    story.append(Spacer(1, 14))

    story.append(_paragraph("Подписи сторон", styles["subtitle"]))
    story.append(Spacer(1, 18))
    story.append(_paragraph("Исполнитель: ____________________", styles["normal"]))
    story.append(Spacer(1, 12))
    story.append(_paragraph("Заказчик: ______________________", styles["normal"]))

    doc.build(story)
    return buffer.getvalue()