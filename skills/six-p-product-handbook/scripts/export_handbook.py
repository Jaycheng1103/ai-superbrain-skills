#!/usr/bin/env python3
"""Validate a 6P interview artifact and export matching Markdown and CJK PDF."""
import argparse
import hashlib
import json
import re
import tempfile
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr
from research_appendix import empty_research, research_blocks, validate_research

SECTIONS = [
    ('People', '你要服務誰？', ['身分背景', '目前階段', '服務範圍'], '我主要服務＿＿＿，他們目前處於＿＿＿階段。'),
    ('Problem', '他們卡在哪裡？', ['具體困境', '實際影響', '過去嘗試'], '他們在＿＿＿時遇到＿＿＿，因此造成＿＿＿。'),
    ('Promise', '你能幫他達成什麼？', ['起點', '終點', '達成標準'], '協助＿＿＿，從＿＿＿走到＿＿＿。'),
    ('Plan', '如何帶他走到目標？', ['階段順序', '關鍵行動', '里程碑'], '先完成＿＿＿，再進行＿＿＿，最後達成＿＿＿。'),
    ('Product', '他會拿到什麼？', ['交付項目', '交付方式', '交付範圍'], '這個方案包含＿＿＿，透過＿＿＿提供，服務期間為＿＿＿。'),
    ('Price', '怎麼收費與設計方案？', ['方案價格', '方案差異', '付款方式'], '＿＿＿方案，費用為＿＿＿，包含＿＿＿，付款方式為＿＿＿。'),
]
CONTENT_STATES = {'已確認', '待驗證', '待補資料', '不適用'}
DOC_STATES = {'草稿', '待補版', '確認版', '示範'}
UNKNOWN = re.compile(r'待補|待確認|待驗證|待定|尚未確認|未確認|＿＿|_{3,}|\[TODO\]|\[TBD\]', re.I)


def item(text='[待補資料]', status='待補資料'):
    return {'text': text, 'status': status}


def skeleton():
    return {
        'schema_version': 1,
        'meta': {'title': '[方案名稱]', 'owner': '[待補資料]', 'industry': '[待補資料]',
                 'mode': '[待補資料]', 'status': '待補版', 'version': 'v1', 'date': date.today().isoformat()},
        'sections': [{'key': key, 'summary': item(),
                      'fields': [dict(label=label, **item()) for label in labels],
                      'statement': item(statement)} for key, _, labels, statement in SECTIONS],
        'open_questions': [{'question': '尚未進行訪談', 'why': '需要確認服務模式與方案內容',
                            'next_action': '先了解行業、服務模式與最近一次委託情境'}],
        'research': empty_research(),
    }


def require_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} 不可為空；未知請明寫 [待補資料]')


def all_items(data):
    for section in data['sections']:
        yield section['summary']
        yield from section['fields']
        yield section['statement']


def validate(data):
    validate_research(data.get('research'))
    if data.get('schema_version') != 1:
        raise ValueError('schema_version 必須為 1')
    meta = data.get('meta', {})
    for name in ['title', 'owner', 'industry', 'mode', 'status', 'version', 'date']:
        require_text(meta.get(name), 'meta.' + name)
    date.fromisoformat(meta['date'])
    if meta['status'] not in DOC_STATES:
        raise ValueError('無效文件狀態')
    sections = data.get('sections', [])
    if not isinstance(sections, list) or [s.get('key') for s in sections] != [s[0] for s in SECTIONS]:
        raise ValueError('六個 P 必須齊全並依 People/Problem/Promise/Plan/Product/Price 排序')
    for section, (_, _, labels, _) in zip(sections, SECTIONS):
        fields = section.get('fields', [])
        if [f.get('label') for f in fields] != labels:
            raise ValueError(f"{section['key']} 的三個欄位名稱或順序有誤")
        for content in [section.get('summary'), *fields, section.get('statement')]:
            if not isinstance(content, dict):
                raise ValueError(f"{section['key']} 缺少摘要、欄位或填寫句")
            require_text(content.get('text'), section['key'])
            if content.get('status') not in CONTENT_STATES:
                raise ValueError(f"{section['key']} 有無效內容狀態")
            if UNKNOWN.search(content['text']) and content['status'] in {'已確認', '不適用'}:
                raise ValueError(f"{section['key']} 包含未知標記卻標為 {content['status']}")
    questions = data.get('open_questions')
    if not isinstance(questions, list):
        raise ValueError('open_questions 必須為陣列，沒有時填 []')
    for question in questions:
        for name in ['question', 'why', 'next_action']:
            require_text(question.get(name), 'open_questions.' + name)
    if meta['status'] == '確認版':
        if questions or any(i['status'] in {'待補資料', '待驗證'} for i in all_items(data)):
            raise ValueError('仍有待補、待驗證或未決問題，不可輸出確認版')
        if any(UNKNOWN.search(v) or '[方案名稱]' in v for v in meta.values()):
            raise ValueError('確認版基本資料仍未填完')


def display(content):
    if content['status'] == '已確認':
        return content['text']
    marker = '[' + content['status'] + ']'
    return content['text'] if content['text'].startswith(marker) else marker + ' ' + content['text']


def markdown(data):
    meta = data['meta']
    lines = [f"# {meta['title']}｜6P 產品手冊", '',
             f"服務者：{meta['owner']}　行業：{meta['industry']}　模式：{meta['mode']}", '',
             f"版本：{meta['version']}　日期：{meta['date']}　狀態：{meta['status']}", '', '## 6P 總覽', '']
    for section in data['sections']:
        lines.extend([f"**{section['key']}**：{display(section['summary'])}", ''])
    for section, (key, question, _, _) in zip(data['sections'], SECTIONS):
        lines.extend([f'## {key}：{question}', '', display(section['summary']), ''])
        for field in section['fields']:
            lines.extend(['### ' + field['label'], '', display(field), ''])
        lines.extend(['### 填寫句', '', display(section['statement']), ''])
    lines.extend(['## 待確認事項與下一步', ''])
    for n, q in enumerate(data['open_questions'], 1):
        lines.extend([f"### {n}. {q['question']}", '', '影響：' + q['why'], '', '下一步：' + q['next_action'], ''])
    if not data['open_questions']:
        lines.append('目前無待確認事項。')
    for kind, value, url in research_blocks(data.get('research')):
        if kind == 'break':
            lines.append('')
        elif kind == 'link':
            lines.extend([f'[{value}](<{url}>)', ''])
        else:
            prefix = {'h1': '## ', 'h2': '### '}.get(kind, '')
            lines.extend([prefix + value, ''])
    return '\n'.join(lines) + '\n'


def build_pdf(data, destination):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
    font_dir = Path(__file__).resolve().parents[1] / 'assets' / 'fonts'
    for name, filename in [('SixP', 'NotoSansTC-Regular.ttf'), ('SixPBold', 'NotoSansTC-Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    full_text = markdown(data) + '摘要填寫句影響下一步產品手冊'
    coverage = set(pdfmetrics.getFont('SixP').face.charToGlyph)
    missing = sorted({c for c in full_text if not c.isspace() and ord(c) not in coverage})
    if missing:
        raise ValueError('字型不支援以下字元，請改用可顯示文字或適當字型：' + ''.join(missing))
    accent = colors.HexColor('#DA571C')
    styles = {
        'title': ParagraphStyle('title', fontName='SixPBold', fontSize=25, leading=36, spaceAfter=16, wordWrap='CJK'),
        'h1': ParagraphStyle('h1', fontName='SixPBold', fontSize=22, leading=31, spaceAfter=15, wordWrap='CJK', keepWithNext=True),
        'h2': ParagraphStyle('h2', fontName='SixPBold', fontSize=13, leading=20, spaceBefore=17, spaceAfter=6, textColor=accent, keepWithNext=True, wordWrap='CJK'),
        'body': ParagraphStyle('body', fontName='SixP', fontSize=11, leading=19, spaceAfter=9, wordWrap='CJK', alignment=TA_LEFT, splitLongWords=True),
        'small': ParagraphStyle('small', fontName='SixP', fontSize=9, leading=15, spaceAfter=6, wordWrap='CJK'),
    }
    story = []

    def p(text, kind='body'):
        # Escape all learner content; never evaluate markup, URLs, or commands.
        story.append(Paragraph(escape(text).replace('\n', '<br/>'), styles[kind]))

    def rule():
        story.append(HRFlowable(width='100%', color=colors.HexColor('#D7D9DB'), thickness=0.6))

    meta = data['meta']
    p(meta['title'], 'title')
    p('6P 產品手冊', 'h1')
    p(f"{meta['status']}　|　{meta['version']}　|　{meta['date']}", 'small')
    p(f"服務者：{meta['owner']}\n行業：{meta['industry']}\n模式：{meta['mode']}", 'small')
    rule()
    p('6P 總覽', 'h2')
    for section in data['sections']:
        p(section['key'], 'h2')
        p(display(section['summary']))
    for section, (key, question, _, _) in zip(data['sections'], SECTIONS):
        story.append(PageBreak())
        p(key, 'title')
        p(question, 'h1')
        p(display(section['summary']))
        rule()
        for field in section['fields']:
            p(field['label'], 'h2')
            p(display(field))
        p('填寫句', 'h2')
        p(display(section['statement']))
    story.append(PageBreak())
    p('待確認事項與下一步', 'h1')
    if data['open_questions']:
        for n, question in enumerate(data['open_questions'], 1):
            p(f"{n}. {question['question']}", 'h2')
            p('影響：' + question['why'])
            p('下一步：' + question['next_action'])
    else:
        p('目前無待確認事項。')
    p('文件狀態：' + meta['status'], 'small')
    p('「已確認」指方案內容已獲確認，不代表市場成果已經驗證。', 'small')
    for kind, value, url in research_blocks(data.get('research')):
        if kind == 'break':
            story.append(PageBreak())
        elif kind == 'link':
            markup = '<link href=' + quoteattr(url) + ' color="#2255AA">' + escape(value) + '</link>'
            story.append(Paragraph(markup, styles['small']))
        else:
            p(value, kind)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#D7D9DB'))
        canvas.line(44, 39, A4[0] - 44, 39)
        canvas.setFont('SixP', 8)
        canvas.drawString(44, 25, '6P 產品手冊　|　' + meta['status'])
        canvas.drawRightString(A4[0] - 44, 25, str(doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(str(destination), pagesize=A4, rightMargin=44, leftMargin=44,
                            topMargin=42, bottomMargin=54, title=meta['title'] + '｜6P 產品手冊', author=meta['owner'])
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def export(data, out_dir):
    from pypdf import PdfReader
    validate(data)
    out_dir.mkdir(parents=True, exist_ok=True)
    names = ['產品手冊.md', '產品手冊.pdf', 'export-report.json']
    if any((out_dir / name).exists() for name in names):
        raise FileExistsError('輸出已存在，請選擇新版本資料夾；不覆寫')
    with tempfile.TemporaryDirectory(prefix='six-p-') as temp:
        temp_dir = Path(temp)
        (temp_dir / names[0]).write_text(markdown(data), encoding='utf-8')
        build_pdf(data, temp_dir / names[1])
        reader = PdfReader(temp_dir / names[1])
        normalize = lambda t: re.sub(r'\s+', '', t)
        # Footer text interleaves with paragraphs crossing page boundaries.
        # Remove our known footer prefix so continued paragraphs stay contiguous.
        body_parts = []
        for page_number, page in enumerate(reader.pages, 1):
            text = normalize(page.extract_text() or '')
            prefix = normalize('6P 產品手冊 | ' + data['meta']['status'] + str(page_number))
            if not text.startswith(prefix):
                raise ValueError('PDF 頁尾讀回格式異常，請檢查輸出')
            body_parts.append(text[len(prefix):])
        extracted = ''.join(body_parts)
        expected = [data['meta'][k] for k in data['meta']]
        expected += [display(i) for i in all_items(data)]
        expected += [v for q in data['open_questions'] for v in q.values()]
        expected += [s[0] for s in SECTIONS] + [label for s in SECTIONS for label in s[2]]
        blocks = research_blocks(data.get('research'))
        expected += [value for kind, value, _ in blocks if kind != 'break']
        missing = [text for text in expected if normalize(text) not in extracted]
        if missing:
            raise ValueError(f'PDF 讀回有 {len(missing)} 項文字未通過核對；請檢查排版，未輸出成品')
        wanted_links = {url for kind, _, url in blocks if kind == 'link'}
        actual_links = set()
        for page in reader.pages:
            for annotation in page.get('/Annots', []):
                action = annotation.get_object().get('/A')
                if action and action.get('/URI'):
                    actual_links.add(str(action['/URI']))
        if not wanted_links.issubset(actual_links):
            raise ValueError('PDF 缺少可點擊的競品來源連結')
        pdf_bytes = (temp_dir / names[1]).read_bytes()
        report = {'schema_version': 1, 'document_status': data['meta']['status'],
                  'pages': len(reader.pages), 'sections': 6, 'fields': 18,
                  'text_readback': 'passed', 'visual_review': 'required',
                  'research_status': (data.get('research') or {}).get('status', '舊版未附研究'),
                  'competitor_count': len((data.get('research') or {}).get('competitors', [])),
                  'source_links': len(wanted_links), 'link_annotations': 'passed',
                  'pdf_sha256': hashlib.sha256(pdf_bytes).hexdigest(), 'pdf_bytes': len(pdf_bytes)}
        (temp_dir / names[2]).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        for name in names:
            with (out_dir / name).open('xb') as target:
                target.write((temp_dir / name).read_bytes())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--init', type=Path, help='建立新的完整訪談資料骨架')
    group.add_argument('--input', type=Path, help='填寫完成的 manual.json')
    parser.add_argument('--out-dir', type=Path, help='新版本輸出資料夾')
    args = parser.parse_args()
    if args.init:
        args.init.parent.mkdir(parents=True, exist_ok=True)
        with args.init.open('x', encoding='utf-8') as target:
            json.dump(skeleton(), target, ensure_ascii=False, indent=2)
            target.write('\n')
        print(args.init)
        return
    if not args.out_dir:
        parser.error('--input 必須搭配 --out-dir')
    try:
        data = json.loads(args.input.read_text(encoding='utf-8'))
        print(json.dumps(export(data, args.out_dir), ensure_ascii=False))
    except (ValueError, KeyError, TypeError, FileExistsError) as exc:
        parser.exit(1, '匯出失敗：' + str(exc) + '\n')


if __name__ == '__main__':
    main()
