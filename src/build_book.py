# -*- coding: utf-8 -*-
"""
Book & GitHub Pages Site Builder for 1917 Lai-goa-kho Tann-jin-siu.
Aggregates single-page raw OCR results into clean chapter Markdown files,
automatically embeds extracted illustrations/diagrams, and generates Docsify navigation with collapsible sidebar.
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

INDEX_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <title>1917 內外科看護學 - 台語白話字與全漢字數位電子書</title>
  <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1" />
  <meta name="description" content="1917 內外科看護學 (Lāi Gōa Kho Khàn-hō͘-ha̍k) 全書台語白話字 AI OCR、全漢字逐段對照與原書解剖插圖電子書">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, viewport-fit=cover">
  
  <!-- Web Fonts (Iansui 芫荽體, HanaMin, Klee One, Noto Serif TC, Roboto) -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/hanamin@0.0.5/HanaMin.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Klee+One&family=Noto+Serif+TC:wght@400;600;700&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
  
  <!-- Docsify Theme & Collapsible Sidebar Plugin Style -->
  <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@4/lib/themes/vue.css">
  <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify-sidebar-collapse/dist/sidebar.min.css" />
  
  <style>
    /* ==========================================================================
       Font Faces (Iansui 芫荽體 & POJ Diacritics Fallback)
       ========================================================================== */
    @font-face {
      font-family: 'Iansui';
      src: url('https://cdn.jsdelivr.net/gh/ButTaiwan/iansui@main/Iansui-Regular.ttf') format('truetype');
      font-weight: normal;
      font-style: normal;
      font-display: swap;
    }

    @font-face {
      font-family: 'POJ-Fallback';
      src: local('-apple-system'), local('Roboto'), local('Segoe UI'), local('Arial'), local('Helvetica Neue');
      unicode-range: U+0020-007F, U+00A0-024F, U+0300-036F, U+2070-209F;
    }

    /* ==========================================================================
       CSS Variables & Themes (Light / Dark)
       ========================================================================== */
    :root {
      --font-zh: 'POJ-Fallback', 'Iansui', 'Klee One', 'HanaMin', 'Noto Serif TC', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-en: 'POJ-Fallback', 'Roboto', -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      
      --theme-color: #2c7a7b;
      --theme-accent: #319795;
      
      /* Light Mode Variables */
      --bg-primary: #ffffff;
      --bg-secondary: #f8fafc;
      --bg-sidebar: #f8fafc;
      --text-primary: #1a202c;
      --text-secondary: #4a5568;
      --text-muted: #718096;
      --border-color: #e2e8f0;
      --blockquote-bg: #f0fdf4;
      --blockquote-border: #2c7a7b;
      --table-th-bg: #edf2f7;
      --card-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
      --code-bg: #f1f5f9;
      --sidebar-toggle-bg: #ffffff;
    }

    [data-theme="dark"] {
      /* Dark Mode Variables */
      --bg-primary: #0f172a;
      --bg-secondary: #1e293b;
      --bg-sidebar: #1e293b;
      --text-primary: #f1f5f9;
      --text-secondary: #cbd5e1;
      --text-muted: #94a3b8;
      --border-color: #334155;
      --blockquote-bg: #1e293b;
      --blockquote-border: #38b2ac;
      --table-th-bg: #334155;
      --card-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
      --code-bg: #1e293b;
      --sidebar-toggle-bg: #1e293b;
    }

    /* ==========================================================================
       Base Typography & Layout
       ========================================================================== */
    body {
      background-color: var(--bg-primary) !important;
      color: var(--text-primary) !important;
      font-family: var(--font-zh) !important;
      font-size: 17px;
      line-height: 1.85;
      transition: background-color 0.3s ease, color 0.3s ease;
      -webkit-font-smoothing: antialiased;
    }

    .markdown-section {
      max-width: 900px;
      padding: 30px 24px 80px 24px !important;
      color: var(--text-primary) !important;
      font-family: var(--font-zh) !important;
    }

    .markdown-section h1, 
    .markdown-section h2, 
    .markdown-section h3, 
    .markdown-section h4 {
      color: var(--text-primary) !important;
      font-family: var(--font-zh) !important;
      font-weight: 700;
    }

    .markdown-section h1 {
      border-bottom: 2px solid var(--border-color);
      padding-bottom: 12px;
      margin-top: 10px;
    }

    .markdown-section a {
      color: var(--theme-color);
      font-weight: 500;
      text-decoration: none;
    }
    .markdown-section a:hover {
      text-decoration: underline;
    }

    /* ==========================================================================
       Blockquotes (Taiwanese Han-ji & Translations)
       ========================================================================== */
    .markdown-section blockquote {
      background-color: var(--blockquote-bg) !important;
      border-left: 4px solid var(--blockquote-border) !important;
      color: var(--text-primary) !important;
      padding: 14px 20px;
      margin: 16px 0 24px 0;
      border-radius: 0 8px 8px 0;
      box-shadow: var(--card-shadow);
      font-size: 16.5px;
      line-height: 1.8;
      font-family: var(--font-zh) !important;
    }

    .markdown-section blockquote p {
      margin: 6px 0;
      color: var(--text-primary) !important;
    }

    /* ==========================================================================
       Responsive Tables
       ========================================================================== */
    .markdown-section table {
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
      display: block;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      border: 1px solid var(--border-color);
      border-radius: 8px;
    }

    .markdown-section table th {
      background-color: var(--table-th-bg) !important;
      color: var(--text-primary) !important;
      font-weight: 600;
      padding: 12px 14px;
      border: 1px solid var(--border-color);
      white-space: nowrap;
      font-family: var(--font-zh) !important;
    }

    .markdown-section table td {
      padding: 10px 14px;
      border: 1px solid var(--border-color);
      color: var(--text-primary) !important;
      font-family: var(--font-zh) !important;
    }

    /* ==========================================================================
       Responsive Illustrations & Figures
       ========================================================================== */
    .markdown-section img {
      max-width: 92% !important;
      height: auto !important;
      border-radius: 8px;
      box-shadow: var(--card-shadow);
      margin: 12px auto;
      display: inline-block;
      transition: transform 0.2s ease, filter 0.3s ease;
      background-color: #ffffff;
      padding: 6px;
    }

    [data-theme="dark"] .markdown-section img {
      filter: brightness(0.92) contrast(1.05);
      background-color: #1e293b;
    }

    .markdown-section hr {
      border: 0;
      border-top: 1px solid var(--border-color);
      margin: 32px 0;
    }

    /* ==========================================================================
       Sidebar & Collapsible Navigation Styling
       ========================================================================== */
    .sidebar {
      background-color: var(--bg-sidebar) !important;
      border-right: 1px solid var(--border-color) !important;
      color: var(--text-primary) !important;
      font-size: 15px;
      font-family: var(--font-zh) !important;
      transition: all 0.3s ease;
    }

    .sidebar ul li a {
      color: var(--text-secondary) !important;
      padding: 6px 10px;
      border-radius: 6px;
      display: block;
      font-family: var(--font-zh) !important;
      font-size: 14.5px;
    }

    .sidebar ul li.active > a,
    .sidebar ul li a:hover {
      color: var(--theme-color) !important;
      background-color: var(--border-color);
      font-weight: 600;
    }

    .sidebar .folder {
      cursor: pointer;
      font-weight: 700;
      color: var(--text-primary) !important;
      padding: 8px 6px;
      display: block;
      user-select: none;
    }

    /* ==========================================================================
       Dedicated Search Panel (Separated from Sidebar Chapters Tree)
       ========================================================================== */
    .sidebar .search {
      position: relative;
      border-bottom: 2px solid var(--border-color) !important;
      padding: 12px 14px;
      margin-bottom: 8px;
    }

    .sidebar .search input {
      background-color: var(--bg-primary) !important;
      color: var(--text-primary) !important;
      border: 1.5px solid var(--border-color) !important;
      border-radius: 8px;
      padding: 8px 12px;
      width: 100%;
      font-family: var(--font-zh) !important;
      font-size: 14px;
      box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
      transition: all 0.2s ease;
    }

    .sidebar .search input:focus {
      border-color: var(--theme-color) !important;
      box-shadow: 0 0 0 3px rgba(44, 122, 123, 0.2);
      outline: none;
    }

    /* Floating Search Results Dropdown Panel */
    .sidebar .results-panel {
      position: absolute;
      left: 8px;
      right: 8px;
      top: 100%;
      z-index: 9999;
      background-color: var(--bg-primary) !important;
      border: 1.5px solid var(--theme-color) !important;
      border-radius: 8px;
      box-shadow: 0 12px 28px rgba(0, 0, 0, 0.25);
      max-height: 460px;
      overflow-y: auto;
      padding: 8px 10px;
    }

    .sidebar .results-panel .matching-post {
      border-bottom: 1px solid var(--border-color);
      padding: 8px 4px;
      margin-bottom: 6px;
    }

    .sidebar .results-panel .matching-post:last-child {
      border-bottom: none;
    }

    .sidebar .results-panel h2 {
      font-size: 14.5px;
      color: var(--theme-color) !important;
      margin: 2px 0 4px 0;
      font-weight: 700;
    }

    .sidebar .results-panel p {
      font-size: 13px;
      color: var(--text-secondary) !important;
      line-height: 1.5;
      margin: 0;
    }

    /* ==========================================================================
       Main Content Keyword Highlighting (主畫面字元反白)
       ========================================================================== */
    mark.search-keyword-highlight,
    .search-keyword-highlight {
      background-color: #fef08a !important;
      color: #1e293b !important;
      padding: 2px 4px !important;
      border-radius: 3px !important;
      font-weight: 700 !important;
      border-bottom: 2px solid #eab308 !important;
      box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }

    [data-theme="dark"] mark.search-keyword-highlight,
    [data-theme="dark"] .search-keyword-highlight {
      background-color: #a16207 !important;
      color: #fef9c3 !important;
      border-bottom: 2px solid #facc15 !important;
    }

    [data-theme="dark"] .sidebar-nav li::before {
      color: var(--text-muted) !important;
    }

    /* ==========================================================================
       Floating Dark Mode Switcher Button
       ========================================================================== */
    #theme-toggle-btn {
      position: fixed;
      top: 14px;
      right: 18px;
      z-index: 1000;
      background-color: var(--bg-secondary);
      color: var(--text-primary);
      border: 1px solid var(--border-color);
      border-radius: 50%;
      width: 42px;
      height: 42px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 2px 10px rgba(0,0,0,0.15);
      transition: all 0.25s ease;
      font-size: 19px;
      user-select: none;
    }

    #theme-toggle-btn:hover {
      transform: scale(1.08);
      border-color: var(--theme-color);
    }

    /* ==========================================================================
       Mobile & Tablet Responsive Adjustments (RWD)
       ========================================================================== */
    @media screen and (max-width: 768px) {
      .markdown-section {
        padding: 20px 16px 60px 16px !important;
        font-size: 16px;
      }
      
      .markdown-section blockquote {
        padding: 12px 14px;
        margin: 14px 0;
        font-size: 15.5px;
      }

      #theme-toggle-btn {
        top: 10px;
        right: 12px;
        width: 36px;
        height: 36px;
        font-size: 16px;
      }

      .sidebar-toggle {
        background-color: var(--sidebar-toggle-bg) !important;
        bottom: 20px;
        left: 20px;
        border-radius: 50%;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        padding: 10px;
        width: 30px;
        height: 30px;
      }
    }
  </style>
</head>
<body>
  <!-- Dark Mode Toggle Button -->
  <button id="theme-toggle-btn" title="切換深色/淺色模式" aria-label="Toggle Dark Mode">🌙</button>

  <div id="app">正在載入《內外科看護學》圖文電子書...</div>

  <script>
    // --------------------------------------------------------------------------
    // Theme Management (Dark Mode / Light Mode with LocalStorage & OS detection)
    // --------------------------------------------------------------------------
    function initTheme() {
      const savedTheme = localStorage.getItem('site_theme');
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      const currentTheme = savedTheme || (prefersDark ? 'dark' : 'light');
      
      document.documentElement.setAttribute('data-theme', currentTheme);
      updateToggleBtn(currentTheme);
    }

    function toggleTheme() {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('site_theme', newTheme);
      updateToggleBtn(newTheme);
    }

    function updateToggleBtn(theme) {
      const btn = document.getElementById('theme-toggle-btn');
      if (btn) {
        btn.textContent = theme === 'dark' ? '☀️' : '🌙';
      }
    }

    initTheme();
    document.addEventListener('DOMContentLoaded', () => {
      const btn = document.getElementById('theme-toggle-btn');
      if (btn) {
        btn.addEventListener('click', toggleTheme);
      }
    });

    // --------------------------------------------------------------------------
    // Keyword Highlighting in Main Content Area
    // --------------------------------------------------------------------------
    function applyKeywordHighlight() {
      const searchInput = document.querySelector('.sidebar .search input');
      const query = searchInput ? searchInput.value.trim() : '';
      const content = document.querySelector('.markdown-section');
      
      if (content && typeof Mark !== 'undefined') {
        const markInstance = new Mark(content);
        markInstance.unmark({
          done: function() {
            if (query && query.length >= 1) {
              markInstance.mark(query, {
                className: 'search-keyword-highlight',
                separateWordSearch: false,
                acrossElements: true,
                done: function() {
                  const firstMatch = document.querySelector('.search-keyword-highlight');
                  if (firstMatch && searchInput && document.activeElement !== searchInput) {
                    firstMatch.scrollIntoView({ behavior: 'smooth', block: 'center' });
                  }
                }
              });
            }
          }
        });
      }
    }

    // --------------------------------------------------------------------------
    // Docsify Configuration with Collapsible Sidebar and Search Settings
    // --------------------------------------------------------------------------
    window.$docsify = {
      name: '1917 內外科看護學',
      repo: 'https://github.com/SinLiongToo/laigoakho_Tejinsiu_ebook',
      loadSidebar: true,
      subMaxLevel: 3,
      sidebarDisplayLevel: 1, // Collapse top-level volumes by default (expandable on click)
      coverpage: true,
      homepage: 'README.md',
      auto2top: true,
      search: {
        maxAge: 86400000,
        paths: 'auto',
        placeholder: '🔍 搜尋白話字、全漢字或英文 (如: kut, 骨)...',
        noData: '查無相符結果',
        depth: 6,
        hideOtherSidebarContent: false // Keep sidebar chapter tree intact and separated!
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
      },
      plugins: [
        function(hook, vm) {
          hook.afterEach(function(html, next) {
            // Bulletproof Image Resolver Plugin
            var basePath = window.location.pathname.replace(/\\/$/, '');
            var tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            
            var images = tempDiv.querySelectorAll('img');
            images.forEach(function(img) {
              var src = img.getAttribute('src');
              if (src && src.indexOf('assets/illustrations/') !== -1 && !src.startsWith('http')) {
                var filename = src.substring(src.indexOf('assets/illustrations/'));
                img.src = basePath + '/' + filename;
              }
            });
            next(tempDiv.innerHTML);
          });

          hook.doneEach(function() {
            applyKeywordHighlight();
            
            // Listen for search input typing to highlight keywords in real time
            const searchInput = document.querySelector('.sidebar .search input');
            if (searchInput && !searchInput.dataset.hasHighlightListener) {
              searchInput.dataset.hasHighlightListener = 'true';
              searchInput.addEventListener('input', () => {
                setTimeout(applyKeywordHighlight, 200);
              });
            }
          });
        }
      ]
    };
  </script>

  <!-- Docsify v4 Core & Essential Plugins -->
  <script src="//cdn.jsdelivr.net/npm/docsify@4"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify/lib/plugins/search.min.js"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify/lib/plugins/zoom-image.min.js"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify-sidebar-collapse/dist/docsify-sidebar-collapse.min.js"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify-copy-code/dist/docsify-copy-code.min.js"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify-pagination/dist/docsify-pagination.min.js"></script>
  <!-- Mark.js for Realtime In-Content Keyword Highlighting -->
  <script src="//cdn.jsdelivr.net/npm/mark.js@8.11.1/dist/mark.min.js"></script>
</body>
</html>
"""

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
    
    print("🔨 開始聚合章節 Markdown 文件至 docs/ (含插圖自動嵌入、字體更新與可折疊目錄)...")
    
    # Pre-defined clean volume grouping
    vol_display_names = {
        "00_Front_Matter": "📖 前言與凡例 (Front Matter)",
        "00_front_matter": "📖 前言與凡例 (Front Matter)",
        "01_Volume_1_Anatomy_Physiology": "🩺 第一篇 解剖學及生理學 (Kái-phò͘-ha̍k)",
        "01_volume_1_anatomy": "🩺 第一篇 解剖學及生理學 (Kái-phò͘-ha̍k)",
        "02_Volume_2_General_Nursing": "🏥 第二篇 普通看護學 (Phó͘-thong Khàn-hō͘-ha̍k)",
        "02_volume_2_nursing": "🏥 第二篇 普通看護學 (Phó͘-thong Khàn-hō͘-ha̍k)",
        "03_Volume_3_Surgical_Nursing": "🔪 第三篇 外科看護學 (Gōa-kho Khàn-hō͘-ha̍k)",
        "03_volume_3_surgery": "🔪 第三篇 外科看護學 (Gōa-kho Khàn-hō͘-ha̍k)",
        "04_Volume_4_Medical_Nursing": "💊 第四篇 內科看護學 (Lāi-kho Khàn-hō͘-ha̍k)",
        "04_volume_4_medicine": "💊 第四篇 內科看護學 (Lāi-kho Khàn-hō͘-ha̍k)",
        "05_Glossary": "📚 附錄一：醫學三語辭彙表 (GÚ-LŪI)",
        "05_glossary": "📚 附錄一：醫學三語辭彙表 (GÚ-LŪI)",
        "06_Index": "🔍 附錄二：總索引目錄 (SEK-ÍN)",
        "06_index": "🔍 附錄二：總索引目錄 (SEK-ÍN)"
    }
    
    sidebar_groups = defaultdict(list)
    total_words = 0
    total_pages_included = 0
    total_illustrations_embedded = 0
    
    for sec in sections:
        sec_id = sec["id"]
        sec_title = sec["title"]
        vol_key = sec.get("volume", "00_front_matter")
        vol_label = vol_display_names.get(vol_key, sec.get("volume_title", vol_key))
        target_file = sec["target_file"]
        target_path = os.path.join(DOCS_DIR, target_file)
        
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
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
            sidebar_groups[vol_label].append((sec_title, target_file))
        else:
            sidebar_groups[vol_label].append((sec_title, target_file))

    # Generate _sidebar.md with collapsible markdown structure
    sidebar_path = os.path.join(DOCS_DIR, "_sidebar.md")
    with open(sidebar_path, "w", encoding="utf-8") as f:
        f.write("* [🏠 首頁 (Home)](README.md)\n")
        f.write("* [📖 全書目錄 (Table of Contents)](00_front_matter/03_contents_and_rules.md)\n\n")
        
        for vol_label, items in sidebar_groups.items():
            f.write(f"* {vol_label}\n")
            for title, path in items:
                f.write(f"  * [{title}]({path})\n")
            f.write("\n")
        
    print(f"✅ 可折疊側邊導航已生成: {sidebar_path}")

    # Generate _coverpage.md
    coverpage_path = os.path.join(DOCS_DIR, "_coverpage.md")
    with open(coverpage_path, "w", encoding="utf-8") as f:
        f.write("""<div align="center">
<img src="assets/author_george_gushue_taylor.jpg" alt="戴仁壽醫師 (Dr. George Gushue-Taylor)" style="width: 140px; height: 140px; object-fit: cover; border-radius: 50%; border: 3px solid #2c7a7b; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />
</div>

# 1917 內外科看護學 <small>1.0</small>

> **The Principles and Practice of Nursing** (Lāi Gōa Kho Khàn-hō͘-ha̍k)  
> **著者**：戴仁壽 醫師 (Dr. George Gushue-Taylor, F.R.C.S., 1883–1954)  
> **合編**：陳大鑼 先生 (Tân Tāi-lô)  
> **題辭與序言**：甘為霖 牧師 (Rev. William Campbell)、蘭大衛 醫師 (Dr. David Landsborough)

- 台灣醫學史上第一部現代護理學與臨床醫學教科書
- 705 頁全書收錄：英文題辭序言、白話字正文 40 章、475 張原書醫學插圖、三語辭彙表與總索引
- 採用 Iansui 芫荽體與台文專屬字型組排版
- 採用 Gemini 3.7 Flash 深度視覺佈局辨識與逐段台漢對照
- 數位典藏建置：2026 年 @Tō͘ Sìn-liông

[開始閱讀 (Get Started)](README.md)
[GitHub 專案庫](https://github.com/SinLiongToo/laigoakho_Tejinsiu_ebook)
""")
    print(f"✅ 封面頁已生成: {coverpage_path}")

    # Generate docs/README.md
    readme_path = os.path.join(DOCS_DIR, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"""# 1917《內外科看護學》數位典藏電子書

<div align="center" style="margin: 20px 0 30px 0;">
  <img src="assets/author_george_gushue_taylor.jpg" alt="戴仁壽醫師 (Dr. George Gushue-Taylor)" style="width: 150px; height: 150px; object-fit: cover; border-radius: 50%; border: 3px solid #2c7a7b; box-shadow: 0 4px 14px rgba(0,0,0,0.15);" />
  <p style="font-size: 16px; margin-top: 10px; font-weight: 600;">原著者：戴仁壽 醫師 (Dr. George Gushue-Taylor, 1883–1954)</p>
  <p style="font-size: 14px; color: #718096; margin-top: -6px;">英國皇家外科醫學院院士 (F.R.C.S.)｜台南新樓醫院院長｜台北馬偕紀念醫院院長｜樂山園創辦人</p>
</div>

歡迎閱讀由 **戴仁壽醫師（Dr. George Gushue-Taylor）** 主編、陳大鑼先生合編之 **《內外科看護學》（The Principles and Practice of Nursing / Lāi Gōa Kho Khàn-hō͘-ha̍k）** 現代化數位電子書。

---

## 👨‍⚕️ 著者生平與歷史背景

**戴仁壽（George Gushue-Taylor，1883年12月6日－1954年4月23日）** 是一位來自加拿大紐芬蘭的醫療傳教醫師：

- **卓越醫術**：畢業於倫敦醫院醫學院，考取極具威望的英國皇家外科醫師學會院士（F.R.C.S.），曾榮獲婦科與解剖學大獎，被譽為日治時期全台灣學術與臨床醫術最高超的外科名醫之一。
- **編著本書**：1911 年抵達台灣行醫，有感於台灣缺乏本土護理專業人才與教材，於 1917 年在台南新樓醫院任內，與陳大鑼先生合作以**台語白話字（Pe̍h-ōe-jī）**編寫了這部高達 705 頁的巨著《內外科看護學》，成為台灣第一部現代臨床護理與解剖醫學專書。
- **奉獻痲瘋防治**：後轉任台北馬偕紀念醫院院長，並於 1934 年在新北八里創立「樂山園（Happy Mount Colony）」，打破當時官方強制隔離制度，給予病患有尊嚴的自治與自養環境。去世後遺骸歸葬於八里樂山療養院紀念園中。

---

## 🌟 本數位典藏電子書特色

1. **原作者尊崇與三語前言**：完整收錄戴仁壽醫師編撰體例、甘為霖牧師題辭、蘭大衛醫師英文序言、白話字頭序與現代華語三語對照。
2. **正文 40 章逐段對照**：全書 705 頁高精度白話字（POJ）與台語全漢字逐段並列。
3. **475 張醫學插圖完整嵌入**：自動裁切並高解析度還原人體解剖圖、外科器械與包紮繃帶插圖。
4. **醫學語彙辭典 (GÚ-LŪI)**：收錄書末珍貴的台語白話字、台語漢字與英語醫學專用術語三語辭典。
5. **台語典藏最佳化字型**：採用 **Iansui 芫荽體**、**HanaMin**、**Klee One** 與 **Noto Serif TC**，完美呈現白話字調號與漢字。
6. **現代化電子書閱讀體驗**：支援深色模式 (Dark Mode)、手機電腦響應式排版 (RWD)、側邊欄各篇折疊展開 (Collapsible Sidebar)、全文搜尋與目錄導覽。

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
*數位典藏建置年份：2026 年 @Tō͘ Sìn-liông*
""")
    print(f"✅ 首頁 README.md 已生成: {readme_path}")

    # Generate docs/index.html with full Dark Mode, Collapsible Sidebar and Bulletproof Image Resolver Plugin
    index_html_path = os.path.join(DOCS_DIR, "index.html")
    with open(index_html_path, "w", encoding="utf-8") as f:
        f.write(INDEX_HTML_TEMPLATE.strip())
    print(f"✅ Docsify Web 站點已更新: {index_html_path}")

if __name__ == "__main__":
    build_chapters()
