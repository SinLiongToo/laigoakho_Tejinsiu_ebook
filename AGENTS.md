# 1917《內外科看護學》數位典藏專案規範與 Agent 指南 (AGENTS.md)

本專案為 1917 年戴仁壽醫師（Dr. George Gushue-Taylor）原著《內外科看護學》（*The Principles and Practice of Nursing* / *Lāi Gōa Kho Khàn-hō͘-ha̍k*）之現代化全書數位典藏、AI OCR 辨識、台漢逐段對照與雙模式電子書專案。

所有參與本專案維護與擴充的 AI Agent 應遵循以下原則與作業規範：

---

## 🏛️ 1. 典籍背景與專案目標

- **典籍名稱**：1917《內外科看護學》（全書共 705 頁）。
- **原著者**：戴仁壽 醫師 (Dr. George Gushue-Taylor, F.R.C.S., 1883–1954) 與 陳大鑼 先生 (Tân Tāi-lô) 合編。
- **文獻價值**：台灣醫學史上第一部現代護理學與臨床醫學教科書，亦為台語白話字（Pe̍h-ōe-jī）史上篇幅最宏大的醫學專著。
- **典藏成果**：
  1. 全書 705 頁白話字（POJ）高精度文字 OCR。
  2. 台灣本土全漢字逐段並列對照（Blockquotes 對照區塊）。
  3. 475 張原書醫學解剖與器械插圖自動裁切與內嵌。
  4. 2,625 條醫學台英漢三語辭典資料庫（GÚ-LŪI 1,019 條 + SEK-ÍN 1,606 條）。
  5. 雙模式（電子書模式 📖 ⇋ 醫學台語辭典模式 📚）SPA 站點建置。

---

## 📜 2. 文本規範與標點符號標準

### 2.1 Unicode NFC 正規化（防 iOS / WebKit 破音標）
- 白話字調號（如 `ē`、`ó`、`â`、`u̍`、`o͘`）在生成與輸出 Markdown 時，必須經由 `unicodedata.normalize('NFC', text)` 預組轉換，嚴禁輸出分離的 NFD 組合調號。
- 專有音標字元如 `o͘`（U+006F + U+0358）需確保在 `Iansui` 與 `POJ-Fallback` 字型棧中平整渲染。

### 2.2 全漢對照引言框（Blockquote）排版規範
- 每個對照區塊必須以 `> **【全漢對照】**` 開頭。
- 漢字文本標點符號必須為全形標點（`，`、`。`、`！`、`？`、`：`、`；`、`（）`、`［］`、`～`）。
- 英文與白話字正文維持半形標點（`,`、`.`、`:`、`!`、`?`）。

---

## 📚 3. 雙模式架構與辭典資料庫維護規範

### 3.1 辭典資料集生成流程
- 資料庫來源：
  - 附錄一：`docs/05_glossary/medical_glossary.md`（三語辭彙）
  - 附錄二：`docs/06_index/general_index.md`（總索引）
- 編譯與內嵌：
  - 由 `src/build_book.py` 內的 `generate_dictionary_dataset()` 解析，生成 `docs/assets/dictionary_data.js`。
  - 同步將 JSON 數據以 `<script id="dict-data" type="application/json">` 內嵌於 `docs/index.html`，以實現 0 毫秒極速同步載入。

### 3.2 字母歸類與搜尋比對邏輯
- 字母開頭判斷需優先檢查複合字首（`CHH`、`CH`、`KH`、`PH`、`TH`、`NG`、`O͘`），並對單字母剝除音標以歸入 `A`～`U`。
- 去調號模糊搜尋需將查詢詞以 `cleanDiacritics()` 轉換為純英文字元後與 `clean` 欄位比對。

---

## 🛠️ 4. 構建與部署指令指南

- **全書聚合與站點生成**：
  ```bash
  python src/build_book.py
  ```
- **本地預覽伺服器**：
  ```bash
  python -m http.server --directory docs 3000
  ```
- **版本提交與 GitHub Pages 發布**：
  ```bash
  git add docs/ src/build_book.py README.md
  git commit -m "feat/docs: update eBook and Dictionary SPA"
  git push origin main
  ```
