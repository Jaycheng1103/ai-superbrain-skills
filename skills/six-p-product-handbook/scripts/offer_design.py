"""v3 offer schema and content blocks; absent offers stay compatible with v2."""
from export_common import item, validate_item, require_text, display, table

DRIVERS = {'夢想結果', '相信會成功', '時間延遲', '付出與犧牲'}
FIELDS = {'name': '方案名稱', 'one_liner': '一句話介紹', 'total_value': '總參考價值',
          'price': '實際售價與付款方式', 'guarantee': '保證', 'scarcity': '稀缺', 'urgency': '急迫'}
SALES_FIELDS = {'headline': '標題', 'subheadline': '副標', 'cta': '行動呼籲'}
TITLE = '報價設計（價值堆疊與價格表）'


def empty_offer():
    return {**{key: item() for key in FIELDS},
            'obstacles': [{'text': '[待補資料]', 'driver': '相信會成功', 'status': '待補資料'}],
            'stack': [{'item': '[待補資料]', 'solves': '[待補資料]', 'delivery': '[待補資料]',
                       'value': '[待補資料]', 'basis': '[待補資料]', 'bonus': False, 'status': '待補資料'}],
            'sales_page': {key: item() for key in SALES_FIELDS}}


def validate_offer(offer, confirmed=False):
    if not isinstance(offer, dict):
        raise ValueError('offer 必須是物件；舊版請省略 offer')
    expected = set(FIELDS) | {'obstacles', 'stack', 'sales_page'}
    if set(offer) != expected:
        raise ValueError('offer 欄位缺漏或多餘：' + '、'.join(sorted(set(offer) ^ expected)))
    for key in FIELDS:
        validate_item(offer[key], 'offer.' + key, confirmed)
    for key in ['obstacles', 'stack']:
        if not isinstance(offer[key], list):
            raise ValueError('offer.' + key + ' 必須是陣列')
    if not offer['stack']:
        raise ValueError('offer.stack 至少需一項；未定請放待補資料項目')
    for n, obstacle in enumerate(offer['obstacles']):
        label = f'offer.obstacles[{n}]'
        validate_item(obstacle, label, confirmed)
        if not isinstance(obstacle.get('driver'), str) or obstacle['driver'] not in DRIVERS:
            raise ValueError(label + '.driver 只能是 夢想結果／相信會成功／時間延遲／付出與犧牲')
    for n, entry in enumerate(offer['stack']):
        label = f'offer.stack[{n}]'
        if not isinstance(entry, dict):
            raise ValueError(label + ' 必須是物件')
        if not isinstance(entry.get('bonus'), bool):
            raise ValueError(label + '.bonus 必須是布林值')
        for field in ['item', 'solves', 'delivery', 'value', 'basis']:
            require_text(entry.get(field), label + '.' + field)
            validate_item({'text': entry[field], 'status': entry.get('status')}, label + '.' + field, confirmed)
    sales = offer['sales_page']
    if not isinstance(sales, dict) or set(sales) != set(SALES_FIELDS):
        raise ValueError('offer.sales_page 必須含 headline、subheadline、cta')
    for key in SALES_FIELDS:
        validate_item(sales[key], 'offer.sales_page.' + key, confirmed)


def marked(content):
    return display(content, mark_confirmed=True)


def offer_blocks(offer):
    if offer is None:
        return []
    blocks = []
    def add(kind, value=''):
        blocks.append((kind, value, None))
    def field(key):
        add('h2', FIELDS[key])
        add('body', marked(offer[key]))
    add('break')
    add('h1', TITLE)
    add('small', '方法參考 Alex Hormozi《$100M Offers》。參考價值不等於成交價；各項沿用方案確認狀態。')
    field('name')
    field('one_liner')
    add('h2', '障礙清單')
    for entry in offer['obstacles']:
        add('body', marked(entry) + '｜方向：' + entry['driver'])
    if not offer['obstacles']:
        add('body', '[不適用] 目前沒有另列障礙。')
    for bonus, heading in [(False, '價值堆疊表'), (True, '贈品清單')]:
        add('h2', heading)
        entries = [e for e in offer['stack'] if e['bonus'] == bonus]
        if entries:
            blocks.append(table(['項目／狀態', '解決的障礙', '交付方式', '參考價值／依據'],
                                [[marked(item(e['item'], e['status'])), e['solves'], e['delivery'],
                                  e['value'] + '\n依據：' + e['basis']] for e in entries], [1.1, 1.3, 1.3, 1.6]))
        else:
            add('body', '[不適用] 本方案未另列' + ('贈品。' if bonus else '核心交付項目。'))
    add('h2', '總參考價值對照售價')
    add('body', '總參考價值：' + marked(offer['total_value']))
    add('body', '實際售價與付款方式：' + marked(offer['price']))
    for key in ['guarantee', 'scarcity', 'urgency']:
        field(key)
    add('h2', '銷售頁素材')
    for key in ['headline', 'subheadline']:
        add('body', SALES_FIELDS[key] + '：' + marked(offer['sales_page'][key]))
    for bonus, label in [(False, '你會得到'), (True, '贈品')]:
        entries = [e for e in offer['stack'] if e['bonus'] == bonus]
        if not entries:
            add('body', label + '：[不適用] 未另列項目。')
        for e in entries:
            add('body', label + '：' + marked(item(e['item'] + '（解決：' + e['solves'].rstrip('。') + '；交付：' + e['delivery'].rstrip('。') + '；參考價值：' + e['value'] + '）', e['status'])))
    add('body', '價格對照：總參考價值 ' + marked(offer['total_value']) + '；實際售價 ' + marked(offer['price']))
    add('body', '保證：' + marked(offer['guarantee']))
    add('body', '限制條件（稀缺）：' + marked(offer['scarcity']))
    add('body', '限制條件（急迫）：' + marked(offer['urgency']))
    add('body', '行動呼籲：' + marked(offer['sales_page']['cta']))
    return blocks
