# PDF 與 Drive 交付

## 本機 PDF

Python 3.10+，依賴見 `scripts/requirements.txt`。若有 `load_workspace_dependencies` 先用環境現成 runtime。內含繁中字型與授權，不依賴講師路徑。缺套件時建虛擬環境：

```sh
python3 -m venv .venv-six-p
.venv-six-p/bin/python -m pip install -r "<skill資料夾>/scripts/requirements.txt"
```

Windows 改用 `.venv-six-p/Scripts/python.exe`。以下 `<...>` 均需換成實際路徑；採用已安裝依賴的 Python：

```sh
python3 "<skill資料夾>/scripts/export_handbook.py" --init "<本次學員資料夾>/manual.json"
python3 "<skill資料夾>/scripts/export_handbook.py" --input "<本次學員資料夾>/manual.json" --out-dir "<本次學員資料夾>/交付_v1"
```

`--init` 建立完整資料骨架。填入答案、摘要、填寫句與狀態，日期用實際日期，保留 schema_version。腳本排版及檢查結構，不替學員決策或查證。

- meta.status：草稿、待補版、確認版、示範。
- 各內容 status：已確認、待驗證、待補資料、不適用。
- 確認版不可含未知、待驗證、空白填寫句或未決問題，腳本會擋明顯缺漏；語意仍由訪談者檢查。
- 產出 `產品手冊.md`、`產品手冊.pdf`、`export-report.json`；不覆寫既有檔，改用新版輸出資料夾。
- Markdown 與 PDF 共用 JSON。原始訪談、私人來源、個資留在 state，不放入手冊。

## 競品研究資料

`--init` 會附空的 `research`。原 `sections`、`open_questions` 原樣保留。舊版沒有 research 仍可匯出。以下是一家競品與一項建議的欄位示意，非完成的五家研究：

```json
{
  "status": "部分完成",
  "provider": "Tavily",
  "checked_at": "2026-09-24",
  "scope": "依原手冊填入受眾、問題、市場與交付型態",
  "limitations": "填入來源缺漏、比價限制及相鄰參考的擴大範圍",
  "competitors": [{
    "id": "C1", "name": "業者名稱", "type": "直接競品",
    "market": "主要市場", "relevance": "與原方案相關的理由",
    "verified": false,
    "six_p": {
      "People": "公開客群", "Problem": "公開問題", "Promise": "業者主張",
      "Plan": "公開流程", "Product": "公開交付", "Price": "公開價格與條件，未公開則明寫"
    },
    "learn": "具體可學習做法", "cautions": "不宜照搬與限制",
    "sources": [{"title": "來源標題", "url": "https://example.com/offer",
      "checked_at": "2026-09-24", "supports": "此頁實際支持哪些內容"}]
  }],
  "recommendations": [{
    "title": "建議名稱", "related_p": "Product", "evidence_ids": ["C1"],
    "observation": "競品觀察與原手冊缺口", "action": "建議調整",
    "validation": "學員下一步如何驗證"
  }]
}
```

日期、網址、內容都換成實際資料。`verified: true` 只表示本次已讀到一手頁面；不代表業者的成果主張已獨立查證，腳本也無法代替來源查核。

研究狀態：待研究、未連接、部分完成、完成、略過、示範。`完成` 須至少五家不同且已讀一手來源的相關業者，並附建議；不足則使用部分完成並說明原因。學員方案尚有缺項也可完成研究，手冊本身仍保持待補版。未連接時 competitors 與 recommendations 留空，limitations 寫連接提醒；不生成虛構名單。

PDF 來源標題可點擊；腳本同時讀回所有研究文字與連結註記。`export-report.json` 記錄研究狀態、競品數、來源連結數。目視檢查涵蓋研究附錄與最末建議頁。研究與建議含有學員內部策略，預設隨私人手冊交付；對外銷售版另製，不混入研究附錄。

## 讀回檢查

核對六個 P、18 欄、總覽與正文一致；檢查中文、數字、日期、價格、幣別及條件。

```sh
pdftoppm -scale-to 1600 -png "產品手冊.pdf" "檢查/page"
```

先建立檢查資料夾，逐頁看字形、截字、換頁與頁碼。沒有 Poppler 可用環境 PDF 預覽／可靠渲染器。無法渲染時可交檔，但需註明「文字已讀回，版面尚未目視驗證」。沒有執行環境就先交文字，不能編造 PDF。

## 選用 Google Drive

使用當前可用 connector／官方 API／已登入瀏覽器，讀當前工具 schema，不假設 API 格式固定。若環境有 Drive skill，遵循其檔案操作規則。

1. 學員要求上傳後，讀登入帳號並確認是其預期帳號，不沿用講師環境。目的地不明時問位置，同時先交本機 PDF。
2. 讀目的資料夾 metadata，確認類型、寫入權限與共用範圍。重名時請指定連結／ID。
3. 上傳已驗證 PDF，MIME `application/pdf`，只傳手冊，不傳原始訪談或 state。不為了連結另做內容不同的 Google Doc。
4. 依工具 schema 傳本機路徑或平台檔案 reference，不猜格式、不貼 base64、不轉送第三方。
5. 用回傳 ID 讀 metadata：名稱、MIME、父資料夾、大小及可用 checksum；能下載時比較 SHA-256 或文字。
6. 使用工具實際回傳連結，打開或 connector 讀回確認該 PDF。不可預測或自造網址。
7. 保留現有權限。私人連結不需公開；另要求分享才依明確授權設定及驗證，不寄信、不通知。

上傳 timeout 先查目的資料夾是否已有本次同名、同大小及同 checksum 檔案，再決定是否重試；無法辨識就停，避免重複。缺連線、無權限或讀回失敗時交本機 PDF，明說雲端尚未完成。
