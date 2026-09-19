# AI 超級大腦流量學：學員 Skill 工具包

把自己的素材整理成 FB 長文、短影音腳本與 IG 輪播。先完成一份主稿，再依需求改編；每一份都用自己的語氣、真實經歷與品牌。

## 一次安裝完整三件組

這次新版包含 **FB 長文、短影音腳本、IG 輪播** 三支 skill。把本頁連結與下面這段話一起貼給支援安裝 skills 的 AI agent：

> 請從 https://github.com/Jaycheng1103/ai-superbrain-skills 安裝 skills/ 內的全部三支技能：fb-post-writer、reels-script-writer、ig-carousel-writer。先確認我的工具支援技能安裝，檢查同名版本並備份客製內容，再依目前環境安裝。安裝後逐一讀回 SKILL.md 與 references，列出三個名稱和實際安裝位置，並各做一次簡短測試。若目前工具不支援安裝，請說明如何下載、匯入或當作本次對話參考，不要宣稱已安裝。

使用 Claude Code／Codex 且已安裝 Node.js 的學員，也可以在自己的專案資料夾執行：

```bash
npx skills add Jaycheng1103/ai-superbrain-skills --skill '*' --agent claude-code codex --full-depth -y
```

這會安裝到目前專案，不會安裝到全域。已有同名客製版請先備份。其他支援的 agent 可移除 `--agent claude-code codex`，依安裝器選單選擇自己的工具。

**[下載完整三件組 ZIP](downloads/content-creation-skills-20260919.zip?raw=true)** · [學員開始使用](學員開始使用.md)

下載後解壓外層，三個資料夾內各選 `.skill` 或 `.zip` 匯入。Claude／Manus 等平台是否支援匯入，依你當下帳號與工具提供的功能為準。一般 ChatGPT 聊天上傳文件屬於本次對話參考，不等於永久安裝。

## 本次更新（2026-09-19）

| 工具 | 本版交付 | 獨立 repo |
|---|---|---|
| [FB 長文寫手](FB長文寫手/如何使用.md) | 完整長文初稿，依素材調整篇幅，內部備註分開 | [superbrain-fb-post-writer](https://github.com/Jaycheng1103/superbrain-fb-post-writer) |
| [短影音腳本寫手](短影音腳本寫手/如何使用.md) | 一版可拍腳本，含台詞、畫面與估計時間 | [superbrain-reels-script-writer](https://github.com/Jaycheng1103/superbrain-reels-script-writer) |
| [IG 輪播圖文](IG輪播圖卡寫手/如何使用.md) | 逐頁文案、素材規劃與 Caption；有工具時製作圖片並驗收 | [superbrain-ig-carousel-writer](https://github.com/Jaycheng1103/superbrain-ig-carousel-writer) |

各資料夾內提供 `.skill` 與同內容 `.zip`。依平台目前支援的格式匯入；不把一般聊天上傳宣稱為永久安裝。詳細看 [學員開始使用](學員開始使用.md)。

## 既有延伸工具

以下維持原版本，本次沒有更新或重新驗收：

- [五大選題產生器](https://github.com/Jaycheng1103/superbrain-topic-finder)
- [Threads 模板教練](https://github.com/Jaycheng1103/superbrain-threads-template-coach)

想依選題、切角、形式、腳本、Hook、剪輯與銷售流程練習，可參考 [內容廚房系統](https://github.com/Jaycheng1103/content-kitchen-system)。本包的短影音仍是該課程步驟 4；「FB 主稿再改編」是另一條內容使用方式，不改動課程順序。

## 使用前要知道

不需要講師的私人工作區或品牌資產。沒有語感樣本也能起稿；沒有圖片工具仍可做輪播規劃。AI 不會自動發布，成品也不保證流量或轉換。學員資料放在自己的專案，不提交到公開教材。

各套件既有授權與第三方素材限制仍各自適用，詳見套件內文件；本總覽不新增或擴張授權。
