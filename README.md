# 1917《內外科看護學》AI OCR 數位典藏、全漢對照與圖文電子書建置全書指南

> **典籍名稱**：1917《內外科看護學》（*Lāi Gōa Kho Khàn-hō͘-ha̍k*，全書共 705 頁）  
> **出版背景**：1917 年由台灣長老教會（彰化基督教醫院創辦人蘭大衛醫師等團隊）出版，為台灣醫學史與台語白話字（Pe̍h-ōe-jī）史料之第一部現代臨床護理教科書。  
> **專案成果**：全書 705 頁高精度文字 OCR、台漢逐段對照、原書解剖插圖自動擷取嵌入、三語辭典、總索引數位化，並發布為 **GitHub Pages 現代化 Web 電子書**。

---

## 📑 目錄
- [1. 系統架構與運作流程 (How the Flow Works)](#1-系統架構與運作流程-how-the-flow-works)
- [2. 關鍵技術突破與模型深度評測 (Model Benchmark)](#2-關鍵技術突破與模型深度評測-model-benchmark)
- [3. 插圖自動偵測與裁切流水線 (Illustration Extraction)](#3-插圖自動偵測與裁切流水線-illustration-extraction)
- [4. 目錄與檔案結構](#4-目錄與檔案結構)
- [5. 操作手冊與指令指南 (CLI Guide)](#5-操作手冊與指令指南-cli-guide)
- [6. 零中斷與斷點續跑機制 (Fault Tolerance)](#6-零中斷與斷點續跑機制-fault-tolerance)
- [7. API 計費與成本分析](#7-api-計費與成本分析)
- [8. GitHub Pages 線上部署教學](#8-github-pages-線上部署教學)
- [9. 將本專案轉化為通用數位典藏 Agent Skill (Reusable Skill Blueprint)](#9-將本專案轉化為通用數位典藏-agent-skill-reusable-skill-blueprint)

---

## 1. 系統架構與運作流程 (How the Flow Works)

```mermaid
flowchart TD
    PDF["1917-內外科看護學.pdf (705 頁)"] --> PDFProc["PyMuPDF 高清轉圖 (200 DPI PNG)"]
    
    subgraph OCR_Phase ["階段一：文字 OCR 與多語對照 (已完成)"]
        PDFProc --> CacheCheck{"檢查快取?<br>(cache/raw_pages/page_XXX.json)"}
        CacheCheck -->|已存在| SkipOCR["⚡ 秒級略過 (0 Token)"]
        CacheCheck -->|待處理| Classify{"章節與類型分流<br>(book_structure.json)"}
        Classify -->|英文序言| P1["Prompt A: 英文 OCR + 台文/中文雙譯"]
        Classify -->|白話字正文| P2["Prompt B: POJ OCR + 逐段全漢對照"]
        Classify -->|三語語彙表| P3["Prompt C: 醫學辭典 (GÚ-LŪI) Markdown 表格"]
        Classify -->|總索引| P4["Prompt D: 總索引 (SEK-ÍN) 條目擷取"]
        P1 & P2 & P3 & P4 --> GeminiOCR["Google Gemini 3.7 Flash API"]
        GeminiOCR --> SaveRaw["💾 儲存單頁原子快取 (page_XXX.json)"]
    end

    subgraph Fig_Phase ["階段二：插圖自動偵測與裁切 (外掛管線)"]
        PDFProc --> FigDetect["Gemini 3.7 Flash 佈局偵測<br>輸出座標 [ymin, xmin, ymax, xmax]"]
        FigDetect --> Crop["Pillow 高解析度自動裁切<br>docs/assets/illustrations/page_XXX_fig_YY.png"]
        Crop --> SaveFigIndex["💾 儲存插圖索引 (illustrations_index.json)"]
    end

    subgraph Build_Phase ["階段三：電子書聚合與發布"]
        SaveRaw & SaveFigIndex --> Builder["🔨 python src/build_book.py"]
        Builder --> Docs["docs/ (40 章 Markdown + 圖文並茂 + Docsify SPA)"]
        Docs --> GHPages["🌐 GitHub Pages 線上電子書"]
    end
```

---

## 2. 關鍵技術突破與模型深度評測 (Model Benchmark)

本專案經過 2025～2026 年多個世代的模型實戰對比，以下為 **Gemini 2.5 Flash**、**Gemini 3.7 Flash** 與 **Claude 3.7 Sonnet** 針對「百年台語白話字文獻數位化」的深度評測：

| 評測維度 | **Gemini 2.5 Flash** (三個月前舊版) | **Gemini 3.7 Flash** (本次採用) | **Claude 3.7 Sonnet** (可選用) |
| :--- | :--- | :--- | :--- |
| **POJ 聲調與點號辨識** | 🟡 偶爾漏失右上點號（`o͘`）或混淆陽入聲（`a̍`）與陽平（`ā`） | 🟢 **極高精確度**，能清晰辨識百年泛黃古籍之 `o͘`、`ⁿ` 與連字號 | 🟢 極高精確度，但有時會過度將古字拼寫標準化/現代化 |
| **台語全漢對照翻譯** | 🟡 部份台語語境較生硬，偶帶現代普通話語感 | 🟢 **非常道地文雅**（如精準對譯「備辦」、「向望」、「無彩工」、「寄附」） | 🟢 文學性與長句邏輯極佳，擅長古典英文題辭之精緻翻譯 |
| **全書 705 頁總花費** | 約 $0.25 USD (~NT$ 8 元) | **約 $0.40 USD (~NT$ 13 元)** | 約 $25.00 ～ $30.00 USD (~NT$ 800～950 元) |
| **API 頻率與穩定度** | 良好 | **極佳（Tier 1 RPM 達 1,000，全程零中斷）** | 圖片輸入受 Rate Limit 限制較嚴格 |
| **定位與最佳角色** | 舊世代基準 | 🏆 **全書大規模高吞吐 OCR、圖文辨識與對照之唯一首選** | 適合用於重要章節的二階段純文字「終審校對與學術註解」 |

---

## 3. 插圖自動偵測與裁切流水線 (Illustration Extraction)

原書包含數百張骨骼解剖、肌肉組織、外科手術器具與繃帶纏繞法之珍貴插圖。本系統採用 **AI 視覺邊界框偵測 + Pillow 原生裁切**：

1. **偵測提示詞 (`PROMPT_DETECT_FIGURES`)**：
   要求模型精準標記影像中所有非文字圖表的正規化座標 `[ymin, xmin, ymax, xmax]` 與原始圖題（Caption）。
2. **自動裁切與補償**：
   根據 PDF 200 DPI 渲染圖像的寬高動態換算像素，並自動加入 0.5% 邊界緩衝（Padding），避免切斷圖框。
3. **無損文字疊加**：
   插圖偵測完全獨立運行，**絕不重新執行或覆寫文字翻譯**，並在 `build_book.py` 聚合時自動以標準 HTML `<figure>` 標籤嵌入 Markdown。

---

## 4. 目錄與檔案結構

```text
Laigoakho_Tennjinsiu_OCR_MD/
├── .github/
│   └── workflows/
│       └── deploy.yml            # GitHub Pages 自動部署 Actions 工作流
├── config/
│   └── book_structure.json       # 705 頁全書篇章結構與頁碼對照定義檔
├── docs/                         # GitHub Pages 發布目錄 / 電子書根目錄
│   ├── index.html                # Docsify SPA 電子書引擎 (支援全文檢索與字級縮放)
│   ├── _coverpage.md             # 電子書封面
│   ├── _sidebar.md               # 側邊欄章節目錄
│   ├── README.md                 # 電子書首頁導讀
│   ├── assets/
│   │   └── illustrations/        # 自動裁切之全書醫學插圖 (PNG)
│   ├── 00_front_matter/          # 英文序言題辭 (多語對照)、台文頭序、凡例目錄
│   ├── 01_volume_1_anatomy/      # 第一篇 解剖學及生理學 (Ch 1～10)
│   ├── 02_volume_2_nursing/      # 第二篇 普通看護學 (Ch 11～21)
│   ├── 03_volume_3_surgery/      # 第三篇 外科看護學 (Ch 22～31)
│   ├── 04_volume_4_medicine/     # 第四篇 內科看護學 (Ch 32～40)
│   ├── 05_glossary/              # 三語語彙表 (GÚ-LŪI 結構化辭典表格)
│   └── 06_index/                 # 總索引 (SEK-ÍN 檢索目錄)
├── cache/
│   ├── raw_pages/                # 單頁文字原子快取 (page_001.json ~ page_705.json)
│   ├── illustrations/            # 單頁插圖座標快取 (page_001.json ~ page_705.json)
│   └── illustrations_index.json  # 全書插圖主索引
├── src/
│   ├── core/
│   │   ├── gemini_ocr.py         # Gemini 3.7 Flash API 調用與 Tenacity 重試封裝
│   │   ├── pdf_processor.py      # PyMuPDF 高清轉圖模組 (200 DPI)
│   │   └── prompt_templates.py   # 特化 Prompt 模板 (前言/正文/語彙/索引)
│   ├── run_ocr_pipeline.py       # 文字 OCR 主流水線驅動
│   ├── extract_all_illustrations.py # 全書插圖自動偵測與裁切流水線
│   └── build_book.py             # 快取聚合、插圖自動嵌入與 Docsify 導航生成
├── run_full_process.py           # 一鍵端到端全流程執行腳本
├── calculate_stats.py            # 即時進度、字數統計與 API 成本計算工具
└── README.md                     # 專案完整文檔
```

---

## 5. 操作手冊與指令指南 (CLI Guide)

### 🚀 一鍵端到端執行
```powershell
python run_full_process.py
```

### 🖼️ 執行全書插圖自動偵測與裁切
```powershell
python src/extract_all_illustrations.py
```

### 🔨 重新編譯生成 docs/ 電子書 (隨時可執行)
```powershell
python src/build_book.py
```

### 📊 查看目前字數、進度與 API 費用統計
```powershell
python calculate_stats.py
```

---

## 6. 零中斷與斷點續跑機制 (Fault Tolerance)

1. **單頁原子快取 (`cache/raw_pages/` & `cache/illustrations/`)**：
   每一頁完成後立即落盤為 JSON。若中途手動關閉或電腦重啟，再次執行會**瞬間略過已完成頁面**，0 重複耗費。
2. **Tenacity 指數退避重試**：
   遭遇網路斷線或 API 429 頻率限制時，自動進行 12 次漸進延遲重試（最高等待 90 秒）。
3. **錯誤自動隔離與批次尾端修復**：
   單頁若遇極端異常，流水線會記錄錯誤至 `error_log.txt` 並繼續往下跑，在全書批次尾段自動啟動二次重試修復。

---

## 7. API 計費與成本分析

- **文字 OCR 與全漢字對照**：全書 705 頁共產出 147 萬字，花費 **$0.4038 USD (約 NT$ 13.1 元)**。
- **插圖偵測與裁切**：全書 705 頁座標偵測，花費 **約 $0.09 USD (約 NT$ 3.0 元)**。
- **整部 705 頁圖文並茂歷史典籍數位化總成本**：**不到新台幣 16.5 元**。

---

## 8. GitHub Pages 線上部署教學

1. **提交並推送程式碼**：
   ```powershell
   git add .
   git commit -m "feat: complete 1917 Lai-goa-kho Tann-jin-siu digitalization"
   git push origin main
   ```
2. **啟用 GitHub Pages**：
   - 開啟 GitHub 倉庫 -> 點選 **Settings** -> **Pages**。
   - **Source** 選擇 **GitHub Actions**（專案已內建 `.github/workflows/deploy.yml`）。
   - 部署完成後，即可在 `https://<使用者名稱>.github.io/<倉庫名稱>/` 在線閱讀！

---

## 9. 將本專案轉化為通用數位典藏 Agent Skill (Reusable Skill Blueprint)

本專案建立的架構可直接作為任何**歷史文獻、多語古籍、圖文教科書數位化**的標準 Agent Skill 藍圖：

### 核心可重用模組：
1. **結構定義引擎 (`config/book_structure.json`)**：以 JSON 定義多篇章映射，杜絕 OCR 碎片化檔名。
2. **多模態特化提示詞模組 (`prompt_templates.py`)**：分離前言多語翻譯、正文嚴格逐段對照、字典表格化等場景。
3. **雙軌分離管線 (Two-Track Pipeline)**：
   - Track 1：專注於文本 OCR 與翻譯快取。
   - Track 2：專注於視覺佈局分析與高解析度插圖裁切。
4. **Docsify 靜態發布模板 (`build_book.py` + `index.html`)**：免編譯、即時渲染 Markdown、內建全文檢索與響應式雙語排版。
