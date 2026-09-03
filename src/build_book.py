# -*- coding: utf-8 -*-
"""
Book & GitHub Pages Site Builder for 1917 Lai-goa-kho Tann-jin-siu.
Aggregates single-page raw OCR results into clean chapter Markdown files,
automatically embeds extracted illustrations/diagrams, compiles medical dictionary dataset,
and generates Docsify navigation + dual-mode eBook & Medical Dictionary SPA.
"""

import os
import sys
import json
import glob
import re
import unicodedata
from datetime import datetime
from collections import defaultdict, Counter

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

INDEX_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <title>1917 內外科看護學 - 台語白話字與全漢字數位電子書 ＆ 醫學台語辭典</title>
  <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1" />
  <meta name="description" content="1917 內外科看護學 (Lāi Gōa Kho Khàn-hō͘-ha̍k) 全書台語白話字 AI OCR、全漢字逐段對照、原書解剖插圖與醫學台英漢三語辭典">
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
      src: url('assets/fonts/Iansui-Regular.ttf') format('truetype'),
           url('https://cdn.jsdelivr.net/gh/ButTaiwan/iansui@main/fonts/ttf/Iansui-Regular.ttf') format('truetype'),
           url('https://raw.githubusercontent.com/ButTaiwan/iansui/main/fonts/ttf/Iansui-Regular.ttf') format('truetype');
      font-weight: normal;
      font-style: normal;
      font-display: swap;
    }

    @font-face {
      font-family: 'POJ-Fallback';
      src: local('Helvetica Neue'), local('Helvetica'), local('Arial'), local('Roboto'), local('Segoe UI');
      unicode-range: U+0020-007F, U+00A0-024F, U+0300-036F, U+2070-209F;
    }

    /* ==========================================================================
       CSS Variables & Themes (Light / Dark)
       ========================================================================== */
    :root {
      --font-zh: 'POJ-Fallback', 'Iansui', 'HanaMinA', 'HanaMinB', 'HanaMin', 'Klee One', 'Noto Serif TC', 'PingFang TC', 'Heiti TC', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Microsoft JhengHei", sans-serif;
      --font-en: 'POJ-Fallback', 'Roboto', -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      
      --theme-color: #2c7a7b;
      --theme-accent: #319795;
      
      /* Light Mode Variables */
      --bg-primary: #ffffff;
      --bg-secondary: #f8fafc;
      --bg-sidebar: #f8fafc;
      --card-bg: #ffffff;
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
      --badge-bg: #e6fffa;
      --badge-text: #234e52;
    }

    [data-theme="dark"] {
      /* Dark Mode Variables */
      --bg-primary: #0b0f19;
      --bg-secondary: #131b2e;
      --bg-sidebar: #111827;
      --card-bg: #1e293b;
      --text-primary: #ffffff;
      --text-secondary: #f3f4f6;
      --text-muted: #cbd5e1;
      --border-color: #374151;
      --blockquote-bg: #131c2e;
      --blockquote-border: #2dd4bf;
      --table-th-bg: #1f2937;
      --card-shadow: 0 4px 16px rgba(0, 0, 0, 0.45);
      --code-bg: #1f2937;
      --sidebar-toggle-bg: #1f2937;
      --badge-bg: #134e4a;
      --badge-text: #ccfbf1;
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
      margin: 0;
      padding: 0;
      transition: background-color 0.3s ease, color 0.3s ease;
      -webkit-font-smoothing: antialiased;
    }

    /* ==========================================================================
       Floating Dual Mode Switcher & Dark Mode Toggle
       ========================================================================== */
    .top-floating-bar {
      position: fixed;
      top: 14px;
      right: 18px;
      z-index: 10000;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .site-mode-switcher {
      display: flex;
      background-color: var(--bg-secondary);
      border: 1.5px solid var(--border-color);
      border-radius: 24px;
      padding: 3px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.12);
    }

    .mode-tab-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border: none;
      background: transparent;
      color: var(--text-secondary);
      font-family: var(--font-zh);
      font-size: 14px;
      font-weight: 600;
      border-radius: 20px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .mode-tab-btn.active {
      background-color: var(--theme-color);
      color: #ffffff !important;
      box-shadow: 0 2px 8px rgba(44, 122, 123, 0.35);
    }

    #theme-toggle-btn {
      background-color: var(--bg-secondary);
      color: var(--text-primary);
      border: 1px solid var(--border-color);
      border-radius: 50%;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 2px 10px rgba(0,0,0,0.15);
      transition: all 0.25s ease;
      font-size: 18px;
      user-select: none;
    }

    #theme-toggle-btn:hover {
      transform: scale(1.08);
      border-color: var(--theme-color);
    }

    /* ==========================================================================
       Docsify eBook Layout
       ========================================================================== */
    .markdown-section {
      max-width: 900px;
      padding: 30px 24px 80px 24px !important;
      color: var(--text-primary) !important;
      font-family: var(--font-zh) !important;
    }

    .markdown-section p, 
    .markdown-section li {
      color: var(--text-primary) !important;
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

    /* Blockquotes */
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

    .markdown-section blockquote p,
    .markdown-section blockquote strong {
      margin: 6px 0;
      color: var(--text-primary) !important;
    }

    /* High-Contrast Tables */
    .markdown-section table {
      width: 100% !important;
      border-collapse: collapse !important;
      margin: 20px 0 !important;
      display: table !important;
      border: 1.5px solid var(--border-color) !important;
      background-color: var(--bg-primary) !important;
      border-radius: 8px;
    }

    .markdown-section table th {
      background-color: #edf2f7 !important;
      color: #0f172a !important;
      font-weight: 700 !important;
      padding: 11px 14px !important;
      border: 1px solid #cbd5e1 !important;
      white-space: nowrap;
      font-family: var(--font-zh) !important;
      text-align: left !important;
    }

    .markdown-section table tr {
      background-color: #ffffff !important;
      border-top: 1px solid #e2e8f0 !important;
    }

    .markdown-section table tr:nth-child(2n) {
      background-color: #f8fafc !important;
    }

    .markdown-section table td {
      padding: 10px 14px !important;
      border: 1px solid #e2e8f0 !important;
      color: #1e293b !important;
      font-family: var(--font-zh) !important;
    }

    [data-theme="dark"] .markdown-section table {
      background-color: #0b0f19 !important;
      border: 1.5px solid #374151 !important;
    }

    [data-theme="dark"] .markdown-section table th {
      background-color: #1e293b !important;
      color: #ffffff !important;
      font-weight: 700 !important;
      border: 1px solid #475569 !important;
    }

    [data-theme="dark"] .markdown-section table tr,
    [data-theme="dark"] .markdown-section table tr:nth-child(odd) {
      background-color: #0e1726 !important;
      border-top: 1px solid #374151 !important;
    }

    [data-theme="dark"] .markdown-section table tr:nth-child(2n),
    [data-theme="dark"] .markdown-section table tr:nth-child(even) {
      background-color: #1e293b !important;
    }

    [data-theme="dark"] .markdown-section table tr:hover {
      background-color: #334155 !important;
    }

    [data-theme="dark"] .markdown-section table td {
      color: #ffffff !important;
      border: 1px solid #374151 !important;
    }

    /* Coverpage */
    section.cover {
      background: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 50%, #f8fafc 100%) !important;
      position: relative !important;
    }
    section.cover .cover-main {
      color: #0f172a !important;
      font-family: var(--font-zh) !important;
    }
    section.cover .cover-main h1 {
      color: #0f172a !important;
      font-weight: 800;
    }
    section.cover .cover-main blockquote,
    section.cover .cover-main blockquote p {
      color: #1e293b !important;
      font-size: 16px;
      line-height: 1.7;
    }
    section.cover .cover-main ul li {
      color: #334155 !important;
      text-align: left;
      font-size: 15px;
      margin-bottom: 6px;
    }
    section.cover .cover-main a.button {
      background-color: var(--theme-color) !important;
      color: #ffffff !important;
      border: 1px solid var(--theme-color) !important;
      font-weight: 600;
      border-radius: 8px;
    }
    section.cover .cover-main a.button:last-child {
      background-color: transparent !important;
      color: var(--theme-color) !important;
      border: 1.5px solid var(--theme-color) !important;
    }

    [data-theme="dark"] section.cover {
      background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #0f172a 100%) !important;
    }
    [data-theme="dark"] section.cover .cover-main {
      color: #ffffff !important;
    }
    [data-theme="dark"] section.cover .cover-main h1 {
      color: #ffffff !important;
      text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    [data-theme="dark"] section.cover .cover-main blockquote,
    [data-theme="dark"] section.cover .cover-main blockquote p {
      color: #e2e8f0 !important;
      background: rgba(19, 27, 46, 0.7) !important;
      border-left: 4px solid #2dd4bf !important;
    }
    [data-theme="dark"] section.cover .cover-main ul li {
      color: #cbd5e1 !important;
    }
    [data-theme="dark"] section.cover .cover-main a.button {
      background-color: #2dd4bf !important;
      color: #0b0f19 !important;
      border: 1px solid #2dd4bf !important;
      font-weight: 700;
      box-shadow: 0 4px 14px rgba(45, 212, 191, 0.25);
    }
    [data-theme="dark"] section.cover .cover-main a.button:last-child {
      background-color: #1e293b !important;
      color: #f8fafc !important;
      border: 1px solid #475569 !important;
    }

    [data-theme="dark"] .markdown-section {
      color: #f8fafc !important;
    }
    [data-theme="dark"] .markdown-section h1,
    [data-theme="dark"] .markdown-section h2,
    [data-theme="dark"] .markdown-section h3,
    [data-theme="dark"] .markdown-section h4 {
      color: #ffffff !important;
      border-color: #374151 !important;
    }
    [data-theme="dark"] .markdown-section p,
    [data-theme="dark"] .markdown-section li,
    [data-theme="dark"] .markdown-section span,
    [data-theme="dark"] .markdown-section strong {
      color: #f8fafc !important;
    }
    [data-theme="dark"] .markdown-section a {
      color: #38bdf8 !important;
    }
    [data-theme="dark"] .markdown-section a:hover {
      color: #67e8f9 !important;
      text-decoration: underline;
    }

    /* Sidebar */
    .sidebar {
      background-color: var(--bg-sidebar) !important;
      border-right: 1.5px solid var(--border-color) !important;
      color: var(--text-primary) !important;
      font-size: 15px;
      font-family: var(--font-zh) !important;
      transition: all 0.3s ease;
      padding: 0 0 40px 0;
    }

    .sidebar-nav li.open > ul {
      display: block !important;
    }
    .sidebar-nav li.collapse > ul {
      display: none !important;
    }

    @media screen and (min-width: 769px) {
      .sidebar {
        width: 360px !important;
      }
      .content {
        left: 360px !important;
        position: absolute !important;
        right: 0 !important;
        top: 0 !important;
        bottom: 0 !important;
        transition: left 0.3s ease;
      }
      body.close .content {
        left: 0 !important;
      }
      body.close .sidebar {
        transform: translateX(-360px) !important;
      }
    }

    .sidebar ul li a {
      color: var(--text-secondary) !important;
      padding: 7px 12px;
      border-radius: 6px;
      display: block;
      font-family: var(--font-zh) !important;
      font-size: 14.5px;
      line-height: 1.55;
      white-space: normal !important;
      word-break: break-word !important;
    }

    .sidebar ul li.active > a,
    .sidebar ul li a:hover {
      color: var(--theme-color) !important;
      background-color: var(--border-color);
      font-weight: 600;
    }

    [data-theme="dark"] .sidebar ul li.active > a {
      color: #2dd4bf !important;
      background-color: #1f2937 !important;
      font-weight: 700;
    }

    .sidebar .folder {
      cursor: pointer;
      font-weight: 700;
      color: var(--text-primary) !important;
      padding: 10px 10px 8px 10px;
      display: block;
      user-select: none;
      white-space: normal !important;
      word-break: break-word !important;
      line-height: 1.5;
    }

    /* Scrollbars */
    .sidebar::-webkit-scrollbar,
    body::-webkit-scrollbar,
    .content::-webkit-scrollbar,
    .markdown-section table::-webkit-scrollbar,
    .dict-content::-webkit-scrollbar,
    .dict-sidebar::-webkit-scrollbar {
      width: 11px !important;
      height: 11px !important;
    }

    .sidebar::-webkit-scrollbar-track,
    body::-webkit-scrollbar-track,
    .content::-webkit-scrollbar-track,
    .dict-content::-webkit-scrollbar-track,
    .dict-sidebar::-webkit-scrollbar-track {
      background: var(--bg-secondary) !important;
      border-radius: 6px;
    }

    .sidebar::-webkit-scrollbar-thumb,
    body::-webkit-scrollbar-thumb,
    .content::-webkit-scrollbar-thumb,
    .dict-content::-webkit-scrollbar-thumb,
    .dict-sidebar::-webkit-scrollbar-thumb {
      background: #94a3b8 !important;
      border-radius: 6px;
      border: 2.5px solid var(--bg-secondary) !important;
    }

    .sidebar::-webkit-scrollbar-thumb:hover,
    body::-webkit-scrollbar-thumb:hover,
    .content::-webkit-scrollbar-thumb:hover,
    .dict-content::-webkit-scrollbar-thumb:hover,
    .dict-sidebar::-webkit-scrollbar-thumb:hover {
      background: var(--theme-color) !important;
    }

    [data-theme="dark"] .sidebar::-webkit-scrollbar-thumb,
    [data-theme="dark"] body::-webkit-scrollbar-thumb,
    [data-theme="dark"] .content::-webkit-scrollbar-thumb,
    [data-theme="dark"] .dict-content::-webkit-scrollbar-thumb,
    [data-theme="dark"] .dict-sidebar::-webkit-scrollbar-thumb {
      background: #64748b !important;
      border-color: #111827 !important;
    }

    .sidebar-collapse-toolbar {
      padding: 4px 14px 10px 14px;
      border-bottom: 1px solid var(--border-color);
      margin-bottom: 6px;
    }

    .collapse-all-btn {
      width: 100%;
      padding: 7px 10px;
      background-color: var(--bg-primary);
      color: var(--text-primary);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      font-size: 13.5px;
      font-family: var(--font-zh);
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s ease;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    .collapse-all-btn:hover {
      border-color: var(--theme-color);
      background-color: var(--blockquote-bg);
      color: var(--theme-color);
    }

    /* eBook Sidebar Search */
    .sidebar .search {
      position: relative;
      border-bottom: 1px solid var(--border-color) !important;
      padding: 12px 14px 8px 14px;
      margin-bottom: 4px;
    }

    .sidebar .search .input-wrap {
      display: flex;
      align-items: center;
      position: relative;
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

    .sidebar .search .clear-button {
      cursor: pointer;
      position: absolute;
      right: 8px;
      display: none;
    }

    .sidebar .search .clear-button.show {
      display: block;
    }

    .app-name.hide,
    .sidebar-nav.hide {
      display: none !important;
    }

    .sidebar:has(.results-panel.show) .sidebar-collapse-toolbar {
      display: none !important;
    }

    .sidebar .results-panel {
      display: none;
      padding: 10px 4px;
      margin-top: 8px;
    }

    .sidebar .results-panel.show {
      display: block !important;
    }

    .sidebar .results-panel .matching-post {
      border-bottom: 1px solid var(--border-color);
      padding: 10px 8px;
      margin-bottom: 8px;
      border-radius: 6px;
      transition: background-color 0.2s ease;
    }

    .sidebar .results-panel .matching-post:hover {
      background-color: var(--blockquote-bg);
    }

    .sidebar .results-panel .matching-post:last-child {
      border-bottom: none;
    }

    .sidebar .results-panel h2 {
      font-size: 14.5px;
      color: var(--theme-color) !important;
      margin: 2px 0 6px 0;
      font-weight: 700;
    }

    [data-theme="dark"] .sidebar .results-panel h2 {
      color: #38bdf8 !important;
    }

    .sidebar .results-panel p {
      font-size: 13px;
      color: var(--text-secondary) !important;
      line-height: 1.6;
      margin: 0;
    }

    [data-theme="dark"] .sidebar .results-panel p {
      color: #cbd5e1 !important;
    }

    .sidebar .results-panel p.empty {
      text-align: center;
      padding: 24px 0;
      color: var(--text-muted) !important;
      font-size: 14px;
    }

    mark.search-keyword-highlight,
    .search-keyword-highlight {
      background-color: #fef08a !important;
      color: #1e293b !important;
      padding: 2px 4px !important;
      border-radius: 3px !important;
      font-weight: 700 !important;
      border-bottom: 2px solid #eab308 !important;
    }

    [data-theme="dark"] mark.search-keyword-highlight,
    [data-theme="dark"] .search-keyword-highlight {
      background-color: #ca8a04 !important;
      color: #0b0f19 !important;
      border-bottom: 2px solid #facc15 !important;
    }

    /* ==========================================================================
       Medical Dictionary SPA Layout (#dict-app)
       ========================================================================== */
    #dict-app {
      display: none;
      position: fixed;
      inset: 0;
      width: 100vw;
      height: 100vh;
      background-color: var(--bg-primary);
      z-index: 999;
    }

    .dict-sidebar {
      width: 360px;
      background-color: var(--bg-sidebar);
      border-right: 1.5px solid var(--border-color);
      height: 100%;
      overflow-y: auto;
      flex-shrink: 0;
      padding: 20px 18px 60px 18px;
      display: flex;
      flex-direction: column;
      box-sizing: border-box;
    }

    .dict-header {
      font-size: 1.25em;
      font-weight: 700;
      color: var(--text-primary);
      margin-bottom: 2px;
    }

    .dict-sub {
      font-size: 0.85em;
      color: var(--text-muted);
      margin-bottom: 12px;
    }

    .dict-mode-tabs {
      display: flex;
      gap: 6px;
      margin-bottom: 14px;
    }

    .dict-tab-btn {
      flex: 1;
      text-align: center;
      padding: 8px 4px;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      background-color: var(--bg-primary);
      color: var(--text-primary);
      cursor: pointer;
      font-size: 0.88em;
      font-weight: 600;
      font-family: var(--font-zh);
      transition: all 0.2s ease;
    }

    .dict-tab-btn.active {
      background-color: var(--theme-color);
      color: #ffffff;
      border-color: var(--theme-color);
    }

    .dict-search-box {
      width: 100%;
      padding: 10px 14px;
      border-radius: 8px;
      border: 1.5px solid var(--border-color);
      background-color: var(--bg-primary);
      color: var(--text-primary);
      font-family: var(--font-zh);
      font-size: 0.95em;
      box-sizing: border-box;
      margin-bottom: 6px;
      outline: none;
      transition: border-color 0.2s;
    }

    .dict-search-box:focus {
      border-color: var(--theme-color);
      box-shadow: 0 0 0 3px rgba(44, 122, 123, 0.2);
    }

    .dict-search-tips {
      font-size: 0.74em;
      color: var(--text-muted);
      margin-bottom: 12px;
      line-height: 1.4;
    }

    .dict-filter-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      margin-bottom: 12px;
    }

    .filter-pill {
      flex: 1 1 calc(33.33% - 5px);
      min-width: 68px;
      padding: 5px 2px;
      font-size: 0.74em;
      font-weight: 600;
      border-radius: 6px;
      border: 1px solid var(--border-color);
      background-color: var(--bg-primary);
      color: var(--text-secondary);
      cursor: pointer;
      text-align: center;
      transition: all 0.15s;
    }

    .filter-pill.active {
      background-color: var(--theme-accent);
      color: #ffffff;
      border-color: var(--theme-accent);
    }

    .dict-freq-badge {
      font-size: 0.72em;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 12px;
      background-color: rgba(234, 88, 12, 0.12);
      color: #ea580c;
      border: 1px solid rgba(234, 88, 12, 0.3);
      white-space: nowrap;
    }

    [data-theme="dark"] .dict-freq-badge {
      background-color: rgba(251, 146, 60, 0.15);
      color: #fb923c;
      border-color: rgba(251, 146, 60, 0.35);
    }

    .dict-stat-line {
      font-size: 0.8em;
      color: var(--text-secondary);
      font-weight: 600;
      margin-bottom: 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .dict-sort-btn {
      background: none;
      border: none;
      color: var(--theme-color);
      font-size: 0.9em;
      cursor: pointer;
      text-decoration: underline;
      font-family: var(--font-zh);
      padding: 0;
    }

    .letter-grid {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 5px;
      margin-bottom: 16px;
    }

    .letter-btn {
      padding: 6px 0;
      text-align: center;
      background-color: var(--bg-primary);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.82em;
      color: var(--text-primary);
      transition: all 0.15s;
    }

    .letter-btn:hover {
      background-color: var(--blockquote-bg);
      border-color: var(--theme-color);
      color: var(--theme-color);
    }

    .letter-btn.active {
      background-color: var(--theme-color);
      color: #ffffff;
      border-color: var(--theme-color);
    }

    .dict-content {
      flex-grow: 1;
      overflow-y: auto;
      padding: 30px 40px 80px 40px;
      background-color: var(--bg-primary);
      box-sizing: border-box;
    }

    .dict-content-inner {
      max-width: 1000px;
      margin: 0 auto;
    }

    .dict-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 14px;
    }

    .dict-card {
      background-color: var(--card-bg);
      border: 1.5px solid var(--border-color);
      border-radius: 12px;
      padding: 16px 18px;
      box-shadow: var(--card-shadow);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: transform 0.15s ease, border-color 0.15s ease;
    }

    .dict-card:hover {
      transform: translateY(-3px);
      border-color: var(--theme-color);
    }

    .dict-card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 6px;
    }

    .dict-card-poj {
      font-size: 1.3em;
      font-weight: 700;
      color: var(--theme-color);
      line-height: 1.3;
    }

    [data-theme="dark"] .dict-card-poj {
      color: #2dd4bf;
    }

    .dict-badge {
      font-size: 0.72em;
      padding: 2px 7px;
      border-radius: 12px;
      background-color: var(--badge-bg);
      color: var(--badge-text);
      font-weight: 600;
      white-space: nowrap;
    }

    .dict-card-han {
      font-size: 1.15em;
      font-weight: 700;
      color: var(--text-primary);
      margin-bottom: 4px;
    }

    .dict-card-eng {
      font-size: 0.95em;
      color: var(--text-secondary);
      font-style: italic;
      margin-bottom: 8px;
      font-family: var(--font-en);
    }

    .dict-card-notes {
      font-size: 0.85em;
      color: var(--text-muted);
      margin-bottom: 12px;
      line-height: 1.5;
    }

    .dict-card-footer {
      border-top: 1px dashed var(--border-color);
      padding-top: 10px;
      margin-top: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.82em;
    }

    .dict-page-ref {
      color: var(--text-muted);
    }

    .dict-jump-btn {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background-color: var(--bg-secondary);
      border: 1px solid var(--border-color);
      color: var(--theme-color);
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.85em;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      transition: all 0.2s;
    }

    .dict-jump-btn:hover {
      background-color: var(--theme-color);
      color: #ffffff;
      border-color: var(--theme-color);
    }

    /* User Manual Styles */
    .manual-lang-tabs {
      display: flex;
      gap: 10px;
      margin-bottom: 24px;
      border-bottom: 2px solid var(--border-color);
      padding-bottom: 10px;
    }

    .manual-lang-btn {
      padding: 8px 18px;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      background-color: var(--bg-secondary);
      color: var(--text-primary);
      font-weight: 700;
      font-size: 0.95em;
      cursor: pointer;
      font-family: var(--font-zh);
    }

    .manual-lang-btn.active {
      background-color: var(--theme-color);
      color: #ffffff;
      border-color: var(--theme-color);
    }

    .manual-section {
      background-color: var(--card-bg);
      border: 1.5px solid var(--border-color);
      border-radius: 12px;
      padding: 24px 28px;
      margin-bottom: 24px;
      box-shadow: var(--card-shadow);
    }

    .manual-section h2 {
      color: var(--theme-color);
      margin-top: 0;
      font-size: 1.35em;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 10px;
    }

    [data-theme="dark"] .manual-section h2 {
      color: #2dd4bf;
    }

    .manual-section h3 {
      font-size: 1.1em;
      margin: 18px 0 8px 0;
      color: var(--text-primary);
    }

    .manual-section p, 
    .manual-section li {
      color: var(--text-primary);
      font-size: 0.95em;
      line-height: 1.8;
    }

    .manual-code {
      display: inline-block;
      background-color: var(--bg-secondary);
      border: 1px solid var(--border-color);
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 700;
      color: var(--theme-color);
    }

    /* Mobile Responsive for Dictionary */
    @media screen and (max-width: 768px) {
      .top-floating-bar {
        top: 10px;
        right: 12px;
      }
      .mode-tab-btn {
        padding: 5px 10px;
        font-size: 12.5px;
      }
      #theme-toggle-btn {
        width: 34px;
        height: 34px;
        font-size: 15px;
      }
      #dict-app {
        flex-direction: column;
      }
      .dict-sidebar {
        width: 100%;
        height: auto;
        max-height: 48vh;
        border-right: none;
        border-bottom: 1.5px solid var(--border-color);
        padding: 14px 14px 14px 14px;
      }
      .dict-content {
        height: 52vh;
        padding: 16px 14px 60px 14px;
      }
      .dict-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <!-- Top Floating Controls: Dual Mode Switcher & Dark Mode Toggle -->
  <div class="top-floating-bar">
    <div class="site-mode-switcher">
      <button id="mode-btn-ebook" class="mode-tab-btn active" title="進入電子書閱讀模式">📖 電子書模式</button>
      <button id="mode-btn-dict" class="mode-tab-btn" title="進入醫學台語辭典模式">📚 字典模式</button>
    </div>
    <button id="theme-toggle-btn" title="切換深色/淺色模式" aria-label="Toggle Dark Mode">🌙</button>
  </div>

  <!-- eBook Container (Docsify Mount) -->
  <div id="ebook-container">
    <div id="app">正在載入《內外科看護學》圖文電子書...</div>
  </div>

  <!-- Medical Dictionary SPA Container (#dict-app) -->
  <div id="dict-app">
    <div class="dict-sidebar">
      <div class="dict-header">1917 內外科看護學</div>
      <div class="dict-sub">台英漢醫學辭典 · GÚ-LŪI & SEK-ÍN</div>
      
      <div class="dict-mode-tabs">
        <button id="dict-tab-search-btn" class="dict-tab-btn active">🔍 詞典檢索</button>
        <button id="dict-tab-help-btn" class="dict-tab-btn">📖 使用手冊</button>
      </div>

      <div id="dict-search-controls">
        <input type="text" id="dict-search-input" class="dict-search-box" placeholder="🔍 搜尋 漢字 / 白話字 / 英文 / 頁碼..." />
        <div class="dict-search-tips">💡 支援：漢字 (喉頭)、白話字 (âu-thâu, kut)、英文 (Larynx)、原書頁碼 (378)</div>
        
        <div class="dict-filter-pills">
          <button class="filter-pill active" data-scope="all">全部 <span id="pill-count-all">(0)</span></button>
          <button class="filter-pill" data-scope="s1">一語 (單字) <span id="pill-count-s1">(0)</span></button>
          <button class="filter-pill" data-scope="s2">二語 (雙字詞) <span id="pill-count-s2">(0)</span></button>
          <button class="filter-pill" data-scope="s3">三語 (三字詞) <span id="pill-count-s3">(0)</span></button>
          <button class="filter-pill" data-scope="s4">四語 (四字詞) <span id="pill-count-s4">(0)</span></button>
          <button class="filter-pill" data-scope="glossary">三語語彙 <span id="pill-count-glossary">(0)</span></button>
          <button class="filter-pill" data-scope="index">總索引 <span id="pill-count-index">(0)</span></button>
        </div>

        <div class="dict-stat-line">
          <span id="dict-stat-count">正在載入詞條...</span>
          <button id="dict-sort-toggle" class="dict-sort-btn">🔥 依頻率排序</button>
        </div>

        <div class="letter-grid" id="dict-letter-grid"></div>
      </div>
    </div>

    <div class="dict-content">
      <div class="dict-content-inner">
        <!-- Dictionary Search Result View -->
        <div id="dict-search-view">
          <div class="dict-grid" id="dict-cards-container"></div>
          <div id="dict-load-more" style="text-align: center; margin-top: 24px; display: none;">
            <button id="btn-load-more" style="padding: 8px 24px; border-radius: 8px; border: 1px solid var(--theme-color); background: var(--bg-secondary); color: var(--theme-color); font-weight: 700; cursor: pointer;">載入更多詞條...</button>
          </div>
        </div>

        <!-- Dictionary User Manual View -->
        <div id="dict-help-view" style="display: none;">
          <div class="manual-lang-tabs">
            <button id="manual-btn-han" class="manual-lang-btn active">🇹🇼 全漢使用手冊</button>
            <button id="manual-btn-poj" class="manual-lang-btn">📜 Choân Pe̍h-ōe-jī Chhiú-chheh (全羅白話字手冊)</button>
          </div>

          <!-- Han-ji Manual -->
          <div id="manual-content-han">
            <div class="manual-section">
              <h2>📖 1917《內外科看護學》醫學詞典緣起與體例</h2>
              <p>本書詞典資料庫完整收錄自 1917 年戴仁壽醫師（Dr. George Gushue-Taylor）編著之《內外科看護學》書末兩大珍貴附錄：</p>
              <ul>
                <li><strong>附錄一：醫學三語辭彙表（GÚ-LŪI）</strong>：收錄 1,019 條專業醫學辭彙，並列「台語白話字（POJ）」、「台語全漢字」與「英文專業醫學術語（English Medical Terms）」。</li>
                <li><strong>附錄二：總索引目錄（SEK-ÍN）</strong>：收錄 1,606 條臨床名詞與原書詳細對應頁碼，完整貫串全書 40 章臨床解剖與護理技術。</li>
              </ul>
            </div>

            <div class="manual-section">
              <h2>🔍 四向即時檢索指南</h2>
              <p>本辭典支援強大的多語模糊即時檢索，您可以於搜尋框直接輸入：</p>
              <ul>
                <li><strong>台語漢字</strong>：例如輸入 <span class="manual-code">喉頭</span>、<span class="manual-code">骨</span>、<span class="manual-code">心臟</span>、<span class="manual-code">麻醉</span>。</li>
                <li><strong>白話字（POJ）/ 台羅</strong>：例如輸入 <span class="manual-code">âu-thâu</span>、<span class="manual-code">kut</span>、<span class="manual-code">chhùi</span>、<span class="manual-code">bâ-chùi</span>。</li>
                <li><strong>去聲調模糊搜尋</strong>：例如輸入 <span class="manual-code">au-thau</span>、<span class="manual-code">ho-khip</span>、<span class="manual-code">sim-chong</span>（無需輸入聲調符號亦可精確比對）。</li>
                <li><strong>英文醫學名詞</strong>：例如輸入 <span class="manual-code">Larynx</span>、<span class="manual-code">Bone</span>、<span class="manual-code">Mitral</span>、<span class="manual-code">Anæsthetic</span>。</li>
                <li><strong>原書頁碼</strong>：例如輸入 <span class="manual-code">378</span>、<span class="manual-code">664</span>，可直接檢索該頁所出現之所有專業醫學詞彙。</li>
              </ul>
            </div>

            <div class="manual-section">
              <h2>🔤 字母快速導覽與範圍篩選</h2>
              <ul>
                <li><strong>字母快捷鍵</strong>：點擊左側字母列（如 <span class="manual-code">A</span>、<span class="manual-code">CH</span>、<span class="manual-code">K</span>、<span class="manual-code">O͘</span>、<span class="manual-code">PH</span>），即可依白話字開頭字母快速篩選詞條。</li>
                <li><strong>範圍標籤</strong>：可切換【全部】、【三語語彙】與【總索引】三個資料集。</li>
                <li><strong>排序切換</strong>：點擊「依字母排序」或「依頁碼排序」，方便按字母順序或書籍篇章順序瀏覽。</li>
              </ul>
            </div>

            <div class="manual-section">
              <h2>🚀 一鍵跳轉至電子書章節</h2>
              <p>每張詞條卡片右下方皆附有 <strong>「📖 閱讀原書第 X 頁」</strong> 按鈕。點擊後系統會<strong>自動由字典模式切換至電子書模式</strong>，並精準定位至該頁所屬章節與對應段落，方便您立即對照上下文與高清解剖插圖！</p>
            </div>
          </div>

          <!-- POJ Manual -->
          <div id="manual-content-poj" style="display: none;">
            <div class="manual-section">
              <h2>📖 1917 Lāi-gōa-kho Khàn-hō͘-ha̍k I-ha̍k Sû-tián Goân-iû</h2>
              <p>Pún sû-tián chu-liāu-khò͘ sī uì 1917 nî Tè Jîn-siū I-seng (Dr. George Gushue-Taylor) só͘ pian-tì ê 《Lāi Gōa Kho Khàn-hō͘-ha̍k》 chheh-bóe nn̄g hāng tiōng-iàu hù-lio̍k só͘ chè-chō：</p>
              <ul>
                <li><strong>Hù-lio̍k I: I-ha̍k Saⁿ-gí Gú-lūi (GÚ-LŪI)</strong>: Siu-lio̍k 1,019 tiâu choan-gia̍p i-ha̍k sû-lūi, pēng-lia̍t Pe̍h-ōe-jī (POJ), Choân Hàn-jī kap Eng-bûn (English Medical Terms).</li>
                <li><strong>Hù-lio̍k II: Chóng Sek-ín Bo̍k-lio̍k (SEK-ÍN)</strong>: Siu-lio̍k 1,606 tiâu lîm-tshn̂g bêng-sû kap goân-chheh ia̍h-bé, thàu-kòe choân-chheh 40 chiuⁿ ê kái-phò͘ kap khàn-hō͘ ki-sut.</li>
              </ul>
            </div>

            <div class="manual-section">
              <h2>🔍 Sù-hiòng Chhiau-chhōe Chi-lâm</h2>
              <p>Pún sû-tián chi-chhî to-gí bô-hō͘ chhiau-chhōe, lí ē-sái ti̍t-chiap ji̍p-kháu：</p>
              <ul>
                <li><strong>Tâi-gí Hàn-jī</strong>: Pí-jû <span class="manual-code">喉頭</span>, <span class="manual-code">骨</span>, <span class="manual-code">心臟</span>, <span class="manual-code">麻醉</span>.</li>
                <li><strong>Pe̍h-ōe-jī (POJ) / Tâi-lô</strong>: Pí-jû <span class="manual-code">âu-thâu</span>, <span class="manual-code">kut</span>, <span class="manual-code">chhùi</span>, <span class="manual-code">bâ-chùi</span>.</li>
                <li><strong>Bô-tiāu-hō Bô͘-hô͘ Chhiau-chhōe</strong>: Pí-jû <span class="manual-code">au-thau</span>, <span class="manual-code">ho-khip</span>, <span class="manual-code">sim-chong</span>.</li>
                <li><strong>Eng-bûn I-ha̍k Bêng-sû</strong>: Pí-jû <span class="manual-code">Larynx</span>, <span class="manual-code">Bone</span>, <span class="manual-code">Mitral</span>.</li>
                <li><strong>Goân-chheh Ia̍h-bé</strong>: Pí-jû <span class="manual-code">378</span>, <span class="manual-code">664</span>.</li>
              </ul>
            </div>

            <div class="manual-section">
              <h2>🔤 Jī-bó Khoài-sú Kòe-lī kap Pâi-lia̍t</h2>
              <ul>
                <li><strong>Jī-bó Khoài-chia̍t-kiān</strong>: Tiám tò-pêng jī-bó (pí-jû <span class="manual-code">A</span>, <span class="manual-code">CH</span>, <span class="manual-code">K</span>, <span class="manual-code">O͘</span>, <span class="manual-code">PH</span>), tō ē-sái khoài-sú kòe-lī sû-tiâu.</li>
                <li><strong>Hoān-uî Piau-chhiam</strong>: Ē-sái chhiat-oaⁿ 【Choân-pō͘】, 【Saⁿ-gí Gú-lūi】 kap 【Chóng Sek-ín】.</li>
                <li><strong>Pâi-lia̍t Chhiat-oaⁿ</strong>: Tiám "I-chiàu Jī-bó" he̍k "I-chiàu Ia̍h-bé" lâi sūn-sū liú-lám.</li>
              </ul>
            </div>

            <div class="manual-section">
              <h2>🚀 Chi̍t-kiān Thiàu-choán kàu Tiān-chú-chheh</h2>
              <p>Muí chi̍t tiuⁿ sû-tiâu khah-phìⁿ chià-ē-pêng lóng ū <strong>「📖 Tha̍k Goân-chheh Tē X Ia̍h」</strong> ê liân-kiat. Tiám liáu-āu hē-thóng ē <strong>chū-tōng uì Sû-tián bô͘-sek chhiat-oaⁿ kàu Tiān-chú-chheh bô͘-sek</strong>, pēng-chhiáⁿ chún-khak tēng-ūi kàu hit ia̍h ê phian-chiuⁿ kap kái-phò͘ tô͘-phìⁿ！</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Inline Dictionary Data for Instant 0ms Load -->
  <script id="dict-data" type="application/json">__DICT_JSON_DATA__</script>
  <script src="assets/dictionary_data.js"></script>

  <script>
    // --------------------------------------------------------------------------
    // Theme Management (Dark Mode / Light Mode)
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
    // Dual Site Mode Switching: eBook Mode 📖 ⇋ Dictionary Mode 📚
    // --------------------------------------------------------------------------
    let currentSiteMode = 'ebook';

    function switchSiteMode(mode) {
      currentSiteMode = mode;
      const btnEbook = document.getElementById('mode-btn-ebook');
      const btnDict = document.getElementById('mode-btn-dict');
      const ebookContainer = document.getElementById('ebook-container');
      const dictApp = document.getElementById('dict-app');

      if (mode === 'dict') {
        if (btnEbook) btnEbook.classList.remove('active');
        if (btnDict) btnDict.classList.add('active');
        if (ebookContainer) ebookContainer.style.display = 'none';
        if (dictApp) dictApp.style.display = 'flex';
        renderDictionary();
      } else {
        if (btnDict) btnDict.classList.remove('active');
        if (btnEbook) btnEbook.classList.add('active');
        if (dictApp) dictApp.style.display = 'none';
        if (ebookContainer) ebookContainer.style.display = 'block';
      }
    }

    function jumpToEbook(targetPath, pageNum) {
      switchSiteMode('ebook');
      if (targetPath) {
        window.location.hash = '#/' + targetPath;
        setTimeout(() => {
          if (pageNum) {
            const pageAnchor = Array.from(document.querySelectorAll('h4, .markdown-section h4')).find(h => h.textContent.includes('原書第 ' + pageNum + ' 頁') || h.textContent.includes('第 ' + pageNum + ' 頁'));
            if (pageAnchor) {
              pageAnchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
          }
        }, 400);
      }
    }

    // --------------------------------------------------------------------------
    // Medical Dictionary SPA Logic
    // --------------------------------------------------------------------------
    let dictAllEntries = [];
    let dictFilteredEntries = [];
    let dictSelectedScope = 'all';
    let dictSelectedLetter = 'ALL';
    let dictSortMode = 'freq'; // 'freq' | 'letter' | 'page'
    let dictCurrentPage = 1;
    const DICT_PAGE_SIZE = 90;

    function initDictionary() {
      if (dictAllEntries.length === 0) {
        try {
          const dataEl = document.getElementById('dict-data');
          if (dataEl && dataEl.textContent.trim()) {
            dictAllEntries = JSON.parse(dataEl.textContent);
          } else if (window.LAIGOAKHO_DICT_DATA && Array.isArray(window.LAIGOAKHO_DICT_DATA)) {
            dictAllEntries = window.LAIGOAKHO_DICT_DATA;
          }
        } catch(e) {
          console.error('Failed to parse dictionary data:', e);
        }
      }
      
      // Update scope counts
      const countAll = dictAllEntries.length;
      const countS1 = dictAllEntries.filter(e => e.type === 's1').length;
      const countS2 = dictAllEntries.filter(e => e.type === 's2').length;
      const countS3 = dictAllEntries.filter(e => e.type === 's3').length;
      const countS4 = dictAllEntries.filter(e => e.type === 's4').length;
      const countGlossary = dictAllEntries.filter(e => e.is_glossary).length;
      const countIndex = dictAllEntries.filter(e => e.is_index).length;
      
      const elAll = document.getElementById('pill-count-all');
      const elS1 = document.getElementById('pill-count-s1');
      const elS2 = document.getElementById('pill-count-s2');
      const elS3 = document.getElementById('pill-count-s3');
      const elS4 = document.getElementById('pill-count-s4');
      const elGlo = document.getElementById('pill-count-glossary');
      const elIdx = document.getElementById('pill-count-index');
      if (elAll) elAll.textContent = '(' + countAll.toLocaleString() + ')';
      if (elS1) elS1.textContent = '(' + countS1.toLocaleString() + ')';
      if (elS2) elS2.textContent = '(' + countS2.toLocaleString() + ')';
      if (elS3) elS3.textContent = '(' + countS3.toLocaleString() + ')';
      if (elS4) elS4.textContent = '(' + countS4.toLocaleString() + ')';
      if (elGlo) elGlo.textContent = '(' + countGlossary.toLocaleString() + ')';
      if (elIdx) elIdx.textContent = '(' + countIndex.toLocaleString() + ')';

      // Build Alphabet Letter Buttons
      buildLetterGrid();
      
      // Bind Events
      const searchInput = document.getElementById('dict-search-input');
      if (searchInput) {
        searchInput.addEventListener('input', () => {
          dictCurrentPage = 1;
          applyDictFilter();
        });
      }

      // Filter pills
      document.querySelectorAll('.filter-pill').forEach(btn => {
        btn.addEventListener('click', (e) => {
          document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          dictSelectedScope = btn.dataset.scope || 'all';
          dictCurrentPage = 1;
          applyDictFilter();
        });
      });

      // Sort toggle
      const sortBtn = document.getElementById('dict-sort-toggle');
      if (sortBtn) {
        sortBtn.addEventListener('click', () => {
          if (dictSortMode === 'freq') {
            dictSortMode = 'letter';
            sortBtn.textContent = '🔤 依字母排序';
          } else if (dictSortMode === 'letter') {
            dictSortMode = 'page';
            sortBtn.textContent = '📄 依頁碼排序';
          } else {
            dictSortMode = 'freq';
            sortBtn.textContent = '🔥 依頻率排序';
          }
          dictCurrentPage = 1;
          applyDictFilter();
        });
      }

      // Sub-tabs: Search vs Help
      const tabSearch = document.getElementById('dict-tab-search-btn');
      const tabHelp = document.getElementById('dict-tab-help-btn');
      const viewSearch = document.getElementById('dict-search-view');
      const viewHelp = document.getElementById('dict-help-view');
      const searchControls = document.getElementById('dict-search-controls');

      if (tabSearch && tabHelp) {
        tabSearch.addEventListener('click', () => {
          tabSearch.classList.add('active');
          tabHelp.classList.remove('active');
          if (viewSearch) viewSearch.style.display = 'block';
          if (viewHelp) viewHelp.style.display = 'none';
          if (searchControls) searchControls.style.display = 'block';
        });

        tabHelp.addEventListener('click', () => {
          tabHelp.classList.add('active');
          tabSearch.classList.remove('active');
          if (viewSearch) viewSearch.style.display = 'none';
          if (viewHelp) viewHelp.style.display = 'block';
          if (searchControls) searchControls.style.display = 'none';
        });
      }

      // Manual Language tabs
      const btnManHan = document.getElementById('manual-btn-han');
      const btnManPoj = document.getElementById('manual-btn-poj');
      const manContentHan = document.getElementById('manual-content-han');
      const manContentPoj = document.getElementById('manual-content-poj');

      if (btnManHan && btnManPoj) {
        btnManHan.addEventListener('click', () => {
          btnManHan.classList.add('active');
          btnManPoj.classList.remove('active');
          if (manContentHan) manContentHan.style.display = 'block';
          if (manContentPoj) manContentPoj.style.display = 'none';
        });
        btnManPoj.addEventListener('click', () => {
          btnManPoj.classList.add('active');
          btnManHan.classList.remove('active');
          if (manContentHan) manContentHan.style.display = 'none';
          if (manContentPoj) manContentPoj.style.display = 'block';
        });
      }

      // Load more button
      const btnLoadMore = document.getElementById('btn-load-more');
      if (btnLoadMore) {
        btnLoadMore.addEventListener('click', () => {
          dictCurrentPage++;
          renderCardsSlice(true);
        });
      }

      applyDictFilter();
    }

    function buildLetterGrid() {
      const container = document.getElementById('dict-letter-grid');
      if (!container) return;
      const letters = ['ALL', 'A', 'B', 'CH', 'CHH', 'E', 'G', 'H', 'I', 'J', 'K', 'KH', 'L', 'M', 'N', 'NG', 'O', 'O͘', 'P', 'PH', 'S', 'T', 'TH', 'U'];
      
      container.innerHTML = letters.map(l => `
        <button class="letter-btn ${l === dictSelectedLetter ? 'active' : ''}" data-letter="${l}">${l}</button>
      `).join('');

      container.querySelectorAll('.letter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          container.querySelectorAll('.letter-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          dictSelectedLetter = btn.dataset.letter;
          dictCurrentPage = 1;
          applyDictFilter();
        });
      });
    }

    function cleanDiacritics(str) {
      if (!str) return '';
      return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/o͘|o\u0358/g, 'o').replace(/[-\s,]+/g, '');
    }

    function applyDictFilter() {
      const searchInput = document.getElementById('dict-search-input');
      const rawQuery = searchInput ? searchInput.value.trim() : '';
      const cleanQ = cleanDiacritics(rawQuery);

      dictFilteredEntries = dictAllEntries.filter(item => {
        // Scope filter
        if (dictSelectedScope === 's1' && item.type !== 's1') return false;
        if (dictSelectedScope === 's2' && item.type !== 's2') return false;
        if (dictSelectedScope === 's3' && item.type !== 's3') return false;
        if (dictSelectedScope === 's4' && item.type !== 's4') return false;
        if (dictSelectedScope === 'glossary' && !item.is_glossary) return false;
        if (dictSelectedScope === 'index' && !item.is_index) return false;

        // Letter filter
        if (dictSelectedLetter !== 'ALL') {
          if (item.letter !== dictSelectedLetter) return false;
        }

        // Search query filter
        if (cleanQ) {
          const matchPoj = cleanDiacritics(item.poj).includes(cleanQ);
          const matchHan = item.han && item.han.includes(rawQuery);
          const matchEng = item.eng && cleanDiacritics(item.eng).includes(cleanQ);
          const matchNotes = item.notes && item.notes.includes(rawQuery);
          const matchPage = String(item.page) === rawQuery || (item.refs && item.refs.some(r => String(r.page) === rawQuery));
          if (!matchPoj && !matchHan && !matchEng && !matchNotes && !matchPage) {
            return false;
          }
        }

        return true;
      });

      // Sort
      if (dictSortMode === 'freq') {
        dictFilteredEntries.sort((a, b) => (b.freq || 1) - (a.freq || 1) || a.clean.localeCompare(b.clean));
      } else if (dictSortMode === 'page') {
        dictFilteredEntries.sort((a, b) => a.page - b.page || (b.freq || 1) - (a.freq || 1));
      } else {
        dictFilteredEntries.sort((a, b) => a.clean.localeCompare(b.clean));
      }

      // Update counter
      const statCount = document.getElementById('dict-stat-count');
      if (statCount) {
        statCount.textContent = `顯示 ${dictFilteredEntries.length.toLocaleString()} / ${dictAllEntries.length.toLocaleString()} 條目`;
      }

      renderCardsSlice(false);
    }

    function renderCardsSlice(append = false) {
      const container = document.getElementById('dict-cards-container');
      const loadMoreDiv = document.getElementById('dict-load-more');
      if (!container) return;

      const totalToShow = dictCurrentPage * DICT_PAGE_SIZE;
      const slice = dictFilteredEntries.slice(0, totalToShow);

      if (slice.length === 0) {
        container.innerHTML = `
          <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--text-muted);">
            <div style="font-size: 2.5em; margin-bottom: 10px;">🔍</div>
            <div style="font-size: 1.1em; font-weight: 700;">查無相符的醫學詞目</div>
            <div style="font-size: 0.9em; margin-top: 6px;">請嘗試切換篩選分類、字母分組或擴大搜尋條件。</div>
          </div>
        `;
        if (loadMoreDiv) loadMoreDiv.style.display = 'none';
        return;
      }

      const cardsHtml = slice.map(item => {
        const refPages = item.refs && item.refs.length > 0
          ? item.refs.slice(0, 6).map(r => `<a href="javascript:void(0)" onclick="jumpToEbook('${r.target}', ${r.page})" class="dict-jump-btn" title="跳轉至原書第 ${r.page} 頁">📖 第 ${r.page} 頁</a>`).join(' ')
          : `<a href="javascript:void(0)" onclick="jumpToEbook('${item.target}', ${item.page})" class="dict-jump-btn" title="跳轉至原書第 ${item.page} 頁">📖 第 ${item.page} 頁</a>`;

        const freqBadge = (item.freq && item.freq > 1)
          ? `<span class="dict-freq-badge" title="全書出現 ${item.freq} 次，涵蓋 ${item.page_count || 1} 頁">🔥 ${item.freq.toLocaleString()} 次 (${item.page_count || 1} 頁)</span>`
          : '';

        return `
          <div class="dict-card">
            <div>
              <div class="dict-card-header">
                <div class="dict-card-poj">${item.poj}</div>
                <div style="display: flex; gap: 5px; align-items: center; flex-wrap: wrap; justify-content: flex-end;">
                  ${freqBadge}
                  <span class="dict-badge">${item.type_name}</span>
                </div>
              </div>
              ${item.han ? `<div class="dict-card-han">${item.han}</div>` : ''}
              ${item.eng ? `<div class="dict-card-eng">${item.eng}</div>` : ''}
              ${item.notes ? `<div class="dict-card-notes">${item.notes}</div>` : ''}
            </div>
            <div class="dict-card-footer">
              <span class="dict-page-ref">原書出處：</span>
              <div style="display: flex; flex-wrap: wrap; gap: 4px;">${refPages}</div>
            </div>
          </div>
        `;
      }).join('');

      container.innerHTML = cardsHtml;

      if (loadMoreDiv) {
        loadMoreDiv.style.display = totalToShow < dictFilteredEntries.length ? 'block' : 'none';
      }
    }

    function renderDictionary() {
      if (dictAllEntries.length === 0) {
        initDictionary();
      } else {
        applyDictFilter();
      }
    }

    // Handle initial URL hash or mode buttons
    window.addEventListener('DOMContentLoaded', () => {
      const btnEbook = document.getElementById('mode-btn-ebook');
      const btnDict = document.getElementById('mode-btn-dict');
      if (btnEbook) btnEbook.addEventListener('click', () => switchSiteMode('ebook'));
      if (btnDict) btnDict.addEventListener('click', () => switchSiteMode('dict'));

      if (window.location.hash.startsWith('#/dict') || window.location.hash.startsWith('#/dictionary')) {
        switchSiteMode('dict');
      }

      initDictionary();
    });

    // --------------------------------------------------------------------------
    // One-Click Sidebar Collapse / Expand Functionality
    // --------------------------------------------------------------------------
    let isAllExpanded = false;
    function toggleAllSidebarChapters() {
      isAllExpanded = !isAllExpanded;
      
      const listItems = document.querySelectorAll('.sidebar-nav li');
      listItems.forEach(li => {
        const childUl = li.querySelector('ul');
        if (childUl) {
          if (isAllExpanded) {
            li.classList.add('open');
            li.classList.remove('collapse');
          } else {
            li.classList.remove('open');
            li.classList.add('collapse');
          }
        }
      });
      
      const icon = document.getElementById('collapse-icon');
      const text = document.getElementById('collapse-text');
      if (icon && text) {
        icon.textContent = isAllExpanded ? '📁' : '📂';
        text.textContent = isAllExpanded ? '一鍵全部收合' : '一鍵全部展開';
      }
    }

    function injectSidebarCollapseButton() {
      const searchBox = document.querySelector('.sidebar .search');
      if (searchBox && !document.querySelector('.sidebar-collapse-toolbar')) {
        const toolbar = document.createElement('div');
        toolbar.className = 'sidebar-collapse-toolbar';
        toolbar.innerHTML = `
          <button id="btn-collapse-all" class="collapse-all-btn" title="一鍵全部展開 / 全部收合所有篇章">
            <span id="collapse-icon">📂</span> <span id="collapse-text">一鍵全部展開</span>
          </button>
        `;
        searchBox.insertAdjacentElement('afterend', toolbar);
        const btn = document.getElementById('btn-collapse-all');
        if (btn) {
          btn.addEventListener('click', toggleAllSidebarChapters);
        }
      }
    }

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
      sidebarDisplayLevel: 1,
      coverpage: true,
      homepage: 'README.md',
      auto2top: true,
      search: {
        maxAge: 86400000,
        paths: 'auto',
        namespace: 'laigoakho_v5',
        placeholder: '🔍 搜尋白話字、全漢字或英文 (如: kut, 骨)...',
        noData: '查無相符結果',
        depth: 6,
        hideOtherSidebarContent: true
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
          hook.init(function() {
            try {
              for (var k in localStorage) {
                if (k.startsWith('docsify.search') && !k.includes('laigoakho_v5')) {
                  localStorage.removeItem(k);
                }
              }
            } catch(e) {}
          });

          hook.afterEach(function(html, next) {
            var basePath = window.location.pathname.replace(/\/$/, '');
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
            injectSidebarCollapseButton();
            applyKeywordHighlight();
            
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

def normalize_han_punctuation(text: str) -> str:
    """
    Normalizes text to standard Unicode NFC (precomposed) and converts
    half-width punctuation to standard full-width punctuation marks.
    """
    text = unicodedata.normalize('NFC', text)
    lines = text.split("\n")
    out_lines = []
    
    for line in lines:
        if line.startswith(">"):
            if line.startswith("> **【全漢對照") or line.startswith("> **所屬篇章") or line.startswith("> **原書頁碼"):
                out_lines.append(line)
                continue
            
            l = line
            l = re.sub(r'([\u4e00-\u9fff\w\)])\s*:\s*', r'\1：', l)
            l = re.sub(r'([\u4e00-\u9fff\w\)])\s*;\s*', r'\1；', l)
            l = re.sub(r'([\u4e00-\u9fff])\s*,\s*', r'\1，', l)
            l = re.sub(r',\s*([\u4e00-\u9fff])', r'，\1', l)
            l = re.sub(r'([\u4e00-\u9fff\)])\s*\.\s*(?!\d)', r'\1。', l)
            l = re.sub(r'([\u4e00-\u9fff])\s*\?\s*', r'\1？', l)
            l = re.sub(r'([\u4e00-\u9fff])\s*!\s*', r'\1！', l)
            l = l.replace('[', '［').replace(']', '］')
            l = re.sub(r'\(([\u4e00-\u9fff][^)]*)\)', r'（\1）', l)
            l = re.sub(r'\(([^)]*[\u4e00-\u9fff])\)', r'（\1）', l)
            l = l.replace('~', '～')
            out_lines.append(l)
        else:
            out_lines.append(line)
            
    return "\n".join(out_lines)

def load_book_structure():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_page_illustrations(page_num: int) -> list:
    ill_cache = os.path.join(ILLUSTRATION_CACHE_DIR, f"page_{page_num:03d}.json")
    if os.path.exists(ill_cache):
        try:
            with open(ill_cache, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("figures", [])
        except Exception:
            pass
    return []

def clean_tone(text):
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower().replace('o͘', 'o').replace('o\u0358', 'o').replace('-', ' ').replace(',', ' ').strip()

def get_first_letter(poj):
    p = poj.strip()
    p_upper = p.upper()
    for prefix in ['CHH', 'CH', 'KH', 'PH', 'TH', 'NG']:
        if p_upper.startswith(prefix):
            return prefix
    if p.startswith('O͘') or p.startswith('o͘') or p.startswith('O\u0358') or p.startswith('o\u0358') or p_upper.startswith('O·'):
        return 'O͘'
    c = p[0]
    c_norm = unicodedata.normalize('NFD', c)
    c_clean = ''.join(ch for ch in c_norm if unicodedata.category(ch) != 'Mn').upper()
    if c_clean.isalpha():
        return c_clean
    return '#'

def generate_dictionary_dataset():
    """Extracts all vocabulary from the entire 705-page corpus + GÚ-LŪI + SEK-ÍN into a structured JSON dataset."""
    print("📚 正在編譯全書 705 頁全語料庫大辭典（含一語、二語、三語、四語與附錄語彙/索引）...")
    book_structure = load_book_structure()
    page_map = {}
    for sec in book_structure["sections"]:
        for p in range(sec["start_page"], sec["end_page"] + 1):
            page_map[p] = {
                "target": sec["target_file"].replace(".md", ""),
                "title": sec["title"]
            }

    # 1. Parse Glossary (GÚ-LŪI)
    glossary_map = {}
    glossary_entries = []
    glossary_path = os.path.join(DOCS_DIR, "05_glossary/medical_glossary.md")
    if os.path.exists(glossary_path):
        with open(glossary_path, "r", encoding="utf-8") as f:
            cur_p = 664
            for line in f:
                m = re.search(r"原書第\s*(\d+)\s*頁", line)
                if m:
                    cur_p = int(m.group(1))
                if "|" in line and not line.strip().startswith("| :") and not "白話字" in line:
                    cols = [c.strip() for c in line.split("|")[1:-1]]
                    if len(cols) >= 3 and cols[0]:
                        poj = cols[0].rstrip(",").strip()
                        han = cols[1].strip()
                        eng = cols[2].rstrip(".").strip()
                        notes = cols[3].strip() if len(cols) > 3 else ""
                        clean_k = clean_tone(poj)
                        item = {
                            "poj": poj,
                            "han": han,
                            "eng": eng,
                            "notes": notes,
                            "page": cur_p,
                            "type": "glossary",
                            "type_name": "三語辭彙"
                        }
                        glossary_entries.append(item)
                        if clean_k and clean_k not in glossary_map:
                            glossary_map[clean_k] = item

    # 2. Parse General Index (SEK-ÍN)
    index_map = {}
    index_entries = []
    index_path = os.path.join(DOCS_DIR, "06_index/general_index.md")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            cur_p = 695
            for line in f:
                m = re.search(r"原書第\s*(\d+)\s*頁", line)
                if m:
                    cur_p = int(m.group(1))
                if "|" in line and not line.strip().startswith("| :") and not "索引詞條" in line:
                    cols = [c.strip() for c in line.split("|")[1:-1]]
                    if len(cols) >= 3 and cols[0]:
                        poj = cols[0].rstrip(",").strip()
                        han = cols[1].strip()
                        p_str = cols[2].strip()
                        clean_k = clean_tone(poj)
                        refs = []
                        for num_m in re.finditer(r"\d+", p_str):
                            p_num = int(num_m.group(0))
                            pm = page_map.get(p_num, {"target": "README", "title": ""})
                            refs.append({"page": p_num, "target": pm["target"]})
                        item = {
                            "poj": poj,
                            "han": han,
                            "page": cur_p,
                            "type": "index",
                            "type_name": "總索引",
                            "refs": refs
                        }
                        index_entries.append(item)
                        if clean_k and clean_k not in index_map:
                            index_map[clean_k] = item

    # 3. Extract all POJ tokens from 705 pages cache
    poj_pattern = re.compile(r"[a-zA-Z\u00C0-\u024F\u0300-\u036F\u1E00-\u1EFF\u207F\u00B7\u0358]+(?:-[a-zA-Z\u00C0-\u024F\u0300-\u036F\u1E00-\u1EFF\u207F\u00B7\u0358]+)*")

    word_counts = Counter()
    word_pages = defaultdict(set)
    word_case_variants = defaultdict(Counter)

    cache_files = glob.glob(os.path.join(CACHE_DIR, "page_*.json"))
    for fpath in cache_files:
        m = re.search(r"page_(\d+)", fpath)
        if not m:
            continue
        p_num = int(m.group(1))
        with open(fpath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                text = data.get("text", "")
                for line in text.split("\n"):
                    line_str = line.strip()
                    if not line_str or line_str.startswith(">") or line_str.startswith("#"):
                        continue
                    words = poj_pattern.findall(line_str)
                    for w in words:
                        w_norm = unicodedata.normalize("NFC", w.strip(".,;:!?\"'()[]"))
                        if len(w_norm) >= 1 and not w_norm.isdigit() and not w_norm.startswith("http"):
                            lower_k = w_norm.lower()
                            word_counts[lower_k] += 1
                            word_pages[lower_k].add(p_num)
                            word_case_variants[lower_k][w_norm] += 1
            except Exception:
                pass

    # 4. Assemble Unified Vocabulary Entries
    entries = []
    eid = 1
    seen_keys = set()

    for lower_k, count in word_counts.most_common():
        best_variant = word_case_variants[lower_k].most_common(1)[0][0]
        clean_k = clean_tone(lower_k)
        s_count = len(lower_k.split("-"))
        
        syllable_type = "s1" if s_count == 1 else "s2" if s_count == 2 else "s3" if s_count == 3 else "s4" if s_count == 4 else "s_multi"
        syllable_name = "一語" if s_count == 1 else "二語" if s_count == 2 else "三語" if s_count == 3 else "四語" if s_count == 4 else f"{s_count}語"

        g_info = glossary_map.get(clean_k)
        i_info = index_map.get(clean_k)
        
        han = g_info["han"] if g_info else (i_info["han"] if i_info else "")
        eng = g_info["eng"] if g_info else ""
        notes = g_info["notes"] if g_info else ""
        
        pages_list = sorted(list(word_pages[lower_k]))
        first_p = pages_list[0] if pages_list else 1
        pm = page_map.get(first_p, {"target": "README", "title": ""})
        
        refs = []
        for p_num in pages_list[:8]:
            p_info = page_map.get(p_num, {"target": "README", "title": ""})
            refs.append({"page": p_num, "target": p_info["target"]})

        type_name = syllable_name
        if g_info and i_info:
            type_name = f"{syllable_name} · 語彙/索引"
        elif g_info:
            type_name = f"{syllable_name} · 三語語彙"
        elif i_info:
            type_name = f"{syllable_name} · 總索引"

        entries.append({
            "id": eid,
            "poj": best_variant,
            "clean": clean_k,
            "han": han,
            "eng": eng,
            "notes": notes,
            "page": first_p,
            "freq": count,
            "page_count": len(pages_list),
            "type": syllable_type,
            "is_glossary": g_info is not None,
            "is_index": i_info is not None,
            "type_name": type_name,
            "letter": get_first_letter(best_variant),
            "target": pm["target"],
            "ch_title": pm["title"],
            "refs": refs
        })
        seen_keys.add(clean_k)
        eid += 1

    # Add remaining GÚ-LŪI terms
    for g in glossary_entries:
        clean_k = clean_tone(g["poj"])
        if clean_k not in seen_keys:
            s_count = len(g["poj"].split("-"))
            syllable_type = "s1" if s_count == 1 else "s2" if s_count == 2 else "s3" if s_count == 3 else "s4" if s_count == 4 else "s_multi"
            syllable_name = "一語" if s_count == 1 else "二語" if s_count == 2 else "三語" if s_count == 3 else "四語" if s_count == 4 else f"{s_count}語"
            pm = page_map.get(g["page"], {"target": "05_glossary/medical_glossary", "title": "語彙 GÚ-LŪI"})
            entries.append({
                "id": eid,
                "poj": g["poj"],
                "clean": clean_k,
                "han": g["han"],
                "eng": g["eng"],
                "notes": g["notes"],
                "page": g["page"],
                "freq": 1,
                "page_count": 1,
                "type": syllable_type,
                "is_glossary": True,
                "is_index": False,
                "type_name": f"{syllable_name} · 三語語彙",
                "letter": get_first_letter(g["poj"]),
                "target": pm["target"],
                "ch_title": pm["title"],
                "refs": [{"page": g["page"], "target": pm["target"]}]
            })
            seen_keys.add(clean_k)
            eid += 1

    # Add remaining SEK-ÍN terms
    for idx_item in index_entries:
        clean_k = clean_tone(idx_item["poj"])
        if clean_k not in seen_keys:
            s_count = len(idx_item["poj"].split("-"))
            syllable_type = "s1" if s_count == 1 else "s2" if s_count == 2 else "s3" if s_count == 3 else "s4" if s_count == 4 else "s_multi"
            syllable_name = "一語" if s_count == 1 else "二語" if s_count == 2 else "三語" if s_count == 3 else "四語" if s_count == 4 else f"{s_count}語"
            pm = page_map.get(idx_item["page"], {"target": "06_index/general_index", "title": "總索引 SEK-ÍN"})
            entries.append({
                "id": eid,
                "poj": idx_item["poj"],
                "clean": clean_k,
                "han": idx_item["han"],
                "eng": "",
                "notes": "",
                "page": idx_item["page"],
                "freq": 1,
                "page_count": len(idx_item.get("refs", [])) or 1,
                "type": syllable_type,
                "is_glossary": False,
                "is_index": True,
                "type_name": f"{syllable_name} · 總索引",
                "letter": get_first_letter(idx_item["poj"]),
                "target": pm["target"],
                "ch_title": pm["title"],
                "refs": idx_item.get("refs", [])
            })
            seen_keys.add(clean_k)
            eid += 1

    assets_dir = os.path.join(DOCS_DIR, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    dict_js_path = os.path.join(assets_dir, "dictionary_data.js")
    with open(dict_js_path, "w", encoding="utf-8") as f:
        f.write("window.LAIGOAKHO_DICT_DATA = " + json.dumps(entries, ensure_ascii=False) + ";")
    print(f"✅ 全語料醫學台語大辭典資料集已生成: {dict_js_path} (共 {len(entries):,} 筆詞條)")
    return entries

def build_chapters():
    book_structure = load_book_structure()
    sections = book_structure["sections"]
    
    print("🔨 開始聚合章節 Markdown 文件至 docs/...")
    
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
            chapter_chunks = []
            
            # Chapter header
            chapter_chunks.append(f"# {sec_title}\n\n")
            if "volume_title" in sec:
                chapter_chunks.append(f"> **所屬篇章**：{sec['volume_title']}\n")
            chapter_chunks.append(f"> **原書頁碼**：第 {start_p} 頁 ～ 第 {end_p} 頁 (已收錄 {len(chapter_pages)}/{end_p - start_p + 1} 頁)\n\n")
            chapter_chunks.append("---\n\n")
            
            for p_num, p_text, p_figs in chapter_pages:
                chapter_chunks.append(f"<!-- Page {p_num:03d} Start -->\n")
                chapter_chunks.append(f"#### 📖 原書第 {p_num} 頁\n\n")
                
                # Embed illustrations if present
                if p_figs:
                    chapter_chunks.append("\n<div align=\"center\" style=\"margin: 24px 0;\">\n\n")
                    for idx, fig in enumerate(p_figs):
                        fig_fn = fig.get("saved_file") or f"page_{p_num:03d}_fig_{idx+1:02d}.png"
                        fig_rel = f"assets/illustrations/{fig_fn}"
                        caption = fig.get("caption", "").strip()
                        alt_label = f"原書插圖 - 第 {p_num} 頁 (圖 {idx+1})"
                        chapter_chunks.append(f"![{alt_label}]({fig_rel})\n\n")
                        if caption:
                            chapter_chunks.append(f"<p class=\"figure-caption\"><em>{caption}</em></p>\n\n")
                        total_illustrations_embedded += 1
                    chapter_chunks.append("</div>\n\n")
                    
                p_text_norm = normalize_han_punctuation(p_text)
                chapter_chunks.append(p_text_norm.strip())
                chapter_chunks.append(f"\n\n<!-- Page {p_num:03d} End -->\n\n---\n\n")
                total_words += len(p_text_norm)
                
            full_chapter_text = unicodedata.normalize('NFC', "".join(chapter_chunks))
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(full_chapter_text)
                
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

    today_str = datetime.now().strftime("%Y-%m-%d")

    # Generate _coverpage.md
    coverpage_path = os.path.join(DOCS_DIR, "_coverpage.md")
    with open(coverpage_path, "w", encoding="utf-8") as f:
        f.write(f"""<div align="center">
<img src="assets/author_george_gushue_taylor.jpg" alt="戴仁壽醫師 (Dr. George Gushue-Taylor)" style="width: 140px; height: 140px; object-fit: cover; border-radius: 50%; border: 3px solid #2c7a7b; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />
</div>

# 1917 內外科看護學 <small>1.0</small>

> **The Principles and Practice of Nursing** (Lāi Gōa Kho Khàn-hō͘-ha̍k)  
> **著者**：戴仁壽 醫師 (Dr. George Gushue-Taylor, F.R.C.S., 1883–1954)  
> **協作**：陳大鑼 先生 (Tân Tāi-lô) 等多位台灣醫界與教會前輩  
> **序言**：戴仁壽 醫師 親撰英文序言 (English Preface) 與 白話字頭序 (Thâu-sū)

- 台灣醫學史上第一部現代護理學與臨床醫學教科書
- 705 頁全書收錄：英文題辭序言、白話字正文 40 章、475 張原書醫學插圖、三語辭彙表與總索引
- 採用 Iansui 芫荽體與台文專屬字型組排版
- 採用 Gemini 3.7 Flash 深度視覺佈局辨識與逐段台漢對照
- 數位典藏建置：2026 年 @Tō͘ Sìn-liông（最後更新：{today_str}）

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
  <p class="author-title" style="font-size: 14px; margin-top: -6px;">英國皇家外科醫學院院士 (F.R.C.S.)｜台南新樓醫院院長｜台北馬偕紀念醫院院長｜樂山園創辦人</p>
</div>

歡迎閱讀由 **戴仁壽醫師（Dr. George Gushue-Taylor）** 主編、陳大鑼先生等台灣醫界前輩合編之 **《內外科看護學》（The Principles and Practice of Nursing / Lāi Gōa Kho Khàn-hō͘-ha̍k）** 現代化數位電子書。

---

## 👨‍⚕️ 著者生平與歷史背景

**戴仁壽（George Gushue-Taylor，1883年12月6日－1954年4月23日）** 是一位來自加拿大紐芬蘭的醫療傳教醫師：

- **卓越醫術**：畢業於倫敦醫院醫學院，考取極具威望的英國皇家外科醫師學會院士（F.R.C.S.），曾榮獲婦科與解剖學大獎，被譽為日治時期全台灣學術與臨床醫術最高超的外科名醫之一。
- **編著本書**：1911 年抵達台灣行醫，有感於台灣缺乏本土護理專業人才與教材，於 1917 年在台南新樓醫院任內，與陳大鑼先生合作以**台語白話字（Pe̍h-ōe-jī）**編寫了這部高達 705 頁的巨著《內外科看護學》，成為台灣第一部現代臨床護理與解剖醫學專書。
- **奉獻痲瘋防治**：後轉任台北馬偕紀念醫院院長，並於 1934 年在新北八里創立「樂山園（Happy Mount Colony）」，打破當時官方強制隔離制度，給予病患有尊嚴的自治與自養環境。去世後遺骸歸葬於八里樂山療養院紀念園中。

---

## 🌟 本數位典藏電子書特色

1. **著者原著與完整三語前言**：完整收錄戴仁壽醫師英文獻詞（Dedication）、英文序言（English Preface）、白話字頭序（Thâu-sū）與現代華語三語對照。
2. **正文 40 章逐段對照**：全書 705 頁高精度白話字（POJ）與台語全漢字逐段並列。
3. **475 張醫學插圖完整嵌入**：自動裁切並高解析度還原人體解剖圖、外科器械與包紮繃帶插圖。
4. **醫學語彙辭典 (GÚ-LŪI)**：收錄書末珍貴的台語白話字、台語漢字與英語醫學專用術語三語辭典。
5. **台語典藏最佳化字型**：採用 **Iansui 芫荽體**、**HanaMin**、**Klee One** 與 **Noto Serif TC**，完美呈現白話字調號與漢字。
6. **現代化雙模式閱讀體驗**：支援【📖 電子書模式】與【📚 醫學台語辭典模式】隨時一鍵切換，支援深色模式 (Dark Mode)、手機電腦響應式排版 (RWD) 與全文搜尋。

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
*數位典藏建置：2026 年 @Tō͘ Sìn-liông ｜ 最後更新日期：{today_str}*
""")
    print(f"✅ 首頁 README.md 已生成: {readme_path}")

    # Generate Dictionary Dataset
    dict_entries = generate_dictionary_dataset()

    # Generate docs/index.html with inline dictionary JSON
    index_html_path = os.path.join(DOCS_DIR, "index.html")
    dict_json_str = json.dumps(dict_entries, ensure_ascii=False)
    final_html = INDEX_HTML_TEMPLATE.replace("__DICT_JSON_DATA__", dict_json_str)
    with open(index_html_path, "w", encoding="utf-8") as f:
        f.write(final_html.strip())
    print(f"✅ 雙模式 Docsify Web 與 醫學台語辭典 站點已更新: {index_html_path}")

if __name__ == "__main__":
    build_chapters()
