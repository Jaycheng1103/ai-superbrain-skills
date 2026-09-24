# 6P 產品手冊訪談教練

這個 skill 會先了解你如何服務客戶，再訪談你完成 People、Problem、Promise、Plan、Product、Price，接著用 Tavily 尋找至少五個相關競品，附改善建議，整理成可編輯文字與 PDF。教練、顧問、接案、代操、房仲、保險或其他行業都可以使用，不必先有課程。

## 安裝到 Codex

把本頁網址與這段話貼給 Codex：

> 請從 https://github.com/Jaycheng1103/ai-superbrain-skills 安裝 skills/six-p-product-handbook。請先保留同名舊版或客製內容，再安裝完整技能資料夾。完成後讀回 SKILL.md、競品研究指引與 PDF 匯出腳本，告訴我實際安裝位置。接著用這個 skill 訪談我，整理產品手冊、研究競品並給我 PDF。

有 Node.js 的學員，可在專案資料夾執行以下指令，只安裝這一支 skill 到目前專案：

```sh
npx skills add Jaycheng1103/ai-superbrain-skills --skill six-p-product-handbook --agent codex --full-depth -y
```

已有同名客製版請先備份。要安裝到全域或不使用 Node.js，可下載 [完整學員安裝包 ZIP](../downloads/six-p-product-handbook-v2.zip?raw=true)，依下方方式安裝。

完整解壓安裝包，在此資料夾開啟終端機並執行：

```sh
python3 install.py --platform codex
```

Windows 若只有 `py` 指令，使用 `py install.py --platform codex`。安裝後重新開啟 Codex 工作階段；已安裝同名版本時不覆寫，先保存舊版再更新。

你也可以將整個 `six-p-product-handbook` 資料夾交給 Codex，說：「請將這個 skill 安裝到我的全局技能資料夾，保留舊版。」

Claude Code 使用者可執行 `python3 install.py --platform claude`，或由自己的工具按支援的技能安裝方式載入整個資料夾。其他平台需支援讀取 SKILL.md、執行 Python 與存取輸出檔案；沒有檔案執行能力的純聊天環境只能訪談與整理文字。

## 開始使用

直接貼上：

> 請用 $six-p-product-handbook 訪談我。我想把自己的服務整理成產品手冊，請先了解我的行業與服務模式，再逐步問我，再用 Tavily 找至少五個相關競品，附來源、可學習做法與改善建議，最後給我 PDF。

已經有資料時，把自己的服務介紹、方案或匿名案例一起提供。不要貼客戶證件、保單個資、帳密或不必要的敏感原件。

每回合通常只回答一至三題；不知道也可以直接說，AI 會協助收斂，並把尚未確定的內容標為待補或待驗證。也可以說「先匯出待補版」，不必等所有細節確定。

## 你會拿到什麼

- 一頁 6P 總覽。
- 六個 P 的詳細說明，各保留三個欄位與完成的填寫句。
- 待確認事項與下一步。
- 至少五家相關競品的 6P 比較、官網來源、查閱日期及可學習做法。
- 針對自己原手冊的改善建議與驗證步驟。
- `產品手冊.md` 與 `產品手冊.pdf`，預設 A4 直式，可列印。

文件會標示草稿、待補版或確認版。實際頁數依答案長度自動調整，加上研究附錄後通常會增加頁數。AI 不會替你捏造案例、價格、保證或客戶成果。

## Tavily 競品搜尋

請使用自己的 Tavily 連線。在 Codex 的「外掛程式」搜尋 Tavily，依畫面安裝或連接。安裝本 skill 不等於已連接 Tavily；AI 會實際檢查可用工具，不需要把 API key 貼在對話中。

流程是先完成自己的 6P，再研究競品。AI 會優先找與受眾、問題、市場及服務模式相近的業者，區分直接競品與相鄰參考。每家都附來源；沒有公開價格或成果證據時會標明，不編造資料。最後的改善建議先列為待驗證，採納後才另存新版原手冊。

未連接時會提醒連接；暫時無法使用或資料不足時，仍可先拿原手冊與已完成的部分，研究狀態會如實標示。研究與建議預設供自己參考，不要直接把含內部策略的完整手冊當對外銷售文件。

## PDF 環境

內附繁體中文字型與授權。需要 Python 3.10 以上、reportlab 與 pypdf。AI 可先使用現成環境；沒有套件時，在專案資料夾執行：

```sh
python3 -m venv .venv-six-p
.venv-six-p/bin/python -m pip install -r six-p-product-handbook/scripts/requirements.txt
```

Windows 使用 `py -m venv .venv-six-p`，再執行 `.venv-six-p\Scripts\python.exe -m pip install -r six-p-product-handbook/scripts/requirements.txt`。

版面驗證需要 PDF 預覽工具，或 Poppler 的 `pdftoppm`。AI 會檢查 PDF 文字與各頁排版；環境不能產檔時，會說明限制並先交付文字。

## 上傳 Google Drive

想放雲端時，告訴 AI「請上傳到我的 Google Drive」，並指定資料夾。需在你自己的工具連接 Drive；AI 會核對帳號、目的資料夾及上傳結果，再給 PDF 連結。

預設保留私人權限，不會自動公開、寄信或發通知。未連接 Drive 仍可取得本機 PDF。安裝此 skill 不會自動取得 Google 帳號權限。

## 套件內容

`six-p-product-handbook/` 是技能本體，包含訪談指引、固定模板、PDF 匯出腳本與開源字型；`install.py` 為安裝工具。套件未附任何講師帳號、API key、學生資料或私人品牌素材。
