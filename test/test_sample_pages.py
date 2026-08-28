# -*- coding: utf-8 -*-
"""
Sample testing script for 1917 Lai-goa-kho Tann-jin-siu.
Tests 4 distinct page types: English Preface, Taiwanese Thau-su, Anatomy chapter, Glossary.
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.run_ocr_pipeline import run_pipeline
from src.build_book import build_chapters

def test_samples():
    sample_pages = [5, 11, 18, 665]
    print(f"🧪 正在執行抽樣測試頁面: {sample_pages} ...")
    
    for p in sample_pages:
        print(f"\n--- 測試第 {p} 頁 ---")
        run_pipeline(start_page=p, end_page=p, force=True, delay=1.0)

    print("\n🔨 測試聚合 docs/ ...")
    build_chapters()
    print("\n✅ 抽樣測試順利完成！")

if __name__ == "__main__":
    test_samples()
