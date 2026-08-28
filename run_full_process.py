# -*- coding: utf-8 -*-
"""
Full-book automated pipeline runner:
Runs OCR on all 705 pages -> Builds docs/ eBook -> Calculates final stats.
"""

import sys
import subprocess

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.run_ocr_pipeline import run_pipeline
from src.build_book import build_chapters
from calculate_stats import calculate_stats

def main():
    print("🚀 [Step 1/3] 正在啟動 1917《內外科看護學》全書 705 頁 AI OCR 轉譯流水線...")
    # Run full book (pages 1 to 705) with gemini-3.7-flash
    run_pipeline(start_page=1, end_page=705, model="gemini-3.7-flash", delay=1.0)
    
    print("\n🔨 [Step 2/3] 正在聚合章節並生成 docs/ GitHub Pages 電子書...")
    build_chapters()
    
    print("\n📊 [Step 3/3] 正在產生全書最終統計報告...")
    calculate_stats()
    
    print("\n🎉🎉🎉 全書 705 頁數位化與電子書建置圓滿完成！")

if __name__ == "__main__":
    main()
