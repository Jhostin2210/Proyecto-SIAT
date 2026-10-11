"""
SIA-T: reporte del estudiante en PDF (REQ-09 y REQ-10).

Reúne en una hoja el nivel de riesgo general, el resultado de cada curso, los patrones observados y
las acciones recomendadas. Se genera en memoria y se descarga desde la ficha del estudiante.
"""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

TINTA, GRIS, LINEA = colors.HexColor("#0f172a"), colors.HexColor("#64748b"), colors.HexColor("#e2e8f0")
COLOR_NIVEL = {"Riesgo alto": colors.HexColor("#b91c1c"), "Riesgo medio": colors.HexColor("#b45309"), "Riesgo bajo": colors.HexColor("#047857")}
HEX_NIVEL = {"Riesgo alto": "#b91c1c", "Riesgo medio": "#b45309", "Riesgo bajo": "#047857"}
FONDO_NIVEL = {"Riesgo alto": colors.HexColor("#fef2f2"), "Riesgo medio": colors.HexColor("#fffbeb"), "Riesgo bajo": colors.HexColor("#ecfdf5")}

E = {
    "marca": ParagraphStyle("marca", fontName="Helvetica-Bold", fontSize=15, textColor=TINTA, leading=18),
    "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=8.5, textColor=GRIS, leading=11),
    "der": ParagraphStyle("der", fontName="Helvetica", fontSize=8.5, textColor=GRIS, leading=11, alignment=TA_RIGHT),
    "nombre": ParagraphStyle("nombre", fontName="Helvetica-Bold", fontSize=17, textColor=TINTA, leading=21),
    "titulo": ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=9, textColor=GRIS, leading=12, spaceBefore=14, spaceAfter=6),
    "texto": ParagraphStyle("texto", fontName="Helvetica", fontSize=10, textColor=TINTA, leading=14),
    "celda": ParagraphStyle("celda", fontName="Helvetica", fontSize=9.5, textColor=TINTA, leading=12),
    "pie": ParagraphStyle("pie", fontName="Helvetica", fontSize=8, textColor=GRIS, leading=11),
}


def _nota(valor) -> str:
    return "—" if valor is None else f"{valor:.0f}" if float(valor).is_integer() else f"{valor:.1f}".replace(".", ",")


def _pct(valor) -> str:
    return f"{valor * 100:.0f} %"


def reporte_estudiante(est: dict, informe: dict, modelo: str, de_practica: bool) -> bytes:
    """est: {codigo, nombre, grado}. informe: el de etl/informe.py más periodo_nombre."""
    salida = io.BytesIO()
    doc = SimpleDocTemplate(salida, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title=f"Reporte de {est['nombre']}", author="SIA-T")
    ancho = A4[0] - 36 * mm
    nivel = informe["nivel"]
    h = []

    encabezado = Table(
        [[Paragraph("SIA-T", E["marca"]), Paragraph(f"Reporte del estudiante<br/>{datetime.now():%d/%m/%Y %H:%M}", E["der"])], [Paragraph("Sistema Inteligente de Alerta Temprana · I.E.P. Peruano Francés", E["sub"]), ""]],
        colWidths=[ancho * 0.65, ancho * 0.35],
    )
    encabezado.setStyle(TableStyle([("SPAN", (1, 0), (1, 1)), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 1), ("TOPPADDING", (0, 0), (-1, -1), 1)]))
    h += [encabezado, Spacer(1, 6), HRFlowable(width="100%", thickness=0.8, color=LINEA), Spacer(1, 12)]

    h += [Paragraph(est["nombre"], E["nombre"]), Paragraph(f"{est['grado']} · Código {est['codigo']} · {informe['periodo_nombre']}", E["sub"]), Spacer(1, 10)]

    caja = Table(
        [[Paragraph(f"<font color='{HEX_NIVEL[nivel]}'><b>{nivel.upper()}</b></font>", ParagraphStyle("n", fontName="Helvetica-Bold", fontSize=13, leading=16)), Paragraph(f"Probabilidad estimada: <b>{_pct(informe['probabilidad'])}</b>", E["der"])], [Paragraph(informe["resumen"], E["texto"]), ""]],
        colWidths=[ancho * 0.6, ancho * 0.4],
    )
    caja.setStyle(TableStyle([("SPAN", (0, 1), (1, 1)), ("BACKGROUND", (0, 0), (-1, -1), FONDO_NIVEL[nivel]), ("BOX", (0, 0), (-1, -1), 0.6, COLOR_NIVEL[nivel]), ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, 0), 9), ("BOTTOMPADDING", (0, -1), (-1, -1), 9), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    h.append(caja)

    h.append(Paragraph("RESULTADO POR CURSO", E["titulo"]))
    filas = [["Curso", "Nota", "Examen", "Trabajos", "Periodo anterior", "Probabilidad", "Nivel"]]
    for c in informe["cursos"]:
        filas.append([Paragraph(c["curso"], E["celda"]), _nota(c["nota"]), _nota(c["examen"]), _nota(c["trabajos"]), _nota(c["nota_previa"]), _pct(c["probabilidad"]), Paragraph(f"<font color='{HEX_NIVEL[c['nivel']]}'><b>{c['nivel'].replace('Riesgo ', '').capitalize()}</b></font>", E["celda"])])
    tabla = Table(filas, colWidths=[ancho * w for w in (0.30, 0.10, 0.11, 0.12, 0.15, 0.12, 0.10)], repeatRows=1)
    tabla.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, 0), 8), ("TEXTCOLOR", (0, 0), (-1, 0), GRIS),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"), ("FONTSIZE", (0, 1), (-1, -1), 9.5), ("TEXTCOLOR", (0, 1), (-1, -1), TINTA),
                ("ALIGN", (1, 0), (5, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINEA), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    h.append(tabla)

    h.append(Paragraph("LO QUE SE OBSERVA", E["titulo"]))
    h += [Paragraph(f"• {p['texto']}", E["texto"]) for p in informe["patrones"]]
    h.append(Paragraph("ACCIONES RECOMENDADAS", E["titulo"]))
    h += [Paragraph(f"{i}. {a}", E["texto"]) for i, a in enumerate(informe["acciones"], start=1)]

    h += [Spacer(1, 16), HRFlowable(width="100%", thickness=0.6, color=LINEA), Spacer(1, 6)]
    pie = f"El nivel de riesgo lo estima un modelo ({modelo}) a partir de las notas y del perfil del estudiante. Es un apoyo para el tutor: no reemplaza el criterio del docente ni es una calificación."
    if de_practica:
        pie += " Reporte de demostración: el estudiante y sus datos son ficticios."
    h.append(Paragraph(pie, E["pie"]))

    doc.build(h)
    return salida.getvalue()
