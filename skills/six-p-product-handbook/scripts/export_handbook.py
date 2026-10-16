#!/usr/bin/env python3
"""Validate a 6P interview artifact and export matching Markdown and CJK PDF."""
from datetime import date
from research_appendix import empty_research, research_blocks, validate_research
from export_common import (CONTENT_STATES, UNKNOWN, item, require_text, display,
                           markdown_blocks, build_pdf as render_pdf, export_document, run_cli)
from offer_design import empty_offer, validate_offer, offer_blocks, TITLE as OFFER_TITLE

SECTIONS = [
    ('People', '你要服務誰？', ['身分背景', '目前階段', '服務範圍'], '我主要服務＿＿＿，他們目前處於＿＿＿階段。'),
    ('Problem', '他們卡在哪裡？', ['具體困境', '實際影響', '過去嘗試'], '他們在＿＿＿時遇到＿＿＿，因此造成＿＿＿。'),
    ('Promise', '你能幫他達成什麼？', ['起點', '終點', '達成標準'], '協助＿＿＿，從＿＿＿走到＿＿＿。'),
    ('Plan', '如何帶他走到目標？', ['階段順序', '關鍵行動', '里程碑'], '先完成＿＿＿，再進行＿＿＿，最後達成＿＿＿。'),
    ('Product', '他會拿到什麼？', ['交付項目', '交付方式', '交付範圍'], '這個方案包含＿＿＿，透過＿＿＿提供，服務期間為＿＿＿。'),
    ('Price', '怎麼收費與設計方案？', ['方案價格', '方案差異', '付款方式'], '＿＿＿方案，費用為＿＿＿，包含＿＿＿，付款方式為＿＿＿。'),
]
DOC_STATES = {'草稿', '待補版', '確認版', '示範'}


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
        'offer': empty_offer(),
    }


def all_items(data):
    for section in data['sections']:
        yield section['summary']
        yield from section['fields']
        yield section['statement']


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('手冊資料必須是物件')
    validate_research(data.get('research'))
    if data.get('schema_version') != 1:
        raise ValueError('schema_version 必須為 1')
    meta = data.get('meta', {})
    if not isinstance(meta, dict):
        raise ValueError('meta 必須是物件')
    for name in ['title', 'owner', 'industry', 'mode', 'status', 'version', 'date']:
        require_text(meta.get(name), 'meta.' + name)
    date.fromisoformat(meta['date'])
    if meta['status'] not in DOC_STATES:
        raise ValueError('無效文件狀態')
    if 'offer' in data:
        validate_offer(data['offer'], confirmed=meta['status'] == '確認版')
    sections = data.get('sections', [])
    if not isinstance(sections, list) or not all(isinstance(s, dict) for s in sections) or [s.get('key') for s in sections] != [s[0] for s in SECTIONS]:
        raise ValueError('六個 P 必須齊全並依 People/Problem/Promise/Plan/Product/Price 排序')
    for section, (_, _, labels, _) in zip(sections, SECTIONS):
        fields = section.get('fields', [])
        if not isinstance(fields, list) or not all(isinstance(f, dict) for f in fields) or [f.get('label') for f in fields] != labels:
            raise ValueError(f"{section['key']} 的三個欄位名稱或順序有誤")
        for content in [section.get('summary'), *fields, section.get('statement')]:
            if not isinstance(content, dict):
                raise ValueError(f"{section['key']} 缺少摘要、欄位或填寫句")
            require_text(content.get('text'), section['key'])
            if not isinstance(content.get('status'), str) or content['status'] not in CONTENT_STATES:
                raise ValueError(f"{section['key']} 有無效內容狀態")
            if UNKNOWN.search(content['text']) and content['status'] in {'已確認', '不適用'}:
                raise ValueError(f"{section['key']} 包含未知標記卻標為 {content['status']}")
    questions = data.get('open_questions')
    if not isinstance(questions, list):
        raise ValueError('open_questions 必須為陣列，沒有時填 []')
    for question in questions:
        if not isinstance(question, dict):
            raise ValueError('open_questions 項目必須是物件')
        for name in ['question', 'why', 'next_action']:
            require_text(question.get(name), 'open_questions.' + name)
    if meta['status'] == '確認版':
        if questions or any(i['status'] in {'待補資料', '待驗證'} for i in all_items(data)):
            raise ValueError('仍有待補、待驗證或未決問題，不可輸出確認版')
        if any(UNKNOWN.search(meta[k]) or '[方案名稱]' in meta[k] for k in ['title', 'owner', 'industry', 'mode', 'version', 'date']):
            raise ValueError('確認版基本資料仍未填完')



def handbook_blocks(data):
    meta = data['meta']
    blocks = []
    def add(kind, value=''):
        blocks.append((kind, value, None))
    add('title', meta['title'])
    add('h1', '6P 產品手冊')
    add('small', f"{meta['status']}　|　{meta['version']}　|　{meta['date']}")
    add('small', f"服務者：{meta['owner']}\n行業：{meta['industry']}\n模式：{meta['mode']}")
    add('rule')
    add('h2', '6P 總覽')
    for section in data['sections']:
        add('h2', section['key'])
        add('body', display(section['summary']))
    for section, (key, question, _, _) in zip(data['sections'], SECTIONS):
        add('break')
        add('h1', key + '：' + question)
        add('body', display(section['summary']))
        add('rule')
        for field in section['fields']:
            add('h2', field['label'])
            add('body', display(field))
        add('h2', '填寫句')
        add('body', display(section['statement']))
    blocks.extend(offer_blocks(data.get('offer')))
    add('break')
    add('h1', '待確認事項與下一步')
    for n, question in enumerate(data['open_questions'], 1):
        add('h2', f"{n}. {question['question']}")
        add('body', '影響：' + question['why'])
        add('body', '下一步：' + question['next_action'])
    if not data['open_questions']:
        add('body', '目前無待確認事項。')
    add('small', '文件狀態：' + meta['status'])
    add('small', '「已確認」指方案內容已獲確認，不代表市場成果已經驗證。')
    blocks.extend(research_blocks(data.get('research')))
    return blocks


def markdown(data):
    return markdown_blocks(handbook_blocks(data))


def build_pdf(data, destination):
    meta = data['meta']
    render_pdf(handbook_blocks(data), destination, title=meta['title'] + '｜6P 產品手冊',
               author=meta['owner'], label='6P 產品手冊', status=meta['status'])


def export(data, out_dir):
    validate(data)
    meta = data['meta']
    offer = data.get('offer')
    report = {'sections': 6, 'fields': 18,
              'research_status': (data.get('research') or {}).get('status', '舊版未附研究'),
              'competitor_count': len((data.get('research') or {}).get('competitors', [])),
              'offer_readback': {'status': 'passed' if offer is not None else 'not_present',
                                 'title': OFFER_TITLE if offer is not None else None,
                                 'stack_items': [entry['item'] for entry in offer['stack']] if offer else []}}
    return export_document(handbook_blocks(data), out_dir, basename='產品手冊',
                           title=meta['title'] + '｜6P 產品手冊', author=meta['owner'],
                           status=meta['status'], report=report)


def main():
    run_cli(skeleton, export, __doc__)


if __name__ == '__main__':
    main()
