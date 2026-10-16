#!/usr/bin/env python3
"""Validate market research and export a matching Traditional Chinese report."""
from datetime import date
from export_common import (require_text, markdown_blocks, build_pdf as render_pdf,
                           export_document, run_cli, table)
from research_appendix import PS, validate_competitors, validate_sources

CRITERIA = ('痛點大', '買得起', '容易找到', '市場在成長')
STATES = {'草稿', '部分完成', '完成', '示範'}
DECISION_FIELDS = {'niche': '選定的利基市場', 'reason': '選擇理由',
                   'rejected_reasons': '放棄其他候選的理由', 'validation': '下一步驗證'}


def placeholder(value):
    # A reason can legitimately discuss uncertainty. Reject unfinished answers,
    # not a filled decision such as "放棄此市場，因付費意願仍待驗證".
    return value.strip().strip('[]') in {'待補資料', '待驗證', '待確認', '未知', '尚未選定', 'TODO', 'TBD'} or value.lstrip().startswith(('[待補', '[TODO]', '[TBD]', '＿＿'))


def candidate_skeleton(number):
    return {'id': f'N{number}', 'name': f'[待補資料] 候選利基 {number}',
            'audience_quotes': [],
            'scores': {key: {'score': None, 'reason': '未知，尚未取得可評分的證據', 'sources': []}
                       for key in CRITERIA},
            'competitors': [], 'saturation': '未知', 'advantage': '[待補資料]',
            'risks': '[待補資料]', 'gap': '[待補資料]'}


def skeleton():
    return {'schema_version': 1,
            'meta': {'background': '[待補資料]', 'region': '[待補資料]', 'date': date.today().isoformat(),
                     'provider': '尚未執行', 'status': '草稿'},
            'candidates': [candidate_skeleton(1), candidate_skeleton(2)],
            'recommendation': '[待驗證] 尚無足夠證據提出市場建議，由學員選定。',
            'decision': {'candidate_id': None, **{key: '[待補資料]' for key in DECISION_FIELDS}},
            'limitations': '尚未進行研究；需要訪談、公開來源與學員選擇。'}


def validate(data):
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('市場報告必須是物件，schema_version 必須為 1')
    meta = data.get('meta')
    if not isinstance(meta, dict):
        raise ValueError('meta 必須是物件')
    for key in ['background', 'region', 'date', 'provider', 'status']:
        require_text(meta.get(key), 'meta.' + key)
    date.fromisoformat(meta['date'])
    if meta['status'] not in STATES:
        raise ValueError('meta.status 只能是 草稿／部分完成／完成／示範')
    require_text(data.get('limitations'), 'limitations')
    if 'recommendation' in data:
        require_text(data['recommendation'], 'recommendation')
    candidates = data.get('candidates')
    if not isinstance(candidates, list):
        raise ValueError('candidates 必須是陣列')
    ids, names = set(), set()
    for n, candidate in enumerate(candidates):
        label = f'candidates[{n}]'
        if not isinstance(candidate, dict):
            raise ValueError(label + ' 必須是物件')
        for key in ['id', 'name', 'saturation', 'advantage', 'risks', 'gap']:
            require_text(candidate.get(key), label + '.' + key)
        canonical = ''.join(candidate['name'].casefold().split())
        if candidate['id'] in ids or canonical in names:
            raise ValueError('候選利基 ID 或名稱重複，不能重複計數')
        ids.add(candidate['id'])
        names.add(canonical)
        if candidate['saturation'] not in {'多', '中', '少', '未知'}:
            raise ValueError(label + '.saturation 只能是 多／中／少／未知')
        quotes = candidate.get('audience_quotes')
        if not isinstance(quotes, list):
            raise ValueError(label + '.audience_quotes 必須是陣列')
        for quote in quotes:
            if not isinstance(quote, dict):
                raise ValueError('客群原話摘要必須是含 text、sources 的物件')
            require_text(quote.get('text'), label + '.audience_quotes.text')
            validate_sources(quote.get('sources'), label + '.audience_quotes.sources', required=True)
        scores = candidate.get('scores')
        if not isinstance(scores, dict) or set(scores) != set(CRITERIA):
            raise ValueError(label + '.scores 必須含 痛點大／買得起／容易找到／市場在成長')
        for key in CRITERIA:
            score = scores[key]
            if not isinstance(score, dict):
                raise ValueError(label + '.scores.' + key + ' 必須含 score、reason、sources')
            value = score.get('score')
            if 'score' not in score or (value is not None and (type(value) is not int or not 1 <= value <= 5)):
                raise ValueError(label + '.scores.' + key + '.score 只能是 1–5 的整數或 null（未知）')
            require_text(score.get('reason'), label + '.scores.' + key + '.reason')
            if value is not None and placeholder(score['reason']):
                raise ValueError(label + '.scores.' + key + ' 缺乏評分理由；證據未知請將 score 設為 null')
            validate_sources(score.get('sources'), label + '.scores.' + key + '.sources', required=value is not None)
        validate_competitors(candidate.get('competitors'))
    decision = data.get('decision')
    if not isinstance(decision, dict) or 'candidate_id' not in decision:
        raise ValueError('decision 必須是物件並含 candidate_id（尚未選定填 null）')
    selected = decision['candidate_id']
    if selected is not None and (not isinstance(selected, str) or selected not in ids):
        raise ValueError('decision.candidate_id 必須對應已列出的候選利基')
    for key in DECISION_FIELDS:
        require_text(decision.get(key), 'decision.' + key)
    if meta['status'] == '完成':
        errors = []
        if len(candidates) < 2:
            errors.append('至少需要 2 個不同候選利基')
        if selected is None:
            errors.append('學員尚未選定利基，請填 decision.candidate_id')
        else:
            competitors = next(c for c in candidates if c['id'] == selected)['competitors']
            if sum(c['verified'] for c in competitors) < 5:
                errors.append('選定的候選至少需要 5 個不同且 verified 為 true 的競品')
        if any(placeholder(decision[key]) for key in DECISION_FIELDS):
            errors.append('decision 的利基、選擇理由、放棄其他候選的理由與下一步驗證都需填完')
        if any(placeholder(meta[key]) for key in ['background', 'region', 'provider']):
            errors.append('基本資料仍有待補或未知')
        if any(placeholder(c['name']) for c in candidates):
            errors.append('候選利基名稱仍有待補或未知')
        if errors:
            raise ValueError('不可標為完成：' + '；'.join(errors) + '。請補齊或改為部分完成並說明限制。')


def score_text(score):
    return '未知' if score['score'] is None else str(score['score']) + '／5'


def market_blocks(data):
    blocks = []
    def add(kind, value=''):
        blocks.append((kind, value, None))
    def sources(entries):
        for source in entries:
            blocks.append(('link', source['title'], source['url']))
            add('small', '查閱日期：' + source['checked_at'] + '｜支持內容：' + source['supports'])
    meta = data['meta']
    add('title', '競品分析報告')
    add('h1', '基本資料')
    for key, label in [('background', '學員背景摘要'), ('region', '地區與語言'), ('date', '日期'),
                       ('provider', '研究工具'), ('status', '狀態')]:
        add('body', label + '：' + meta[key])
    add('small', '選市場四條件參考 Alex Hormozi《$100M Offers》。評分、市場空隙與 AI 建議皆為待驗證判斷；由學員選定市場。')
    if meta['status'] == '示範':
        add('body', '本報告為虛構學員與市場資料的排版示範，來源與價格不代表實際研究。')
    add('h1', '候選利基比較表')
    if data['candidates']:
        # Stack the four scores vertically to keep A4 portrait type legible.
        blocks.append(table(['候選利基／競品飽和度', '四條件評分（待驗證）', '學員優勢／主要風險'],
                            [[c['name'] + '\n飽和度：' + c['saturation'],
                              '\n'.join(key + '：' + score_text(c['scores'][key]) for key in CRITERIA),
                              '優勢：' + c['advantage'] + '\n風險：' + c['risks']] for c in data['candidates']],
                            [1.1, 1.3, 1.6]))
    else:
        add('body', '[待補資料] 尚未提出候選利基。')
    for candidate in data['candidates']:
        add('break')
        add('h1', candidate['id'] + ' ' + candidate['name'])
        add('h2', '客群原話摘要與來源')
        for quote in candidate['audience_quotes']:
            add('body', quote['text'])
            sources(quote['sources'])
        if not candidate['audience_quotes']:
            add('body', '未知：目前沒有附來源的客群原話摘要。')
        add('h2', '競品清單')
        if not candidate['competitors']:
            add('body', '目前沒有可交付的競品資料，請見研究限制。')
        for competitor in candidate['competitors']:
            add('h2', competitor['id'] + ' ' + competitor['name'])
            add('small', competitor['type'] + '｜' + competitor['market'] + '｜' +
                ('已讀一手來源' if competitor['verified'] else '來源待驗證'))
            add('body', '相關理由：' + competitor['relevance'])
            for key in PS:
                add('body', key + '：' + competitor['six_p'][key])
            add('body', '可學習做法：' + competitor['learn'])
            add('body', '不宜照搬與限制：' + competitor['cautions'])
            sources(competitor['sources'])
        add('h2', '四條件評分與理由')
        for key in CRITERIA:
            score = candidate['scores'][key]
            add('body', '[待驗證] ' + key + '：' + score_text(score))
            add('body', '理由：' + score['reason'])
            sources(score['sources'])
        add('h2', '市場空隙')
        add('body', '[待驗證] ' + candidate['gap'])
    add('break')
    add('h1', '選定的利基市場與下一步')
    if data.get('recommendation'):
        add('body', '[待驗證] AI 建議：' + data['recommendation'])
    decision = data['decision']
    selected = next((c['name'] for c in data['candidates'] if c['id'] == decision['candidate_id']), '尚未選定')
    add('body', '學員選定候選：' + selected)
    for key, label in DECISION_FIELDS.items():
        add('h2', label)
        add('body', decision[key])
    add('h1', '研究限制')
    add('body', data['limitations'])
    return blocks


def markdown(data):
    return markdown_blocks(market_blocks(data))


def build_pdf(data, destination):
    render_pdf(market_blocks(data), destination, title='競品分析報告', author='',
               label='競品分析報告', status=data['meta']['status'])


def export(data, out_dir):
    validate(data)
    selected = next((c for c in data['candidates'] if c['id'] == data['decision']['candidate_id']), None)
    report = {'candidate_count': len(data['candidates']),
              'competitor_count': sum(len(c['competitors']) for c in data['candidates']),
              'selected_candidate_id': data['decision']['candidate_id'],
              'selected_competitor_count': len(selected['competitors']) if selected else 0,
              'selected_verified_competitor_count': sum(c['verified'] for c in selected['competitors']) if selected else 0}
    return export_document(market_blocks(data), out_dir, basename='競品分析報告', title='競品分析報告',
                           author='', status=data['meta']['status'], report=report)


def main():
    run_cli(skeleton, export, __doc__)


if __name__ == '__main__':
    main()
