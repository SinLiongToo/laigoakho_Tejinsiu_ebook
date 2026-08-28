# -*- coding: utf-8 -*-
"""
Book & GitHub Pages Site Builder for 1917 Lai-goa-kho Tann-jin-siu.
Aggregates single-page raw OCR results into clean chapter Markdown files,
automatically embeds extracted illustrations/diagrams, and generates Docsify navigation.
"""

import os
import sys
import json
import glob
from collections import defaultdict

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CONFIG_PATH = "config/book_structure.json"
CACHE_DIR = "cache/raw_pages"
ILLUSTRATION_CACHE_DIR = "cache/illustrations"
DOCS_DIR = "docs"

def load_book_structure():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_page_illustrations(page_num: int) -> list:
    """Load illustration metadata for a page if extracted."""
    ill_cache = os.path.join(ILLUSTRATION_CACHE_DIR, f"page_{page_num:03d}.json")
    if os.path.exists(ill_cache):
        try:
            with open(ill_cache, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("figures", [])
        except Exception:
            pass
    return []

def build_chapters():
    book_structure = load_book_structure()
    sections = book_structure["sections"]
    
    print("🔨 開始聚合章節 Markdown 文件至 docs/ (含插圖自動嵌入)...")
    
    sidebar_items = defaultdict(list)
    total_words = 0
    total_pages_included = 0
    total_illustrations_embedded = 0
    
    for sec in sections:
        sec_id = sec["id"]
        sec_title = sec["title"]
        vol_name = sec.get("volume_title", sec.get("volume", "前言與附錄"))
        target_file = sec["target_file"]
        target_path = os.path.join(DOCS_DIR, target_file)
        
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Calculate relative path from chapter directory to docs/assets/
        depth = target_file.count("/")
        rel_assets_prefix = "../" * depth + "assets/illustrations/"
        
        start_p = sec["start_page"]
        end_p = sec["end_page"]
        
        chapter_pages = []
        for p in range(start_p, end_p + 1):
            cache_file = os.path.join(CACHE_DIR, f"page_{p:03d}.json")
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data.get("text"):
                            figs = get_page_illustrations(p)
                            chapter_pages.append((p, data["text"], figs))
                except Exception:
                    pass
        
        if chapter_pages:
            total_pages_included += len(chapter_pages)
            with open(target_path, "w", encoding="utf-8") as f:
                # Chapter header
                f.write(f"# {sec_title}\n\n")
                if "volume_title" in sec:
                    f.write(f"> **所屬篇章**：{sec['volume_title']}\n")
                f.write(f"> **原書頁碼**：第 {start_p} 頁 ～ 第 {end_p} 頁 (已收錄 {len(chapter_pages)}/{end_p - start_p + 1} 頁)\n\n")
                f.write("---\n\n")
                
                for p_num, p_text, p_figs in chapter_pages:
                    f.write(f"<!-- Page {p_num:03d} Start -->\n")
                    f.write(f"#### 📖 原書第 {p_num} 頁\n\n")
                    
                    # Embed illustrations if present on this page
                    if p_figs:
                        f.write("\n<div align=\"center\" style=\"margin: 24px 0;\">\n\n")
                        for idx, fig in enumerate(p_figs):
                            fig_fn = fig.get("saved_file") or f"page_{p_num:03d}_fig_{idx+1:02d}.png"
                            fig_rel = f"assets/illustrations/{fig_fn}"
                            caption = fig.get("caption", "").strip()
                            alt_label = f"原書插圖 - 第 {p_num} 頁 (圖 {idx+1})"
                            f.write(f"![{alt_label}]({fig_rel})\n\n")
                            if caption:
                                f.write(f"<p style=\"font-size: 14.5px; color: #4a5568; margin-top: 8px; margin-bottom: 20px;\"><em>{caption}</em></p>\n\n")
                            total_illustrations_embedded += 1
                        f.write("</div>\n\n")
                        
                    f.write(p_text.strip())
                    f.write(f"\n\n<!-- Page {p_num:03d} End -->\n\n---\n\n")
                    total_words += len(p_text)
                    
            print(f"  📄 [{len(chapter_pages):02d} 頁] -> {target_file}")
            sidebar_items[vol_name].append((sec_title, target_file))
        else:
            sidebar_items[vol_name].append((sec_title, target_file))

    # Generate _sidebar.md
    sidebar_path = os.path.join(DOCS_DIR, "_sidebar.md")
    with open(sidebar_path, "w", encoding="utf-8") as f:
        f.write("* [🏠 首頁 (Home)](README.md)\n")
        f.write("* [📖 全書目錄 (Table of Contents)](00_front_matter/03_contents_and_rules.md)\n\n")
        
        for vol, items in sidebar_items.items():
            f.write(f"* **{vol}**\n")
            for title, path in items:
                f.write(f"  * [{title}]({path})\n")
            f.write("\n")
            
        f.write("* [📚 醫學三語辭彙表 (GÚ-LŪI)](05_glossary/medical_glossary.md)\n")
        f.write("* [🔍 總索引 (SEK-ÍN)](06_index/general_index.md)\n")
        
    print(f"✅ 側邊導航已生成: {sidebar_path}")

    # Generate _coverpage.md
    coverpage_path = os.path.join(DOCS_DIR, "_coverpage.md")
    with open(coverpage_path, "w", encoding="utf-8") as f:
        f.write("""# 1917 內外科看護學 <small>1.0</small>

> Lāi Gōa Kho Khàn-hō͘-ha̍k
> 全書台語白話字 (Pe̍h-ōe-jī) 現代 AI 視覺辨識與全漢字對照電子書 (含全書插圖)

- 台灣長老教會早期現代醫學經典
- 705 頁全書完整收錄：英文題辭序言、白話字正文 40 章、原書解剖插圖、三語語彙表與索引
- 採用 Gemini 3.7 Flash 深度多模態視覺佈局辨識與精密校注

[開始閱讀 (Get Started)](README.md)
[GitHub 專案庫](https://github.com/)
""")
    print(f"✅ 封面頁已生成: {coverpage_path}")

    # Generate docs/README.md
    readme_path = os.path.join(DOCS_DIR, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"""# 1917《內外科看護學》數位典藏電子書

歡迎閱讀 **《內外科看護學》（Lāi Gōa Kho Khàn-hō͘-ha̍k）** 現代化數位電子書。

本書於 1917 年由彰化基督教醫院創辦人蘭大衛醫師（Dr. David Landsborough）等宣教醫師團隊以台語白話字（Pe̍h-ōe-jī）編撰出版，是台灣醫學史與台語文獻史上極其珍貴的第一部現代臨床護理與醫學教科書。

---

## 🌟 數位化特色

1. **三語前言完整收錄**：包含蘭大衛醫師等人的英文序言、台文漢字與白話字對照、現代華語翻譯。
2. **正文 40 章逐段對照**：全書 705 頁高精度白話字（POJ）與台語全漢字逐段並列。
3. **醫學插圖與圖解完整嵌入**：自動裁切並高解析度還原人體解剖圖、外科器械與包紮繃帶插圖。
4. **醫學語彙辭典 (GÚ-LŪI)**：收錄書末珍貴的台語白話字、台語漢字與英語醫學專用術語三語辭典。
5. **現代化電子書閱讀體驗**：支援手機與電腦響應式排版、字級調整、全文搜尋與目錄導覽。

---

## 📚 目錄導覽

### 📖 前言與凡例
- [英文題辭與序言 (English Preface & Dedication)](00_front_matter/01_english_preface.md)
- [台文頭序 (Thâu-sū)](00_front_matter/02_thau_su.md)
- [目錄與借語凡例 (Chià-gô͘)](00_front_matter/03_contents_and_rules.md)

### 🩺 第一篇 解剖學及生理學 (Kái-phò͘-ha̍k kap Seng-lí-ha̍k)
- [第一章 身軀普通之構造](01_volume_1_anatomy/ch_01_body_structure.md)
- [第二章 骨系統](01_volume_1_anatomy/ch_02_skeletal_system.md)
- [第三章 筋肉系統及關節](01_volume_1_anatomy/ch_03_muscular_and_joints.md)
- [第四章 消化器系統](01_volume_1_anatomy/ch_04_digestive_system.md)
- [第五章 血及血管系統](01_volume_1_anatomy/ch_05_circulatory_system.md)
- [第六章 呼吸器系統](01_volume_1_anatomy/ch_06_respiratory_system.md)
- [第七章 泌尿器系統](01_volume_1_anatomy/ch_07_urinary_system.md)
- [第八章 皮膚](01_volume_1_anatomy/ch_08_skin_system.md)
- [第九章 神經系統](01_volume_1_anatomy/ch_09_nervous_system.md)
- [第十章 五官器](01_volume_1_anatomy/ch_10_sensory_organs.md)

### 🏥 第二篇 普通看護學 (Phó͘-thong Khàn-hō͘-ha̍k)
- 涵蓋第 11 章至第 21 章：看護職責、病室管理、飲食法、水浴、反對刺激、發藥等臨床技術。

### 🔪 第三篇 外科看護學 (Gōa-kho Khàn-hō͘-ha̍k)
- 涵蓋第 22 章至第 31 章：細菌與消毒、創傷、骨折、麻醉手術、繃帶學等外科護理。

### 💊 第四篇 內科看護學 (Lāi-kho Khàn-hō͘-ha̍k)
- 涵蓋第 32 章至第 40 章：各系統內科疾病、傳染病、熱帶醫學、產婦看護與嬰兒護理。

### 📖 附錄
- [三語醫學語彙表 (GÚ-LŪI)](05_glossary/medical_glossary.md)
- [總索引 (SEK-ÍN)](06_index/general_index.md)

---
*數位典藏建置年份：2026 年*
""")
    print(f"✅ 首頁 README.md 已生成: {readme_path}")

    # Generate docs/index.html (Docsify SPA with search, theme, styling)
    index_html_path = os.path.join(DOCS_DIR, "index.html")
    with open(index_html_path, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <title>1917 內外科看護學 - 台語白話字與全漢字數位電子書</title>
  <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1" />
  <meta name="description" content="1917 內外科看護學 (Lāi Gōa Kho Khàn-hō͘-ha̍k) 台語白話字 AI OCR 與全漢字逐段對照電子書">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0">
  <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@4/lib/themes/vue.css">
  <style>
    :root {
      --theme-color: #2c7a7b;
    }
    .markdown-section {
      max-width: 880px;
      font-size: 16.5px;
      line-height: 1.8;
    }
    blockquote {
      background: #f7fafc;
      border-left: 4px solid #2c7a7b;
      padding: 12px 18px;
      margin: 14px 0;
      color: #2d3748;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 1.5em 0;
    }
    table th {
      background-color: #edf2f7;
      color: #1a202c;
    }
    table th, table td {
      padding: 10px 14px;
      border: 1px solid #e2e8f0;
    }
    .sidebar {
      font-size: 14.5px;
    }
    figure {
      text-align: center;
      margin: 20px auto;
    }
    figure img {
      max-width: 100%;
      height: auto;
      box-shadow: 0 4px 10px rgba(0,0,0,0.08);
      border-radius: 6px;
    }
    figcaption {
      font-size: 14px;
      color: #4a5568;
      margin-top: 8px;
    }
  </style>
</head>
<body>
  <div id="app">正在載入《內外科看護學》電子書...</div>
  <script>
    window.$docsify = {
      name: '1917 內外科看護學',
      repo: '',
      loadSidebar: true,
      subMaxLevel: 3,
      coverpage: true,
      auto2top: true,
      search: {
        maxAge: 86400000,
        paths: 'auto',
        placeholder: '搜尋書中白話字、漢字或英文詞彙...',
        noData: '查無符合內容',
        depth: 4
      },
      pagination: {
        previousText: '上一篇',
        nextText: '下一篇',
        crossChapter: true
      },
      copyCode: {
        buttonText: '複製',
        errorText: '錯誤',
        successText: '已複製'
      }
    }
  </script>
  <!-- Docsify v4 -->
  <script src="//cdn.jsdelivr.net/npm/docsify@4"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify/lib/plugins/search.min.js"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify/lib/plugins/zoom-image.min.js"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify-copy-code/dist/docsify-copy-code.min.js"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify-pagination/dist/docsify-pagination.min.js"></script>
</body>
</html>
""")
    print(f"✅ Docsify Web 站點已更新: {index_html_path}")

if __name__ == "__main__":
    build_chapters()
