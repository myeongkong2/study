from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "SRC_CODE_GUIDE.md"
OUT = ROOT / "outputs" / "ECD-AIG_SRC_CODE_GUIDE.pdf"
FONT_DIR = Path(r"C:\Windows\Fonts")


def register_fonts():
    pdfmetrics.registerFont(TTFont("Malgun", str(FONT_DIR / "malgun.ttf")))
    pdfmetrics.registerFont(TTFont("MalgunBold", str(FONT_DIR / "malgunbd.ttf")))


def styles():
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="Malgun", fontSize=9.2, leading=13.2, spaceAfter=5, textColor=colors.HexColor("#212529")),
        "bullet": ParagraphStyle("Bullet", parent=base["BodyText"], fontName="Malgun", fontSize=9.1, leading=12.8, leftIndent=14, firstLineIndent=-7, spaceAfter=2, textColor=colors.HexColor("#212529")),
        "number": ParagraphStyle("Number", parent=base["BodyText"], fontName="Malgun", fontSize=9.1, leading=12.8, leftIndent=16, firstLineIndent=-10, spaceAfter=2, textColor=colors.HexColor("#212529")),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontName="MalgunBold", fontSize=15, leading=19, spaceBefore=14, spaceAfter=7, textColor=colors.HexColor("#2E74B5")),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontName="MalgunBold", fontSize=11.7, leading=15, spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#1F4D78")),
        "code": ParagraphStyle("Code", parent=base["Code"], fontName="Malgun", fontSize=7.8, leading=10.2, leftIndent=8, rightIndent=8, spaceBefore=3, spaceAfter=5, backColor=colors.HexColor("#F2F4F7"), borderPadding=5),
        "cover_title": ParagraphStyle("CoverTitle", parent=base["Title"], fontName="MalgunBold", fontSize=25, leading=31, alignment=TA_CENTER, textColor=colors.HexColor("#1F4D78")),
        "cover_subtitle": ParagraphStyle("CoverSubtitle", parent=base["BodyText"], fontName="MalgunBold", fontSize=15, leading=20, alignment=TA_CENTER, textColor=colors.HexColor("#2E74B5")),
        "cover_note": ParagraphStyle("CoverNote", parent=base["BodyText"], fontName="Malgun", fontSize=10, leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#5C6670")),
        "cover_rule": ParagraphStyle("CoverRule", parent=base["BodyText"], fontName="MalgunBold", fontSize=12, leading=17, alignment=TA_CENTER, textColor=colors.HexColor("#9B1C1C")),
        "table_header": ParagraphStyle("TableHeader", parent=base["BodyText"], fontName="MalgunBold", fontSize=8.8, leading=11, textColor=colors.HexColor("#1F4D78")),
        "table_body": ParagraphStyle("TableBody", parent=base["BodyText"], fontName="Malgun", fontSize=8.5, leading=11, textColor=colors.HexColor("#212529")),
    }


def cover(st):
    return [
        Spacer(1, 1.32 * inch),
        Paragraph("ECD-AIG Planning", st["cover_title"]),
        Spacer(1, 0.12 * inch),
        Paragraph("src/ecd_aig 파이썬 소스 코드 해설서", st["cover_subtitle"]),
        Spacer(1, 0.2 * inch),
        Paragraph("응답 전 ECD-AIG 설계 추적과 위험 점검 코드를 읽기 위한 개발자 안내서", st["cover_note"]),
        Spacer(1, 0.44 * inch),
        Paragraph("핵심 원칙", st["cover_note"]),
        Spacer(1, 0.08 * inch),
        Paragraph("사전 점검 통과 != 경험적 타당도 확보", st["cover_rule"]),
        Spacer(1, 0.52 * inch),
        Paragraph("Generated for the local research prototype | 2026-06-01", st["cover_note"]),
        PageBreak(),
    ]


def index_table(st):
    rows = [
        [Paragraph("범주", st["table_header"]), Paragraph("파일", st["table_header"])],
        [Paragraph("핵심 흐름", st["table_body"]), Paragraph("models.py, validation.py, item_quality.py, pre_response.py, __main__.py", st["table_body"])],
        [Paragraph("문항 준비", st["table_body"]), Paragraph("generation.py, import_items.py, blueprint.py, simulation.py", st["table_body"])],
        [Paragraph("설명 산출물", st["table_body"]), Paragraph("ecd_report.py, caf.py, toulmin.py, dossier.py", st["table_body"])],
        [Paragraph("응답자료 이후", st["table_body"]), Paragraph("scoring.py, response_data.py, psychometrics.py, agreement.py", st["table_body"])],
        [Paragraph("출력과 화면", st["table_body"]), Paragraph("rendering.py, export.py, webapp.py, __init__.py", st["table_body"])],
    ]
    table = Table(rows, colWidths=[1.2 * inch, 5.62 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B7C4D1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return [
        Paragraph("파일 빠른 찾기", st["h1"]),
        Paragraph("처음 읽을 때는 models.py → validation.py → item_quality.py → pre_response.py → __main__.py 순서를 권장한다.", st["body"]),
        Spacer(1, 0.04 * inch),
        table,
        Spacer(1, 0.08 * inch),
    ]


def markdown_story(st):
    story = []
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    in_code = False
    code_lines = []
    skipped_title = False
    for line in lines:
        if line.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), st["code"]))
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            continue
        if line.startswith("# "):
            if not skipped_title:
                skipped_title = True
                continue
            story.append(Paragraph(escape(line[2:]), st["h1"]))
        elif line.startswith("## "):
            story.append(Paragraph(escape(line[3:]), st["h1"]))
        elif line.startswith("### "):
            story.append(Paragraph(escape(line[4:]), st["h2"]))
        elif line.startswith("- "):
            story.append(Paragraph("• " + escape(line[2:]), st["bullet"]))
        elif len(line) > 3 and line[0].isdigit() and line[1:3] == ". ":
            story.append(Paragraph(escape(line), st["number"]))
        else:
            story.append(Paragraph(escape(line), st["body"]))
    return story


def decorate_page(canvas, doc):
    page = canvas.getPageNumber()
    canvas.saveState()
    canvas.setFont("Malgun", 7.5)
    canvas.setFillColor(colors.HexColor("#5C6670"))
    canvas.drawRightString(letter[0] - 0.6 * inch, letter[1] - 0.42 * inch, "ECD-AIG Planning | Source Code Guide")
    canvas.drawRightString(letter[0] - 0.6 * inch, 0.38 * inch, f"Page {page}")
    canvas.restoreState()


def build():
    register_fonts()
    st = styles()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.58 * inch,
        bottomMargin=0.58 * inch,
        title="ECD-AIG Planning src/ecd_aig 파이썬 소스 코드 해설서",
        author="ECD-AIG Planning",
    )
    story = cover(st) + index_table(st) + markdown_story(st)
    doc.build(story, onFirstPage=decorate_page, onLaterPages=decorate_page)
    print(OUT)


if __name__ == "__main__":
    build()
