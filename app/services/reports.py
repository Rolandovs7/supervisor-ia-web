"""PDF safety reports generated with ReportLab."""

from datetime import datetime
from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_PRIMARY = colors.HexColor("#0f172a")
_ACCENT = colors.HexColor("#0d8bff")
_MUTED = colors.HexColor("#64748b")
_BORDER = colors.HexColor("#cbd5e1")
_STRIPE = colors.HexColor("#f1f5f9")
_LEVEL_COLORS = {
    "alto": "#be123c",
    "medio": "#b45309",
    "baja": "#047857",
}

_MARGIN = 18 * mm


def _format_date(value: Any) -> str:
    """Render a Supabase timestamp as dd/mm/yyyy HH:MM."""
    if not value:
        return "—"
    if isinstance(value, datetime):
        moment = value
    else:
        try:
            moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return str(value)
    return moment.strftime("%d/%m/%Y %H:%M")


def _footer(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(_MUTED)
    canvas.drawString(_MARGIN, 12 * mm, "Supervisor IA · Reporte de seguridad")
    canvas.drawRightString(A4[0] - _MARGIN, 12 * mm, f"Página {doc.page}")
    canvas.restoreState()


def build_obra_report(obra: dict[str, Any], alertas: list[dict[str, Any]]) -> bytes:
    """Build a PDF report for one construction site and return its bytes."""
    title_style = ParagraphStyle(
        "ReportTitle",
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=23,
        textColor=_PRIMARY,
        spaceAfter=4,
    )
    label_style = ParagraphStyle(
        "ReportLabel",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=_MUTED,
    )
    value_style = ParagraphStyle(
        "ReportValue",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=_PRIMARY,
    )
    cell_style = ParagraphStyle(
        "ReportCell",
        fontName="Helvetica",
        fontSize=9,
        leading=12,
    )
    header_cell_style = ParagraphStyle(
        "ReportHeaderCell",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.white,
    )

    nombre = str(obra.get("nombre") or "Obra sin nombre")
    ubicacion = str(obra.get("ubicacion") or "No indicada")
    pending = sum(not alerta.get("resuelta", False) for alerta in alertas)

    banner = Table(
        [
            [
                Paragraph(
                    '<font color="#ffffff">SUPERVISOR IA</font>',
                    ParagraphStyle(
                        "BannerBrand",
                        fontName="Helvetica-Bold",
                        fontSize=10,
                        leading=13,
                    ),
                ),
                Paragraph(
                    '<font color="#ffffff">REPORTE DE SEGURIDAD</font>',
                    ParagraphStyle(
                        "BannerTitle",
                        fontName="Helvetica-Bold",
                        fontSize=10,
                        leading=13,
                        alignment=2,
                    ),
                ),
            ]
        ],
        colWidths=[A4[0] / 2 - _MARGIN, A4[0] / 2 - _MARGIN],
    )
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _PRIMARY),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )

    meta = Table(
        [
            [
                Paragraph("UBICACIÓN", label_style),
                Paragraph(escape(ubicacion), value_style),
                Paragraph("GENERADO", label_style),
                Paragraph(_format_date(datetime.now()), value_style),
            ]
        ],
        colWidths=[70, 160, 70, 160],
    )
    meta.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.6, _BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    summary = Table(
        [
            [
                Paragraph("TOTAL ALERTAS", label_style),
                Paragraph("PENDIENTES", label_style),
                Paragraph("RESUELTAS", label_style),
            ],
            [
                Paragraph(str(len(alertas)), value_style),
                Paragraph(str(pending), value_style),
                Paragraph(str(len(alertas) - pending), value_style),
            ],
        ],
        colWidths=[(A4[0] - 2 * _MARGIN) / 3] * 3,
    )
    summary.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _STRIPE),
                ("BOX", (0, 0), (-1, -1), 0.6, _BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, _BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    data = [
        [
            Paragraph("FECHA", header_cell_style),
            Paragraph("TIPO", header_cell_style),
            Paragraph("NIVEL", header_cell_style),
            Paragraph("ESTADO", header_cell_style),
        ]
    ]
    for alerta in alertas:
        nivel = str(alerta.get("nivel") or "baja")
        color = _LEVEL_COLORS.get(nivel.lower(), _MUTED.hexval().replace("0x", "#")[:7])
        estado = "Resuelta" if alerta.get("resuelta") else "Pendiente"
        data.append(
            [
                Paragraph(escape(_format_date(alerta.get("created_at"))), cell_style),
                Paragraph(escape(str(alerta.get("tipo") or "—")), cell_style),
                Paragraph(
                    f'<font color="{color}"><b>{escape(nivel.upper())}</b></font>',
                    cell_style,
                ),
                Paragraph(escape(estado), cell_style),
            ]
        )

    if not alertas:
        data.append(
            [
                Paragraph(
                    "No hay alertas registradas para esta obra.",
                    cell_style,
                ),
                "",
                "",
                "",
            ]
        )

    alerts_table = Table(
        data,
        colWidths=[120, 150, 85, (A4[0] - 2 * _MARGIN) - 355],
        repeatRows=1,
    )
    alerts_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _PRIMARY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _STRIPE]),
                ("GRID", (0, 0), (-1, -1), 0.4, _BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LINEBELOW", (0, 0), (-1, 0), 1.2, _ACCENT),
            ]
        )
    )

    story = [
        banner,
        Spacer(1, 16),
        Paragraph(escape(nombre), title_style),
        meta,
        Spacer(1, 16),
        summary,
        Spacer(1, 18),
        alerts_table,
    ]

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=_MARGIN,
        rightMargin=_MARGIN,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=f"Reporte de seguridad - {nombre}",
        author="Supervisor IA",
    )
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
