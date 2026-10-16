"""Offline regression tests. Run with the Python that has reportlab/pypdf/pytest."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from pypdf import PdfReader

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import export_common as common
import export_handbook as handbook
import export_market_report as market
from offer_design import FIELDS, SALES_FIELDS, TITLE
from research_appendix import PS


def source(number=1):
    return {'title': f'虛構示範來源 {number}', 'url': f'https://example.com/demo/{number}',
            'checked_at': '2026-10-16', 'supports': '僅供測試與排版示範，並非真實市場證據。'}


def competitor(number=1, verified=False):
    return {'id': f'C{number}', 'name': f'虛構工作室 {number}', 'type': '直接競品',
            'market': '示範地區', 'relevance': '同樣以剛開始接案的插畫工作者為對象。',
            'verified': verified,
            'six_p': dict(zip(PS, ['剛開始接案的插畫工作者', '交稿與修訂範圍不清楚',
                                  '業者主張：協助建立接案流程', '需求訪談、試作與交付檢核',
                                  '兩次小組討論與一份檢核表', '示範價格 NT$ 3,000／期，並非實際售價'])),
            'learn': '把修改次數與檔案格式寫清楚。', 'cautions': '虛構資料，不可作為定價依據。',
            'sources': [source(number)]}


def sample_manual():
    data = handbook.skeleton()
    data['meta'].update(title='插畫接案流程整理計畫（虛構示範）', owner='林小禾（虛構學員）',
                        industry='插畫服務', mode='教練／顧問', status='示範', version='v3-示範')
    summaries = ['服務剛開始獨立接案、需要整理交付流程的插畫工作者。',
                 '在需求確認與修改範圍不清楚時，容易反覆溝通而延後交付。',
                 '協助整理一份可供客戶核對的需求單與交付檢核表。',
                 '先盤點委託情境，再試填需求單，最後檢查交付內容。',
                 '四週內提供兩次小組討論、可編輯需求模板與一次作業回饋。',
                 '示範方案費用為 NT$ 6,000，報名前一次支付；實際條件另行確認。']
    details = [
        ['剛開始獨立接案的插畫工作者，委託人也是需求確認窗口。', '已有作品集，正在整理接案與交付流程。', '適合需要整理流程者；不包含代為尋找客戶。'],
        ['收到模糊需求時，不知道先確認尺寸、用途還是修改範圍。', '反覆確認需求增加溝通時間；目前沒有量化損失資料。', '曾使用一般待辦清單，但缺少客戶確認欄位。'],
        ['案件資料分散在對話與筆記裡。', '完成一份需求確認表與交付檢核表。', '以模擬案件試填，確認格式、用途與修改範圍；客戶須提供需求。'],
        ['第一週盤點，第二週試填，第三週討論，第四週整理可交付版本。', '學員試填需求單，教練針對資訊缺口提供回饋。', '完成可核對的欄位，再進行模擬交付檢查。'],
        ['兩次小組討論、需求確認模板一份、交付檢核表一份。', '四週線上進行；一次作業回饋，交付可編輯文件與 PDF。', '包含流程整理；不含代接案、法律審閱與客戶溝通代辦。'],
        ['虛構示範價 NT$ 6,000，由學員支付服務者；含稅假設仍需驗證。', '單一方案包含前述四週支持，沒有另外設計分級。', '示範為一次支付；取消與退款條件需在真實報名前另行確認。'],
    ]
    for section, summary, answers in zip(data['sections'], summaries, details):
        section['summary'] = common.item(summary, '待驗證')
        for field, answer in zip(section['fields'], answers):
            field.update(text=answer, status='待驗證')
        section['statement'] = common.item(summary, '待驗證')
    offer = data['offer']
    offer.update(name=common.item('四週插畫接案流程整理計畫', '待驗證'),
                 one_liner=common.item('協助剛開始獨立接案的插畫工作者，在四週內整理需求與交付流程。', '待驗證'),
                 obstacles=[common.item('怕漏問客戶需求，交稿後才發現認知不同。', '待驗證') | {'driver': '相信會成功'},
                            common.item('不想每次接案都從空白文件開始。', '待驗證') | {'driver': '付出與犧牲'}],
                 stack=[{'item': '需求盤點與情境演練小組', 'solves': '不知道哪些需求必須先問清楚。',
                         'delivery': '線上小組兩次，每次九十分鐘；每次提供討論紀錄與下一步練習。',
                         'value': 'NT$ 5,000（示範）', 'basis': '虛構數值，尚無實際單賣或公開市場價格支持。',
                         'bonus': False, 'status': '待驗證'},
                        {'item': '從需求確認到交付驗收的可編輯流程模板與使用說明',
                         'solves': '案件資訊分散在訊息裡，難以確認最後採用哪個版本。',
                         'delivery': '一份可編輯文件，包含需求、版本、修改次數與驗收欄位；使用前以模擬案件試填。',
                         'value': 'NT$ 3,000（示範）', 'basis': '僅作表格換行測試，不代表已驗證的價值。',
                         'bonus': False, 'status': '待驗證'},
                        {'item': '交稿前五分鐘檢核表', 'solves': '擔心遺漏檔案格式與命名。',
                         'delivery': '一頁 PDF，可列印勾選。', 'value': 'NT$ 1,000（示範）',
                         'basis': '虛構示範，未作市場調查。', 'bonus': True, 'status': '待驗證'}],
                 total_value=common.item('NT$ 9,000（虛構參考價值）', '待驗證'),
                 price=common.item('NT$ 6,000，一次支付；稅費與取消條件仍需確認。', '待驗證'),
                 guarantee=common.item('服務保證草案：若未收到約定模板，於通知後七日內補交；申請方式與例外需確認。', '待驗證'),
                 scarcity=common.item('不使用：目前未設定固定名額限制。', '不適用'),
                 urgency=common.item('不使用：目前沒有已確定的截止日。', '不適用'),
                 sales_page={'headline': common.item('用四週整理插畫接案的需求與交付流程', '待驗證'),
                             'subheadline': common.item('透過小組討論與可編輯模板，完成一份能核對的工作流程。', '待驗證'),
                             'cta': common.item('先提供匿名案件情境，確認適合範圍。', '待驗證')})
    data['open_questions'] = [{'question': '參考價值與取消條件仍需查證', 'why': '影響報價與對外承諾',
                               'next_action': '補公開價格來源，並確認可執行的交付條件。'}]
    data['research'].update(status='略過', limitations='本次僅示範 6P 與報價設計排版，未進行真實競品研究。')
    return data


def complete_manual():
    data = handbook.skeleton()
    data['meta'] = dict(title='已定方案', owner='虛構測試者', industry='服務', mode='顧問',
                        status='確認版', version='v3', date='2026-10-16')
    for content in handbook.all_items(data):
        content.update(text='本次已確認的方案內容。', status='已確認')
    data['open_questions'] = []
    for key in FIELDS:
        data['offer'][key] = common.item('已確認條件與適用範圍。', '已確認')
    for key in SALES_FIELDS:
        data['offer']['sales_page'][key] = common.item('已確認銷售文案。', '已確認')
    data['offer']['obstacles'] = [dict(text='需要確認交付項目', driver='夢想結果', status='已確認')]
    data['offer']['stack'] = [dict(item='需求模板', solves='避免遺漏', delivery='可編輯文件',
                                 value='NT$ 1,000', basis='原單賣價格', bonus=False, status='已確認')]
    return data


def sample_market(completed=False):
    data = market.skeleton()
    data['meta'].update(background='林小禾（虛構學員），曾整理插畫專案流程。', region='台灣／繁體中文',
                        provider='離線虛構示範，未呼叫搜尋服務', status='完成' if completed else '示範')
    for n, candidate in enumerate(data['candidates']):
        candidate.update(name=['初次接案的插畫工作者', '開始帶助理的設計工作室'][n],
                         audience_quotes=[{'text': '虛構摘要：想把交付規格講清楚，避免最後一刻才補資料。', 'sources': [source(90 + n)]}],
                         competitors=[competitor(i + 1 + n * 10, verified=completed) for i in range(5 if n == 0 else 3)],
                         saturation='中', advantage='具備整理需求與交付欄位的經驗。',
                         risks='付費意願與可觸及人數仍須實際訪談。',
                         gap='可測試把修改次數、版本紀錄與交付格式整理到同一份文件。')
        for key in market.CRITERIA[:3]:
            candidate['scores'][key] = {'score': 4 - n, 'reason': '示範判斷：模擬來源呈現需求與現有付費方案，仍需實際訪談核對。', 'sources': [source(n + 1)]}
    data['decision'].update(candidate_id='N1', niche='服務台灣初次接案的插畫工作者，整理需求與交付流程。',
                            reason='較符合學員目前能提供的流程整理經驗。',
                            rejected_reasons='帶助理的工作室還需要管理與授權設計經驗，超出本次範圍。',
                            validation='先訪談五位目標客戶，詢問最近一次修改範圍不清的情境；至少三位願意試填需求單才繼續測試。')
    data['recommendation'] = '先測試初次接案者的需求確認流程；由學員決定是否採用。'
    data['limitations'] = '全部為虛構排版與程式測試資料；example.com 是示例網址，沒有進行市場查核，分數與價格不可當成事實。'
    return data


@pytest.mark.parametrize('module', [handbook, market])
def test_init_and_export_cli(module, tmp_path):
    script = SCRIPTS / (module.__name__ + '.py')
    data_path, out = tmp_path / 'input.json', tmp_path / 'output'
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([sys.executable, str(script), '--init', str(data_path)], check=True, capture_output=True, env=env)
    subprocess.run([sys.executable, str(script), '--input', str(data_path), '--out-dir', str(out)], check=True, capture_output=True, env=env)
    report = json.loads((out / 'export-report.json').read_text())
    assert report['text_readback'] == report['link_annotations'] == 'passed'
    assert list(out.glob('*.pdf')) and list(out.glob('*.md'))
    retry = subprocess.run([sys.executable, str(script), '--init', str(data_path)], capture_output=True, text=True, env=env)
    assert retry.returncode != 0


def test_v2_without_offer_exports(tmp_path):
    data = handbook.skeleton()
    del data['offer']
    report = handbook.export(data, tmp_path / 'v2')
    assert report['offer_readback']['status'] == 'not_present'
    assert '報價設計' not in handbook.markdown(data)


@pytest.mark.parametrize('value', [None, [], {}, '錯誤'])
def test_offer_structure(value):
    data = handbook.skeleton()
    data['offer'] = value
    with pytest.raises(ValueError, match='offer'):
        handbook.validate(data)


@pytest.mark.parametrize('field,value', [('status', '已完成'), ('status', []), ('driver', '速度'), ('driver', None)])
def test_obstacle_invalid_values(field, value):
    data = handbook.skeleton()
    data['offer']['obstacles'][0][field] = value
    with pytest.raises(ValueError, match='offer.obstacles'):
        handbook.validate(data)


@pytest.mark.parametrize('target', ['name', 'sales_page', 'stack', 'obstacles'])
def test_offer_rejects_bad_status_everywhere(target):
    data = handbook.skeleton()
    content = {'name': data['offer']['name'], 'sales_page': data['offer']['sales_page']['cta'],
               'stack': data['offer']['stack'][0], 'obstacles': data['offer']['obstacles'][0]}[target]
    content['status'] = '完成'
    with pytest.raises(ValueError, match='status'):
        handbook.validate(data)


@pytest.mark.parametrize('field,value', [('bonus', 1), ('delivery', None), ('basis', ''), ('solves', [])])
def test_offer_stack_shape(field, value):
    data = handbook.skeleton()
    data['offer']['stack'][0][field] = value
    with pytest.raises(ValueError):
        handbook.validate(data)


@pytest.mark.parametrize('status', ['待驗證', '待補資料'])
@pytest.mark.parametrize('target', ['name', 'sales_page', 'stack', 'obstacles'])
def test_confirmed_rejects_pending_offer(status, target):
    data = complete_manual()
    content = {'name': data['offer']['name'], 'sales_page': data['offer']['sales_page']['cta'],
               'stack': data['offer']['stack'][0], 'obstacles': data['offer']['obstacles'][0]}[target]
    content['status'] = status
    with pytest.raises(ValueError, match='確認版'):
        handbook.validate(data)


def test_confirmed_offer_valid_and_unknown_cannot_hide():
    data = complete_manual()
    handbook.validate(data)
    data['offer']['stack'][0]['basis'] = '[待補資料]'
    with pytest.raises(ValueError, match='未知標記'):
        handbook.validate(data)


@pytest.mark.parametrize('score', [0, 6, True, '4', 2.5])
def test_market_invalid_scores(score):
    data = sample_market()
    data['candidates'][0]['scores']['痛點大']['score'] = score
    with pytest.raises(ValueError, match='1–5'):
        market.validate(data)


@pytest.mark.parametrize('score', [1, 5, None])
def test_market_score_boundaries(score):
    data = sample_market()
    data['candidates'][0]['scores']['痛點大']['score'] = score
    market.validate(data)


@pytest.mark.parametrize('score', [4, None])
def test_every_score_requires_reason(score):
    data = sample_market()
    data['candidates'][0]['scores']['痛點大'].update(score=score, reason='')
    with pytest.raises(ValueError, match='reason'):
        market.validate(data)


def test_scored_criterion_requires_source():
    data = sample_market()
    data['candidates'][0]['scores']['痛點大']['sources'] = []
    with pytest.raises(ValueError, match='來源'):
        market.validate(data)


def test_market_completed_can_keep_explicit_unknown():
    data = sample_market(completed=True)
    market.validate(data)
    assert '市場在成長：未知' in market.markdown(data)


def test_completed_decision_may_explain_uncertainty():
    data = sample_market(completed=True)
    data['decision']['rejected_reasons'] = '放棄其他候選，因付費意願仍待驗證，先聚焦已能觸及的對象。'
    market.validate(data)


def test_completed_market_counts_verified_competitors():
    data = sample_market(completed=True)
    data['candidates'][0]['competitors'].append(competitor(99, verified=False))
    market.validate(data)  # Five read sources still qualify; the sixth stays unverified.


@pytest.mark.parametrize('failure', ['one_candidate', 'four_competitors', 'unverified', 'unselected',
                                     'wrong_selection', 'reason', 'rejected_reasons', 'validation',
                                     'duplicate_candidate', 'duplicate_competitor'])
def test_market_completion_requirements(failure):
    data = sample_market(completed=True)
    if failure == 'one_candidate':
        data['candidates'].pop()
    elif failure == 'four_competitors':
        data['candidates'][0]['competitors'].pop()
    elif failure == 'unverified':
        data['candidates'][0]['competitors'][0]['verified'] = False
    elif failure == 'unselected':
        data['decision']['candidate_id'] = None
    elif failure == 'wrong_selection':
        data['decision']['candidate_id'] = 'N2'
    elif failure == 'duplicate_candidate':
        data['candidates'][1]['name'] = data['candidates'][0]['name']
    elif failure == 'duplicate_competitor':
        data['candidates'][0]['competitors'][1]['name'] = '  ' + data['candidates'][0]['competitors'][0]['name']
    else:
        data['decision'][failure] = '[待補資料]'
    with pytest.raises(ValueError):
        market.validate(data)


@pytest.mark.parametrize('module', [handbook, market])
def test_existing_output_directory_is_preserved(module, tmp_path):
    before = tmp_path / 'keep.txt'
    before.write_text('保留原檔')
    with pytest.raises(FileExistsError):
        module.export(module.skeleton(), tmp_path)
    assert before.read_text() == '保留原檔'
    assert len(list(tmp_path.iterdir())) == 1


def test_pdf_offer_readback_and_wrapping(tmp_path):
    data = sample_manual()
    data['offer']['stack'][1]['item'] += ' <b>原文</b> | 欄位'
    out = tmp_path / 'handbook'
    report = handbook.export(data, out)
    text = ''.join(p.extract_text() for p in PdfReader(out / '產品手冊.pdf').pages)
    compact = ''.join(text.split())
    assert ''.join(TITLE.split()) in compact
    for entry in data['offer']['stack']:
        assert ''.join(entry['item'].split()) in compact
    assert report['offer_readback']['stack_items'] == [e['item'] for e in data['offer']['stack']]
    md = (out / '產品手冊.md').read_text()
    assert md.index('## Price') < md.index('## 報價設計') < md.index('## 待確認事項')
    assert '### 贈品清單' in md and '&lt;b&gt;' in md and '&#124;' in md
    for label in ['你會得到', '價格對照', '限制條件', '行動呼籲']:
        assert label in text


def test_table_cells_can_continue_across_pages(tmp_path):
    data = sample_manual()
    for field in ['delivery', 'basis']:
        data['offer']['stack'][0][field] = ''.join(
            f'第{i}項{field}的條件包含交付格式與時段差異，需要逐項核對。' for i in range(1, 45))
    report = handbook.export(data, tmp_path / 'long-table')
    assert report['text_readback'] == 'passed'
    assert report['pages'] > 12


def test_market_completed_pdf_links_and_content(tmp_path):
    data = sample_market(completed=True)
    report = market.export(data, tmp_path / 'market')
    assert report['selected_verified_competitor_count'] == 5
    assert report['candidate_count'] == 2
    assert report['source_links'] == 10
    assert report['link_annotations'] == 'passed'


@pytest.mark.parametrize('omission', ['title', 'stack'])
def test_readback_rejects_missing_offer_content(omission, monkeypatch, tmp_path):
    data = sample_manual()
    render = common.build_pdf
    def omit(blocks, destination, **kwargs):
        removed = TITLE if omission == 'title' else data['offer']['stack'][0]['item']
        # Remove from every occurrence, including the derived sales-page materials.
        altered = json.loads(json.dumps(blocks, ensure_ascii=False).replace(removed, '文字遺失'))
        return render(altered, destination, **kwargs)
    monkeypatch.setattr(common, 'build_pdf', omit)
    out = tmp_path / 'broken'
    with pytest.raises(ValueError, match='讀回'):
        handbook.export(data, out)
    assert not out.exists()


def test_readback_checks_table_even_when_sales_copy_is_present(monkeypatch, tmp_path):
    data = sample_manual()
    render = common.build_pdf
    def omit(blocks, destination, **kwargs):
        altered = json.loads(json.dumps(blocks, ensure_ascii=False))
        next(value for kind, value, _ in altered if kind == 'table')['rows'][0][0] = '文字遺失'
        return render(altered, destination, **kwargs)
    monkeypatch.setattr(common, 'build_pdf', omit)
    with pytest.raises(ValueError, match='讀回'):
        handbook.export(data, tmp_path / 'broken-table')


def test_research_appendix_v2_still_checks_links(tmp_path):
    data = handbook.skeleton()
    del data['offer']
    data['research'].update(status='部分完成', competitors=[competitor()], recommendations=[
        dict(title='補上交付規格', related_p='Product', evidence_ids=['C1'], observation='有格式缺口',
             action='列出交付格式', validation='請客戶試讀')])
    report = handbook.export(data, tmp_path / 'research')
    assert report['source_links'] == 1 and report['competitor_count'] == 1
