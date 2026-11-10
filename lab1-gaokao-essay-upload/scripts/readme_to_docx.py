"""把 README.md 转换为包含截图的 README.docx。"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

PROJECT = Path(__file__).resolve().parent.parent
README = PROJECT / "README.md"
OUTPUT = PROJECT / "README.docx"

INK = RGBColor(0x1D, 0x1C, 0x1A)
MUTED = RGBColor(0x6F, 0x69, 0x5E)
RED = RGBColor(0xA8, 0x3A, 0x2C)
CODE_COLOR = RGBColor(0x8F, 0x2F, 0x23)
CN_FONT = "微软雅黑"
SERIF_FONT = "宋体"
MONO_FONT = "Consolas"


def set_run_font(run, name=CN_FONT, size=10.5, bold=None, color=None, italic=None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color is not None:
        run.font.color.rgb = color


def shade(paragraph, fill: str):
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    p_pr.append(shd)


def add_page_number(paragraph):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)


def add_inline(paragraph, text: str, size=10.5, color=INK, bold=False):
    pattern = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))")
    position = 0
    for match in pattern.finditer(text):
        if match.start() > position:
            run = paragraph.add_run(text[position : match.start()])
            set_run_font(run, size=size, color=color, bold=bold)
        token = match.group(0)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            set_run_font(run, size=size, color=color, bold=True)
        elif token.startswith("`"):
            run = paragraph.add_run(token[1:-1])
            set_run_font(run, name=MONO_FONT, size=size - 1, color=CODE_COLOR)
        else:
            label, url = token[1:-1].split("](", 1)
            run = paragraph.add_run(label)
            set_run_font(run, size=size, color=RED, bold=False)
            run2 = paragraph.add_run(f"（{url}）")
            set_run_font(run2, size=size - 1.5, color=MUTED)
        position = match.end()
    if position < len(text):
        run = paragraph.add_run(text[position:])
        set_run_font(run, size=size, color=color, bold=bold)


def add_heading(doc, text: str, level: int):
    paragraph = doc.add_heading(level=level)
    paragraph.paragraph_format.space_before = Pt(16 if level == 1 else 12)
    paragraph.paragraph_format.space_after = Pt(6)
    size = 17 if level == 1 else 13.5
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(text)
    set_run_font(run, name=SERIF_FONT, size=size, bold=True, color=INK)
    if level == 1:
        p_pr = paragraph._p.get_or_add_pPr()
        p_bdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "6")
        bottom.set(qn("w:space"), "4")
        bottom.set(qn("w:color"), "C9B99A")
        p_bdr.append(bottom)
        p_pr.append(p_bdr)
    return paragraph


def add_cover(doc):
    for _ in range(3):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("《生成式人工智能》课程实验一")
    set_run_font(run, size=12, color=MUTED)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    run = p.add_run("文心 · 高考满分作文智能工坊")
    set_run_font(run, name=SERIF_FONT, size=28, bold=True, color=RED)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("基于提示工程的高考作文智能生成 Web 应用")
    set_run_font(run, size=13, color=INK)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("FastAPI · OpenAI SDK · DeepSeek · SSE · 原生前端")
    set_run_font(run, size=10, color=MUTED)

    for _ in range(3):
        doc.add_paragraph()

    table = doc.add_table(rows=5, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    rows = [
        ("班　　级", "网安243"),
        ("姓　　名", "付小娅"),
        ("学　　号", "202401050876"),
        ("课程名称", "生成式人工智能"),
        ("完成日期", date.today().strftime("%Y年%m月%d日")),
    ]
    for i, (key, value) in enumerate(rows):
        table.rows[i].cells[0].width = Cm(4.2)
        table.rows[i].cells[1].width = Cm(8.5)
        p0 = table.rows[i].cells[0].paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r0 = p0.add_run(key)
        set_run_font(r0, size=11, color=MUTED)
        p1 = table.rows[i].cells[1].paragraphs[0]
        r1 = p1.add_run(value)
        set_run_font(r1, size=11, color=INK, bold=True)

    doc.add_page_break()


def add_code_block(doc, lines: list[str]):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Pt(10)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.05
    shade(p, "F4F1EA")
    run = p.add_run()
    for index, line in enumerate(lines):
        if index:
            run.add_break()
        run.add_text(line)
    set_run_font(run, name=MONO_FONT, size=8.5, color=RGBColor(0x33, 0x30, 0x2B))


def add_table(doc, rows: list[list[str]]):
    cols = max(len(row) for row in rows)
    table = doc.add_table(rows=len(rows), cols=cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for r, row in enumerate(rows):
        for c in range(cols):
            cell = table.rows[r].cells[c]
            cell.text = ""
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(2)
            text = row[c] if c < len(row) else ""
            bold = r == 0
            add_inline(paragraph, text, size=9, color=INK, bold=bold)
            if bold:
                tc_pr = cell._tc.get_or_add_tcPr()
                shd = OxmlElement("w:shd")
                shd.set(qn("w:val"), "clear")
                shd.set(qn("w:color"), "auto")
                shd.set(qn("w:fill"), "F1E8D8")
                tc_pr.append(shd)


def is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells if cell.strip())


def parse_markdown(doc, text: str):
    lines = text.splitlines()
    skip_front = True
    in_code = False
    code_lines: list[str] = []
    table_lines: list[str] = []

    def flush_table():
        if not table_lines:
            return
        rows = []
        for raw in table_lines:
            cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
            if is_separator_row(cells):
                continue
            rows.append(cells)
        if rows:
            add_table(doc, rows)
            doc.add_paragraph()
        table_lines.clear()

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                add_code_block(doc, code_lines)
                code_lines = []
                in_code = False
            else:
                flush_table()
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue

        if stripped.startswith("|"):
            table_lines.append(stripped)
            continue
        flush_table()

        if skip_front and stripped.startswith("# "):
            continue
        if skip_front and stripped.startswith(">"):
            continue
        if stripped == "---":
            skip_front = False
            continue

        image = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if image:
            alt, src = image.group(1), image.group(2)
            path = (PROJECT / src).resolve()
            if path.exists():
                paragraph = doc.add_paragraph()
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                paragraph.paragraph_format.space_before = Pt(6)
                paragraph.paragraph_format.space_after = Pt(3)
                run = paragraph.add_run()
                width = Inches(3.4) if "mobile" in path.name else Inches(6.25)
                run.add_picture(str(path), width=width)
                caption = doc.add_paragraph()
                caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
                caption.paragraph_format.space_after = Pt(12)
                c_run = caption.add_run(alt)
                set_run_font(c_run, size=9, color=MUTED, italic=True)
            continue

        if stripped.startswith("# "):
            continue
        if stripped.startswith("## "):
            skip_front = False
            add_heading(doc, stripped[3:].strip(), level=1)
            continue
        if stripped.startswith("### "):
            skip_front = False
            add_heading(doc, stripped[4:].strip(), level=2)
            continue

        if not stripped:
            continue

        if stripped.startswith("> "):
            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.left_indent = Pt(14)
            paragraph.paragraph_format.right_indent = Pt(14)
            paragraph.paragraph_format.space_before = Pt(4)
            paragraph.paragraph_format.space_after = Pt(6)
            shade(paragraph, "F7F1E7")
            add_inline(paragraph, stripped[2:].strip(), size=9.5, color=MUTED)
            continue

        if re.match(r"^[-*]\s+", stripped):
            paragraph = doc.add_paragraph(style="List Bullet")
            paragraph.paragraph_format.space_after = Pt(2)
            add_inline(paragraph, re.sub(r"^[-*]\s+", "", stripped), size=10.5)
            continue

        if re.match(r"^\d+\.\s+", stripped):
            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.left_indent = Pt(20)
            paragraph.paragraph_format.first_line_indent = Pt(-12)
            paragraph.paragraph_format.space_after = Pt(3)
            add_inline(paragraph, stripped, size=10.5)
            continue

        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(5)
        paragraph.paragraph_format.line_spacing = 1.45
        add_inline(paragraph, stripped, size=10.5)


def setup_document(doc):
    section = doc.sections[0]
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.4)
    section.right_margin = Cm(2.4)

    normal = doc.styles["Normal"]
    normal.font.name = CN_FONT
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), CN_FONT)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run("文心 · 高考满分作文智能工坊　|　网安243 付小娅 202401050876　|　第 ")
    set_run_font(run, size=8, color=MUTED)
    add_page_number(footer)
    run2 = footer.add_run(" 页")
    set_run_font(run2, size=8, color=MUTED)


def main():
    doc = Document()
    setup_document(doc)
    add_cover(doc)
    parse_markdown(doc, README.read_text(encoding="utf-8"))
    doc.save(OUTPUT)
    print(f"saved {OUTPUT}")


if __name__ == "__main__":
    main()
