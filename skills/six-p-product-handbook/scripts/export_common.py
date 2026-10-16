"""Shared, offline Markdown/PDF layout, validation and readback for 6P exports."""
import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

CONTENT_STATES = {'已確認', '待驗證', '待補資料', '不適用'}
UNKNOWN = re.compile(r'待補|待確認|待驗證|待定|尚未確認|未確認|未知|＿＿|_{3,}|\[TODO\]|\[TBD\]', re.I)
PAGE_MARGIN = 44
FRAME_PADDING = 6
CELL_PADDING = 7
CELL_FONT_SIZE = 9.5


def item(text='[待補資料]', status='待補資料'):
    return {'text': text, 'status': status}


def require_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} 不可為空；未知請明寫 [待補資料]')


def validate_item(content, label, confirmed=False):
    if not isinstance(content, dict):
        raise ValueError(f'{label} 必須是含 text、status 的物件')
    require_text(content.get('text'), label + '.text')
    if not isinstance(content.get('status'), str) or content['status'] not in CONTENT_STATES:
        raise ValueError(f'{label}.status 只能是 已確認／待驗證／待補資料／不適用')
    if UNKNOWN.search(content['text']) and content['status'] in {'已確認', '不適用'}:
        raise ValueError(f'{label} 包含未知標記卻標為 {content["status"]}')
    if confirmed and content['status'] in {'待補資料', '待驗證'}:
        raise ValueError(f'確認版不可含待補資料或待驗證：{label}')


def display(content, mark_confirmed=False):
    if content['status'] == '已確認' and not mark_confirmed:
        return content['text']
    marker = '[' + content['status'] + ']'
    return content['text'] if content['text'].startswith(marker) else marker + ' ' + content['text']


def table(headers, rows, widths):
    """A table block; widths are relative, all cells use wrapping paragraphs."""
    return ('table', {'headers': headers, 'rows': rows, 'widths': widths}, None)


def table_widths(weights):
    from reportlab.lib.pagesizes import A4
    width = A4[0] - 2 * (PAGE_MARGIN + FRAME_PADDING)
    return [width * weight / sum(weights) for weight in weights]


def block_texts(blocks):
    for kind, value, _ in blocks:
        if kind == 'table':
            yield from value['headers']
            for row in value['rows']:
                yield from row
        elif kind not in {'break', 'rule'}:
            yield value


def markdown_blocks(blocks):
    lines = []
    def cell(value):
        return value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('|', '&#124;').replace('\n', '<br>')
    for kind, value, url in blocks:
        if kind == 'break':
            continue
        if kind == 'rule':
            lines.extend(['---', ''])
        elif kind == 'table':
            lines.append('| ' + ' | '.join(cell(v) for v in value['headers']) + ' |')
            lines.append('| ' + ' | '.join('---' for _ in value['headers']) + ' |')
            for row in value['rows']:
                lines.append('| ' + ' | '.join(cell(v) for v in row) + ' |')
            lines.append('')
        elif kind == 'link':
            label = value.replace('[', '\\[').replace(']', '\\]')
            lines.extend([f'[{label}](<{url}>)', ''])
        else:
            lines.extend([{'title': '# ', 'h1': '## ', 'h2': '### '}.get(kind, '') + value, ''])
    return '\n'.join(lines) + '\n'


def build_pdf(blocks, destination, *, title, author, label, status):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, HRFlowable, LongTable, TableStyle

    font_dir = Path(__file__).resolve().parents[1] / 'assets' / 'fonts'
    for name, filename in [('SixP', 'NotoSansTC-Regular.ttf'), ('SixPBold', 'NotoSansTC-Bold.ttf')]:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    coverage = set(pdfmetrics.getFont('SixP').face.charToGlyph)
    full_text = ''.join(block_texts(blocks)) + label + status
    missing = sorted({c for c in full_text if not c.isspace() and ord(c) not in coverage})
    if missing:
        raise ValueError('字型不支援以下字元，請改用可顯示文字或適當字型：' + ''.join(missing))
    accent = colors.HexColor('#DA571C')
    styles = {
        'title': ParagraphStyle('title', fontName='SixPBold', fontSize=25, leading=36, spaceAfter=16, wordWrap='CJK', keepWithNext=True),
        'h1': ParagraphStyle('h1', fontName='SixPBold', fontSize=22, leading=31, spaceAfter=15, wordWrap='CJK', keepWithNext=True),
        'h2': ParagraphStyle('h2', fontName='SixPBold', fontSize=13, leading=20, spaceBefore=17, spaceAfter=6, textColor=accent, keepWithNext=True, wordWrap='CJK'),
        'body': ParagraphStyle('body', fontName='SixP', fontSize=11, leading=19, spaceAfter=9, wordWrap='CJK', splitLongWords=True),
        'small': ParagraphStyle('small', fontName='SixP', fontSize=9, leading=15, spaceAfter=6, wordWrap='CJK'),
        'cell': ParagraphStyle('cell', fontName='SixP', fontSize=CELL_FONT_SIZE, leading=16, wordWrap='CJK', splitLongWords=True),
        'header': ParagraphStyle('header', fontName='SixPBold', fontSize=CELL_FONT_SIZE, leading=16, wordWrap='CJK'),
    }
    def paragraph(value, kind):
        return Paragraph(escape(value).replace('\n', '<br/>'), styles[kind])
    story = []
    for kind, value, url in blocks:
        if kind == 'break':
            story.append(PageBreak())
        elif kind == 'rule':
            story.append(HRFlowable(width='100%', color=colors.HexColor('#D7D9DB'), thickness=0.6))
        elif kind == 'link':
            story.append(Paragraph('<link href=' + quoteattr(url) + ' color="#2255AA">' + escape(value) + '</link>', styles['small']))
        elif kind == 'table':
            rows = [[paragraph(v, 'header') for v in value['headers']]]
            rows.extend([paragraph(v, 'cell') for v in row] for row in value['rows'])
            grid = LongTable(rows, colWidths=table_widths(value['widths']),
                             repeatRows=1, splitByRow=1, splitInRow=1, hAlign='LEFT', spaceAfter=12)
            grid.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F7EEE8')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAFAFA')]),
                ('LINEBELOW', (0, 0), (-1, 0), 0.7, accent),
                ('LINEBELOW', (0, 1), (-1, -1), 0.3, colors.HexColor('#D7D9DB')),
                ('LEFTPADDING', (0, 0), (-1, -1), CELL_PADDING), ('RIGHTPADDING', (0, 0), (-1, -1), CELL_PADDING),
                ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(grid)
        else:
            story.append(paragraph(value, kind))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#D7D9DB'))
        canvas.line(44, 39, A4[0] - 44, 39)
        canvas.setFont('SixP', 8)
        canvas.drawString(44, 25, label + '　|　' + status)
        canvas.drawRightString(A4[0] - 44, 25, str(doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(str(destination), pagesize=A4, rightMargin=PAGE_MARGIN, leftMargin=PAGE_MARGIN,
                            topMargin=42, bottomMargin=54, title=title, author=author)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def readback(pdf_path, blocks, *, label, status):
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    normalize = lambda t: re.sub(r'\s+', '', t)
    body_parts = []
    column_parts = {}
    def collect_cells(text, cm, tm, font, size):
        # Reading a split row in page order interleaves other columns and repeated
        # headers. Reassemble table paragraphs by their actual PDF column origin.
        if size == CELL_FONT_SIZE and font and 'NotoSansTC-Regular' in str(font.get('/BaseFont')):
            x = round(tm[4] * cm[0] + tm[5] * cm[2] + cm[4], 1)
            column_parts.setdefault(x, []).append(text)
    for page_number, page in enumerate(reader.pages, 1):
        text = normalize(page.extract_text(visitor_text=collect_cells) or '')
        prefix = normalize(label + ' | ' + status + str(page_number))
        if not text.startswith(prefix):
            raise ValueError('PDF 頁尾讀回格式異常，請檢查輸出')
        body_parts.append(text[len(prefix):])
    extracted = ''.join(body_parts)
    expected = list(block_texts(blocks))
    missing = []
    columns = {x: normalize(''.join(parts)) for x, parts in column_parts.items()}
    for kind, value, _ in blocks:
        if kind == 'table':
            missing.extend(t for t in value['headers'] if normalize(t) not in extracted)
            x = PAGE_MARGIN + FRAME_PADDING + CELL_PADDING
            for index, width in enumerate(table_widths(value['widths'])):
                actual = columns.get(round(x, 1), '')
                missing.extend(row[index] for row in value['rows'] if normalize(row[index]) not in actual)
                x += width
        elif kind not in {'break', 'rule'} and normalize(value) not in extracted:
            missing.append(value)
    if missing:
        raise ValueError(f'PDF 讀回有 {len(missing)} 項文字未通過核對；請檢查排版，未輸出成品：' + repr(missing[:3]))
    wanted_links = {url for kind, _, url in blocks if kind == 'link'}
    actual_links = set()
    for page in reader.pages:
        for annotation in page.get('/Annots', []):
            action = annotation.get_object().get('/A')
            if action and action.get('/URI'):
                actual_links.add(str(action['/URI']))
    if not wanted_links.issubset(actual_links):
        raise ValueError('PDF 缺少可點擊的來源連結')
    pdf_bytes = pdf_path.read_bytes()
    return {'pages': len(reader.pages), 'text_readback': 'passed', 'checked_texts': len(expected),
            'visual_review': 'required', 'source_links': len(wanted_links), 'link_annotations': 'passed',
            'pdf_sha256': hashlib.sha256(pdf_bytes).hexdigest(), 'pdf_bytes': len(pdf_bytes)}


def export_document(blocks, out_dir, *, basename, title, author, status, report):
    out_dir = Path(out_dir)
    if out_dir.exists():
        raise FileExistsError('輸出資料夾已存在，請選擇新版本資料夾；不覆寫')
    with tempfile.TemporaryDirectory(prefix='six-p-') as temp:
        temp_dir = Path(temp)
        names = [basename + '.md', basename + '.pdf', 'export-report.json']
        (temp_dir / names[0]).write_text(markdown_blocks(blocks), encoding='utf-8')
        label = '6P 產品手冊' if basename == '產品手冊' else basename
        build_pdf(blocks, temp_dir / names[1], title=title, author=author, label=label, status=status)
        report = dict(report, schema_version=1, document_status=status,
                      **readback(temp_dir / names[1], blocks, label=label, status=status))
        (temp_dir / names[2]).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        out_dir.mkdir(parents=True, exist_ok=False)
        for name in names:
            with (out_dir / name).open('xb') as target:
                target.write((temp_dir / name).read_bytes())
    return report


def run_cli(skeleton, exporter, description):
    parser = argparse.ArgumentParser(description=description)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--init', type=Path, help='建立新的完整資料骨架')
    group.add_argument('--input', type=Path, help='填寫完成的 JSON')
    parser.add_argument('--out-dir', type=Path, help='尚不存在的新版本輸出資料夾')
    args = parser.parse_args()
    if args.input and not args.out_dir:
        parser.error('--input 必須搭配 --out-dir')
    try:
        if args.init:
            args.init.parent.mkdir(parents=True, exist_ok=True)
            with args.init.open('x', encoding='utf-8') as target:
                json.dump(skeleton(), target, ensure_ascii=False, indent=2)
                target.write('\n')
            print(args.init)
        else:
            data = json.loads(args.input.read_text(encoding='utf-8'))
            print(json.dumps(exporter(data, args.out_dir), ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(1, '匯出失敗：' + str(exc) + '\n')
