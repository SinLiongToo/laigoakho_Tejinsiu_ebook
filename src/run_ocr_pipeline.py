# -*- coding: utf-8 -*-
"""
Main OCR Pipeline runner for 1917 Lai-goa-kho Tann-jin-siu.
Designed for 100% resilient, non-stop processing with atomic disk cache,
progress tracking, automatic error skipping & end-of-batch retry.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

# Adjust module path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.core.pdf_processor import PDFProcessor
from src.core.gemini_ocr import GeminiOCREngine
from src.core.prompt_templates import get_prompt_for_type

CACHE_DIR = "cache/raw_pages"
CONFIG_PATH = "config/book_structure.json"
PROGRESS_FILE = "cache/progress_summary.json"
PDF_PATH = "1917-內外科看護學.pdf"

def load_book_structure(config_path: str = CONFIG_PATH) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_section_for_page(book_structure: dict, page_num: int) -> dict:
    """Find the section config for a given 1-based page number."""
    for sec in book_structure["sections"]:
        if sec["start_page"] <= page_num <= sec["end_page"]:
            return sec
    return {
        "id": "unknown",
        "type": "poj_main",
        "title": f"未分類頁面_{page_num}",
        "volume": "01_Volume_1_Anatomy_Physiology",
        "target_file": f"unknown/page_{page_num:03d}.md"
    }

def run_pipeline(start_page: int = 1, 
                 end_page: int = 705, 
                 model: str = "gemini-3.7-flash", 
                 force: bool = False, 
                 delay: float = 1.2,
                 pdf_path: str = PDF_PATH):
    
    os.makedirs(CACHE_DIR, exist_ok=True)
    book_structure = load_book_structure()
    pdf_processor = PDFProcessor(pdf_path)
    total_pages = min(end_page, pdf_processor.total_pages)
    
    ocr_engine = GeminiOCREngine(model=model)
    
    print("=" * 70)
    print(f"📖 啟動 1917《內外科看護學》AI OCR 數位化流水線")
    print(f"🎯 目標範圍: 第 {start_page} 頁 ～ 第 {total_pages} 頁 (全書共 {pdf_processor.total_pages} 頁)")
    print(f"🤖 採用模型: {model}")
    print(f"🛡️ 容錯機制: 單頁原子快取 + 斷點防護 + 零中斷自動續跑")
    print("=" * 70)

    failed_pages = []
    processed_count = 0
    skipped_count = 0

    for page_num in range(start_page, total_pages + 1):
        cache_file = os.path.join(CACHE_DIR, f"page_{page_num:03d}.json")
        
        # Check if already processed
        if os.path.exists(cache_file) and not force:
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("text") and not data.get("error"):
                        skipped_count += 1
                        if page_num % 20 == 0 or page_num == start_page:
                            print(f"⏩ 第 {page_num:03d}/{total_pages} 頁：已存在快取，自動跳過")
                        continue
            except Exception:
                pass # corrupted cache, re-process

        section = get_section_for_page(book_structure, page_num)
        prompt = get_prompt_for_type(section.get("type", "main_chapter"))

        print(f"\n📄 [{page_num:03d}/{total_pages}] 正在處理：{section.get('title')} ({section.get('type')})")
        
        image_path = None
        start_time = time.time()
        
        try:
            # 1. Extract high-res image
            image_path = pdf_processor.extract_page_image(page_num, dpi=200)
            
            # 2. Call Gemini OCR
            result_text = ocr_engine.process_image(image_path, prompt)
            elapsed = time.time() - start_time
            
            # 3. Save atomic page cache
            page_record = {
                "page_number": page_num,
                "section_id": section.get("id"),
                "section_type": section.get("type"),
                "volume": section.get("volume"),
                "target_file": section.get("target_file"),
                "chapter_title": section.get("title"),
                "processed_at": datetime.now().isoformat(),
                "model": model,
                "elapsed_seconds": round(elapsed, 2),
                "text": result_text,
                "error": None
            }
            
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(page_record, f, ensure_ascii=False, indent=2)
                
            processed_count += 1
            print(f"✅ 第 {page_num:03d} 頁完成 ({elapsed:.1f}s, {len(result_text)} 字)")

        except Exception as e:
            elapsed = time.time() - start_time
            err_msg = str(e)
            print(f"⚠️ 第 {page_num:03d} 頁發生錯誤: {err_msg}")
            print(f"📌 記錄錯誤並繼續處理下一頁，確保整體流水線不中斷...")
            
            # Save error record
            err_record = {
                "page_number": page_num,
                "section_id": section.get("id"),
                "section_type": section.get("type"),
                "processed_at": datetime.now().isoformat(),
                "model": model,
                "error": err_msg,
                "text": None
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(err_record, f, ensure_ascii=False, indent=2)
                
            failed_pages.append((page_num, err_msg))
            
            # Also append to log file
            with open("error_log.txt", "a", encoding="utf-8") as log_f:
                log_f.write(f"[{datetime.now().isoformat()}] Page {page_num} Failed: {err_msg}\n")

        finally:
            if image_path:
                pdf_processor.cleanup_image(image_path)
            
            # Respectful pacing between calls
            time.sleep(delay)

    # Secondary retry pass for any failed pages in this run
    if failed_pages:
        print("\n" + "=" * 70)
        print(f"🔄 正在對本批次失敗的 {len(failed_pages)} 個頁面進行二次自動修復補跑...")
        print("=" * 70)
        
        still_failed = []
        for page_num, prev_err in failed_pages:
            cache_file = os.path.join(CACHE_DIR, f"page_{page_num:03d}.json")
            section = get_section_for_page(book_structure, page_num)
            prompt = get_prompt_for_type(section.get("type", "main_chapter"))
            
            print(f"🔁 重試第 {page_num:03d} 頁...")
            image_path = None
            try:
                time.sleep(3.0) # slightly longer wait before retry
                image_path = pdf_processor.extract_page_image(page_num, dpi=200)
                result_text = ocr_engine.process_image(image_path, prompt)
                
                page_record = {
                    "page_number": page_num,
                    "section_id": section.get("id"),
                    "section_type": section.get("type"),
                    "volume": section.get("volume"),
                    "target_file": section.get("target_file"),
                    "chapter_title": section.get("title"),
                    "processed_at": datetime.now().isoformat(),
                    "model": model,
                    "text": result_text,
                    "error": None
                }
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(page_record, f, ensure_ascii=False, indent=2)
                print(f"✨ 第 {page_num:03d} 頁重試修復成功！")
                processed_count += 1
            except Exception as e:
                print(f"❌ 第 {page_num:03d} 頁重試依然失敗: {e}")
                still_failed.append((page_num, str(e)))
            finally:
                if image_path:
                    pdf_processor.cleanup_image(image_path)
                    
        failed_pages = still_failed

    pdf_processor.close()

    # Save summary progress
    summary = {
        "last_run": datetime.now().isoformat(),
        "total_requested": total_pages - start_page + 1,
        "processed_this_run": processed_count,
        "skipped_cached": skipped_count,
        "failed_remaining": len(failed_pages),
        "failed_list": failed_pages
    }
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("🎉 本批次處理完畢！")
    print(f"📊 新處理頁數: {processed_count}")
    print(f"⚡ 快取略過頁數: {skipped_count}")
    print(f"⚠️ 剩餘待修正頁數: {len(failed_pages)}")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="1917 Lai-goa-kho Tann-jin-siu OCR Pipeline")
    parser.add_argument("--start", type=int, default=1, help="Start page number (1-based, default: 1)")
    parser.add_argument("--end", type=int, default=705, help="End page number (1-based, default: 705)")
    parser.add_argument("--model", type=str, default="gemini-3.7-flash", help="Gemini model name")
    parser.add_argument("--force", action="store_true", help="Force re-run even if cached")
    parser.add_argument("--delay", type=float, default=1.2, help="Delay between calls in seconds")
    parser.add_argument("--page", type=int, default=None, help="Process a single specific page")
    
    args = parser.parse_args()
    
    if args.page is not None:
        run_pipeline(start_page=args.page, end_page=args.page, model=args.model, force=args.force, delay=args.delay)
    else:
        run_pipeline(start_page=args.start, end_page=args.end, model=args.model, force=args.force, delay=args.delay)
