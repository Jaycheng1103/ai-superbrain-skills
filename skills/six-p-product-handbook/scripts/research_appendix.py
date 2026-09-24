"""Structured competitor evidence and recommendations shared by PDF and Markdown."""
from datetime import date
from urllib.parse import urlsplit

PS = ['People', 'Problem', 'Promise', 'Plan', 'Product', 'Price']
STATES = {'待研究', '未連接', '部分完成', '完成', '略過', '示範'}


def empty_research():
    return {'status': '待研究', 'provider': '尚未執行', 'checked_at': date.today().isoformat(),
            'scope': '依學員原產品手冊確認搜尋範圍', 'limitations': '尚未進行競品搜尋',
            'competitors': [], 'recommendations': []}


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('研究欄位不可空白：' + label)


def validate_research(research):
    if research is None:
        return
    if not isinstance(research, dict):
        raise ValueError('research 必須是物件')
    for key in ['status', 'provider', 'checked_at', 'scope', 'limitations']:
        text(research.get(key), key)
    if research['status'] not in STATES:
        raise ValueError('研究狀態不正確')
    date.fromisoformat(research['checked_at'])
    competitors = research.get('competitors')
    recommendations = research.get('recommendations')
    if not isinstance(competitors, list) or not isinstance(recommendations, list):
        raise ValueError('competitors 與 recommendations 必須為陣列')
    ids, names = set(), set()
    for competitor in competitors:
        for key in ['id', 'name', 'type', 'market', 'relevance', 'learn', 'cautions']:
            text(competitor.get(key), key)
        if competitor['type'] not in {'直接競品', '相鄰參考'}:
            raise ValueError('競品類型須為直接競品或相鄰參考')
        canonical = ''.join(competitor['name'].casefold().split())
        if competitor['id'] in ids or canonical in names:
            raise ValueError('競品 ID 或供應者重複，不能用同一家湊數')
        ids.add(competitor['id']); names.add(canonical)
        if not isinstance(competitor.get('verified'), bool):
            raise ValueError('verified 必須明確表示是否已讀到一手來源')
        if set(competitor.get('six_p', {})) != set(PS):
            raise ValueError('每家競品都須包含六個 P，未知請寫頁面未載明')
        for key, value in competitor['six_p'].items():
            text(value, key)
        sources = competitor.get('sources')
        if not isinstance(sources, list) or not sources:
            raise ValueError('每家競品至少要有一個來源')
        for source in sources:
            for key in ['title', 'url', 'checked_at', 'supports']:
                text(source.get(key), key)
            url = urlsplit(source['url'])
            if url.scheme not in {'http', 'https'} or not url.hostname or url.username or url.password:
                raise ValueError('來源須為不含登入資訊的 HTTP(S) 網址')
            date.fromisoformat(source['checked_at'])
    for recommendation in recommendations:
        for key in ['title', 'related_p', 'observation', 'action', 'validation']:
            text(recommendation.get(key), key)
        if recommendation['related_p'] not in PS:
            raise ValueError('建議須對應一個主要 P')
        references = recommendation.get('evidence_ids')
        if not isinstance(references, list) or not references or any(ref not in ids for ref in references):
            raise ValueError('每項建議須連回實際列出的競品 ID')
    if research['status'] == '完成':
        if len(competitors) < 5 or not all(c['verified'] for c in competitors):
            raise ValueError('研究完成需至少五家不同且已讀到一手來源的相關競品')
        if not recommendations:
            raise ValueError('研究完成需附改善建議，不能只交五家名單')


def research_blocks(research):
    """Return (kind, text, URL or None) for identical content in both outputs."""
    if research is None:
        return []
    blocks = []
    def add(kind, value='', url=None):
        blocks.append((kind, value, url))
    add('break')
    add('h1', '競品研究')
    add('small', f"研究狀態：{research['status']}　搜尋工具：{research['provider']}　查閱日期：{research['checked_at']}")
    add('body', '搜尋範圍：' + research['scope'])
    add('body', '研究限制：' + research['limitations'])
    competitors = research['competitors']
    direct = sum(c['type'] == '直接競品' for c in competitors)
    add('body', f'共 {len(competitors)} 家：直接競品 {direct} 家，相鄰參考 {len(competitors) - direct} 家。')
    for c in competitors:
        add('h2', c['id'] + ' ' + c['name'])
        add('body', c['type'] + '｜' + c['relevance'])
    if not competitors:
        add('body', '目前沒有可交付的競品資料；原產品手冊仍可先使用。')
    for c in competitors:
        add('break')
        add('h1', c['id'] + ' ' + c['name'])
        add('small', c['type'] + '｜' + c['market'] + '｜' + ('已讀一手來源' if c['verified'] else '來源待驗證'))
        add('body', '相關理由：' + c['relevance'])
        for key in PS:
            add('h2', key)
            add('body', c['six_p'][key])
        add('h2', '可以學習')
        add('body', c['learn'])
        add('h2', '不宜照搬與限制')
        add('body', c['cautions'])
        add('h2', '來源與查閱日期')
        for n, source in enumerate(c['sources'], 1):
            add('link', f"{c['id']}-{n} {source['title']}", source['url'])
            add('small', source['checked_at'] + '｜支持內容：' + source['supports'])
    add('break')
    add('h1', '改善建議報告')
    add('body', '以下為根據原手冊與競品資料提出的待驗證建議，尚未改動原方案。')
    for n, rec in enumerate(research['recommendations'], 1):
        add('h2', f"{n}. {rec['title']}（{rec['related_p']}）")
        add('body', '觀察與原手冊缺口：' + rec['observation'])
        add('small', '競品依據：' + '、'.join(rec['evidence_ids']))
        add('body', '[待驗證] 建議行動：' + rec['action'])
        add('body', '下一步驗證：' + rec['validation'])
    if not research['recommendations']:
        add('body', '目前證據不足，暫不提出基於競品的改善建議。')
    return blocks
