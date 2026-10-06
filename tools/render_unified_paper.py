"""Render the one active TGI Markdown article as an A4 PDF."""
from pathlib import Path
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'paper/technical/TGI_TOPOLOGICAL_GEOMETRIC_INTELLIGENCE.md'
OUTPUT = ROOT / 'paper/technical/TGI_TOPOLOGICAL_GEOMETRIC_INTELLIGENCE.pdf'

FONT_SETS = (
    (Path('C:/Windows/Fonts/arial.ttf'),
     Path('C:/Windows/Fonts/arialbd.ttf'),
     Path('C:/Windows/Fonts/ariali.ttf')),
    (Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
     Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
     Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf')),
)
font_files = next((fonts for fonts in FONT_SETS if all(path.is_file() for path in fonts)), None)
if font_files is None:
    raise RuntimeError('Arial or DejaVu Sans TrueType fonts are required')
pdfmetrics.registerFont(TTFont('Article', str(font_files[0])))
pdfmetrics.registerFont(TTFont('ArticleBold', str(font_files[1])))
pdfmetrics.registerFont(TTFont('ArticleItalic', str(font_files[2])))
pdfmetrics.registerFontFamily('Article', normal='Article', bold='ArticleBold',
                              italic='ArticleItalic', boldItalic='ArticleBold')

STYLES = {
    'title': ParagraphStyle('title', fontName='ArticleBold', fontSize=17.5,
                            leading=21, alignment=TA_CENTER, spaceAfter=14),
    'author': ParagraphStyle('author', fontName='Article', fontSize=9.5,
                             leading=13, alignment=TA_CENTER, spaceAfter=2),
    'h2': ParagraphStyle('h2', fontName='ArticleBold', fontSize=11.5,
                         leading=14, spaceBefore=14, spaceAfter=7,
                         keepWithNext=True),
    'h3': ParagraphStyle('h3', fontName='ArticleBold', fontSize=10.5,
                         leading=13, spaceBefore=11, spaceAfter=5,
                         keepWithNext=True),
    'h4': ParagraphStyle('h4', fontName='ArticleBold', fontSize=9.6,
                         leading=12, spaceBefore=9, spaceAfter=4,
                         keepWithNext=True),
    'body': ParagraphStyle('body', fontName='Article', fontSize=9.0,
                           leading=12.7, alignment=TA_JUSTIFY, spaceAfter=6.5),
    'reference': ParagraphStyle('reference', fontName='Article', fontSize=8.7,
                                leading=11.5, alignment=TA_LEFT, spaceAfter=5),
    'cell': ParagraphStyle('cell', fontName='Article', fontSize=7.1,
                           leading=9, alignment=TA_LEFT),
    'cellhead': ParagraphStyle('cellhead', fontName='ArticleBold', fontSize=7.1,
                               leading=9, alignment=TA_LEFT),
}


def inline(value):
    value = escape(value)
    value = re.sub(r'`([^`]+)`', r'<font name="ArticleItalic">\1</font>', value)
    value = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', value)
    value = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', value)
    value = re.sub(r'(https?://[^\s<]+)', r'<link href="\1" color="#164a76">\1</link>', value)
    return value


def table_flow(lines, available):
    rows = [[cell.strip() for cell in line.strip().strip('|').split('|')]
            for line in lines]
    rows = [row for row in rows if not all(re.fullmatch(r':?-{3,}:?', x)
                                          for x in row)]
    count = max(map(len, rows))
    rows = [row + [''] * (count - len(row)) for row in rows]
    weights = [max(8, min(38, max(len(row[col]) for row in rows)))
               for col in range(count)]
    widths = [available * weight / sum(weights) for weight in weights]
    cells = [[Paragraph(inline(value), STYLES['cellhead' if number == 0 else 'cell'])
              for value in row] for number, row in enumerate(rows)]
    table = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9eef3')),
        ('LINEBELOW', (0, 0), (-1, 0), .65, colors.HexColor('#778b9e')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor('#f7f9fb')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return table


def footer(canvas, document):
    canvas.saveState()
    canvas.setFont('Article', 8)
    canvas.setFillColor(colors.HexColor('#5a6670'))
    canvas.drawString(49, 29, 'TGI: Topological Geometric Intelligence')
    canvas.drawRightString(A4[0] - 49, 29, str(document.page))
    canvas.restoreState()


def main():
    text = SOURCE.read_text(encoding='utf-8')
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=49,
                            leftMargin=49, topMargin=46, bottomMargin=51,
                            title='TGI: Topological Geometric Intelligence',
                            author='Emylton Leunufna')
    story = []
    lines = text.splitlines()
    cursor = 0
    references = False
    while cursor < len(lines):
        line = lines[cursor].strip()
        if not line:
            cursor += 1
            continue
        if line.startswith('|'):
            block = []
            while cursor < len(lines) and lines[cursor].strip().startswith('|'):
                block.append(lines[cursor]); cursor += 1
            story.append(Spacer(1, 3))
            story.append(table_flow(block, A4[0] - 98))
            story.append(Spacer(1, 8))
            continue
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            heading = line[level:].strip()
            if heading == 'References':
                references = True
            style = 'title' if level == 1 else f'h{min(level, 4)}'
            story.append(Paragraph(inline(heading), STYLES[style]))
            cursor += 1
            continue
        paragraph = [line]
        cursor += 1
        while cursor < len(lines) and lines[cursor].strip() and not lines[cursor].startswith(('#', '|')):
            paragraph.append(lines[cursor].strip()); cursor += 1
        story.append(Paragraph(inline(' '.join(paragraph)),
                               STYLES['reference' if references else
                                      'author' if len(story) < 4 else 'body']))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == '__main__':
    main()
