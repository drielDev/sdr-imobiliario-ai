from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "relatorio_tecnico.md"
OUTPUT = ROOT / "relatorio_tecnico.pdf"


def configurar_fontes() -> tuple[str, str]:
    fontes = (
        (
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        ),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
    )
    for regular, bold in fontes:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont("Relatorio", str(regular)))
            pdfmetrics.registerFont(TTFont("Relatorio-Bold", str(bold)))
            pdfmetrics.registerFontFamily(
                "Relatorio",
                normal="Relatorio",
                bold="Relatorio-Bold",
                italic="Relatorio",
                boldItalic="Relatorio-Bold",
            )
            return "Relatorio", "Relatorio-Bold"
    return "Helvetica", "Helvetica-Bold"


def formatar_inline(texto: str) -> str:
    texto = escape(texto, quote=False)
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    texto = re.sub(r"`(.+?)`", r'<font name="Courier">\1</font>', texto)
    return texto


def construir_documento() -> None:
    fonte, fonte_negrito = configurar_fontes()
    estilos = getSampleStyleSheet()
    estilos.add(
        ParagraphStyle(
            name="CapaTitulo",
            parent=estilos["Title"],
            fontName=fonte_negrito,
            fontSize=25,
            leading=31,
            textColor=colors.HexColor("#174A42"),
            alignment=TA_CENTER,
            spaceAfter=16,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="Secao",
            parent=estilos["Heading1"],
            fontName=fonte_negrito,
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#174A42"),
            spaceBefore=13,
            spaceAfter=7,
            keepWithNext=True,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="Subsecao",
            parent=estilos["Heading2"],
            fontName=fonte_negrito,
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#A34F2B"),
            spaceBefore=9,
            spaceAfter=5,
            keepWithNext=True,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="CorpoRelatorio",
            parent=estilos["BodyText"],
            fontName=fonte,
            fontSize=9.4,
            leading=14,
            textColor=colors.HexColor("#252B2A"),
            spaceAfter=7,
            splitLongWords=True,
        )
    )
    estilos.add(
        ParagraphStyle(
            name="ListaRelatorio",
            parent=estilos["BodyText"],
            fontName=fonte,
            fontSize=9.2,
            leading=13.5,
            textColor=colors.HexColor("#252B2A"),
            spaceAfter=3,
        )
    )

    story = []
    linhas = SOURCE.read_text(encoding="utf-8").splitlines()
    indice = 0
    while indice < len(linhas):
        linha = linhas[indice].strip()
        if not linha:
            indice += 1
            continue
        if linha.startswith("# "):
            story.append(Spacer(1, 28 * mm))
            story.append(Paragraph(formatar_inline(linha[2:]), estilos["CapaTitulo"]))
            story.append(Spacer(1, 10 * mm))
        elif linha.startswith("## "):
            story.append(Paragraph(formatar_inline(linha[3:]), estilos["Secao"]))
        elif linha.startswith("### "):
            story.append(Paragraph(formatar_inline(linha[4:]), estilos["Subsecao"]))
        elif linha.startswith("- "):
            itens = []
            while indice < len(linhas) and linhas[indice].strip().startswith("- "):
                texto = formatar_inline(linhas[indice].strip()[2:])
                itens.append(ListItem(Paragraph(texto, estilos["ListaRelatorio"])))
                indice += 1
            story.append(
                ListFlowable(
                    itens,
                    bulletType="bullet",
                    start="circle",
                    leftIndent=16,
                    bulletFontName=fonte,
                    bulletFontSize=7,
                )
            )
            indice -= 1
        elif linha.startswith("``` ") or linha == "```":
            pass
        else:
            story.append(Paragraph(formatar_inline(linha), estilos["CorpoRelatorio"]))
        indice += 1

    documento = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=19 * mm,
        bottomMargin=18 * mm,
        title="Relatório Técnico: SDR Imobiliário com IA Generativa",
        author="Projeto SDR Imobiliário AI",
    )

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D6DEDA"))
        canvas.line(20 * mm, 13 * mm, A4[0] - 20 * mm, 13 * mm)
        canvas.setFont(fonte, 8)
        canvas.setFillColor(colors.HexColor("#59635F"))
        canvas.drawString(20 * mm, 8 * mm, "SDR Imobiliário AI | Relatório técnico")
        canvas.drawRightString(A4[0] - 20 * mm, 8 * mm, str(doc.page))
        canvas.restoreState()

    documento.build(story, onFirstPage=rodape, onLaterPages=rodape)
    print(f"PDF gerado: {OUTPUT}")


if __name__ == "__main__":
    construir_documento()