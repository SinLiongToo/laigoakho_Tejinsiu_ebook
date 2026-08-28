# -*- coding: utf-8 -*-
"""
Automated Illustration Extraction Pipeline for 1917 Lai-goa-kho Tann-jin-siu.
Uses Gemini 3.7 Flash to detect bounding boxes of anatomical figures, diagrams,
surgical instruments, and bandaging illustrations, and crops them via Pillow.
Saves single-page cache to ensure 100% resume capability and zero duplicate token cost.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from PIL import Image

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Adjust module path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.pdf_processor import PDFProcessor
from src.core.gemini_ocr import GeminiOCREngine

ILLUSTRATION_CACHE_DIR = "cache/illustrations"
ILLUSTRATION_OUTPUT_DIR = "docs/assets/illustrations"
ILLUSTRATIONS_MASTER_INDEX = "cache/illustrations_index.json"
PDF_PATH = "1917-內外科看護學.pdf"

PROMPT_DETECT_FIGURES = """
You are an expert document layout analyzer.
Analyze this scanned page from the 1917 medical book 'Lai-goa-kho Khan-ho-hak'.
Detect all illustrations, anatomical diagrams, medical charts, surgical instrument drawings, or bandaging illustrations on this page.

For each distinct illustration/figure found, output a JSON object:
- "box_2d": [ymin, xmin, ymax, xmax] with coordinates normalized in range [0, 1000].
- "caption": The original figure label or caption printed under or near the figure (e.g. "Tē 5 tô", "Tē 12 tô"), including POJ or Chinese/English text if present.

Return ONLY a valid JSON array:
[
  {
    "box_2d": [ymin, xmin, ymax, xmax],
    "caption": "Figure caption..."
  }
]
If there are NO illustrations or drawings on this page (only plain text or tables), return an empty list [].
Do NOT output markdown formatting around the JSON if possible, just clean JSON.
"""

def extract_illustrations(start_page: int = 1, 
                          end_page: int = 705, 
                          model: str = "gemini-3.7-flash", 
                          force: bool = False, 
                          delay: float = 0.8,
                          pdf_path: str = PDF_PATH):
    
    os.makedirs(ILLUSTRATION_CACHE_DIR, exist_ok=True)
    os.makedirs(ILLUSTRATION_OUTPUT_DIR, exist_ok=True)
    
    pdf_processor = PDFProcessor(pdf_path)
    total_pages = min(end_page, pdf_processor.total_pages)
    ocr_engine = GeminiOCREngine(model=model)
    
    print("=" * 70)
    print("🎨 啟動 1917《內外科看護學》全書插圖/解剖圖自動偵測與裁切流水線")
    print(f"🎯 目標範圍: 第 {start_page} 頁 ～ 第 {total_pages} 頁")
    print(f"🤖 採用模型: {model} (高精度視覺佈局偵測)")
    print(f"📂 輸出目錄: {ILLUSTRATION_OUTPUT_DIR}")
    print("=" * 70)

    total_figures_cropped = 0
    pages_with_figures = 0

    for page_num in range(start_page, total_pages + 1):
        cache_file = os.path.join(ILLUSTRATION_CACHE_DIR, f"page_{page_num:03d}.json")
        
        # Check cache
        figures = None
        if os.path.exists(cache_file) and not force:
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    figures = data.get("figures")
            except Exception:
                pass
                
        if figures is None:
            image_path = None
            try:
                # Extract high-res image (200 DPI)
                image_path = pdf_processor.extract_page_image(page_num, dpi=200)
                resp_text = ocr_engine.process_image(image_path, PROMPT_DETECT_FIGURES)
                
                # Parse JSON
                clean_json_str = resp_text.strip().replace("```json", "").replace("```", "").strip()
                figures = json.loads(clean_json_str) if clean_json_str else []
                
                # Save cache
                cache_record = {
                    "page_number": page_num,
                    "processed_at": datetime.now().isoformat(),
                    "model": model,
                    "figure_count": len(figures),
                    "figures": figures
                }
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_record, f, ensure_ascii=False, indent=2)
                    
            except Exception as e:
                print(f"⚠️ 第 {page_num:03d} 頁插圖偵測異常: {e}")
                figures = []
            finally:
                if image_path:
                    pdf_processor.cleanup_image(image_path)
                time.sleep(delay)

        # If page contains figures, perform high-res cropping
        if figures and len(figures) > 0:
            pages_with_figures += 1
            # Render page image for cropping
            page_img_path = pdf_processor.extract_page_image(page_num, dpi=200)
            try:
                with Image.open(page_img_path) as full_img:
                    w, h = full_img.size
                    for idx, fig in enumerate(figures):
                        box = fig.get("box_2d")
                        if not box or len(box) != 4:
                            continue
                        ymin, xmin, ymax, xmax = box
                        # Calculate pixel bounding box with slight safety padding
                        pad_x = int(w * 0.005)
                        pad_y = int(h * 0.005)
                        crop_box = (
                            max(0, int(xmin * w / 1000) - pad_x),
                            max(0, int(ymin * h / 1000) - pad_y),
                            min(w, int(xmax * w / 1000) + pad_x),
                            min(h, int(ymax * h / 1000) + pad_y)
                        )
                        cropped = full_img.crop(crop_box)
                        
                        fig_filename = f"page_{page_num:03d}_fig_{idx+1:02d}.png"
                        fig_save_path = os.path.join(ILLUSTRATION_OUTPUT_DIR, fig_filename)
                        cropped.save(fig_save_path, optimize=True)
                        
                        fig["saved_file"] = fig_filename
                        fig["saved_rel_path"] = f"assets/illustrations/{fig_filename}"
                        total_figures_cropped += 1
                        print(f"  🖼️ [p.{page_num:03d}] 擷取插圖 {idx+1}: {fig.get('caption', '')[:40]} -> {fig_filename}")
            finally:
                pdf_processor.cleanup_image(page_img_path)

        if page_num % 50 == 0 or page_num == total_pages:
            print(f"📊 處理進度: [{page_num:03d}/{total_pages}] 已累計裁切 {total_figures_cropped} 張插圖")

    pdf_processor.close()

    # Build master illustrations index
    master_index = {}
    for p in range(1, total_pages + 1):
        c_file = os.path.join(ILLUSTRATION_CACHE_DIR, f"page_{p:03d}.json")
        if os.path.exists(c_file):
            try:
                with open(c_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    figs = data.get("figures", [])
                    if figs:
                        master_index[str(p)] = figs
            except Exception:
                pass
                
    with open(ILLUSTRATIONS_MASTER_INDEX, "w", encoding="utf-8") as f:
        json.dump(master_index, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("🎉 插圖偵測與裁切任務圓滿完成！")
    print(f"🖼️ 總共擷取插圖數: {total_figures_cropped} 張 (分佈於 {pages_with_figures} 個頁面)")
    print(f"📑 索引已儲存至: {ILLUSTRATIONS_MASTER_INDEX}")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract all illustrations from 1917 PDF")
    parser.add_argument("--start", type=int, default=1, help="Start page")
    parser.add_argument("--end", type=int, default=705, help="End page")
    parser.add_argument("--model", type=str, default="gemini-3.7-flash", help="Gemini model")
    parser.add_argument("--force", action="store_true", help="Force re-detection")
    parser.add_argument("--delay", type=float, default=0.8, help="Delay between pages")
    
    args = parser.parse_args()
    extract_illustrations(start_page=args.start, end_page=args.end, model=args.model, force=args.force, delay=args.delay)
