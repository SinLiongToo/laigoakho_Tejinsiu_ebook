# -*- coding: utf-8 -*-
"""
Statistics and Cost Calculator for 1917 Lai-goa-kho Tann-jin-siu.
"""

import os
import sys
import json
import glob

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CACHE_DIR = "cache/raw_pages"
CONFIG_PATH = "config/book_structure.json"

def calculate_stats():
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: {CONFIG_PATH} not found.")
        return

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        book_structure = json.load(f)

    total_pages = book_structure["total_pages"]
    cached_files = glob.glob(os.path.join(CACHE_DIR, "page_*.json"))
    
    successful_pages = 0
    failed_pages = 0
    total_characters = 0
    total_time_seconds = 0
    
    sections_progress = []
    
    for sec in book_structure["sections"]:
        s_page = sec["start_page"]
        e_page = sec["end_page"]
        count = 0
        chars = 0
        for p in range(s_page, e_page + 1):
            c_file = os.path.join(CACHE_DIR, f"page_{p:03d}.json")
            if os.path.exists(c_file):
                try:
                    with open(c_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data.get("text"):
                            count += 1
                            chars += len(data["text"])
                            total_time_seconds += data.get("elapsed_seconds", 0)
                        elif data.get("error"):
                            failed_pages += 1
                except Exception:
                    pass
        successful_pages += count
        total_characters += chars
        sections_progress.append({
            "title": sec["title"],
            "expected_pages": e_page - s_page + 1,
            "done_pages": count,
            "characters": chars
        })

    percent = (successful_pages / total_pages) * 100 if total_pages > 0 else 0

    print("=" * 65)
    print("📊 1917《內外科看護學》數位化進度與數據統計")
    print("=" * 65)
    print(f"📚 全書總頁數: {total_pages} 頁")
    print(f"✅ 已成功完成: {successful_pages} 頁 ({percent:.1f}%)")
    print(f"⚠️ 異常/待補跑: {failed_pages} 頁")
    print(f"📝 總擷取字數: {total_characters:,} 字")
    print(f"⏱️ 累計耗時: {total_time_seconds / 60:.1f} 分鐘")
    
    # Cost estimation (Gemini 2.5/3.7 Flash: ~$0.075/1M input image tokens, ~$0.30/1M output tokens)
    est_input_tokens = successful_pages * 300
    est_output_tokens = (total_characters / 2) * 1.3
    est_cost_usd = (est_input_tokens / 1_000_000 * 0.10) + (est_output_tokens / 1_000_000 * 0.40)
    est_cost_twd = est_cost_usd * 32.5
    
    print(f"💰 預估 API 花費: 約 ${est_cost_usd:.4f} USD (約新台幣 {est_cost_twd:.2f} 元)")
    print("-" * 65)
    print("📌 各篇章進度摘要：")
    for sp in sections_progress:
        status_icon = "🟢" if sp["done_pages"] == sp["expected_pages"] else ("🟡" if sp["done_pages"] > 0 else "⚪")
        print(f"  {status_icon} {sp['title'][:32]:<32} : {sp['done_pages']:02d}/{sp['expected_pages']:02d} 頁 ({sp['characters']:,} 字)")
    print("=" * 65)

if __name__ == "__main__":
    calculate_stats()
