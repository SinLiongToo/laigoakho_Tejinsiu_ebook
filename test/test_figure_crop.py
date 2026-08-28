# -*- coding: utf-8 -*-
import os
import sys
import json
import fitz
from PIL import Image
from google import genai

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Setup
os.makedirs("docs/assets/illustrations", exist_ok=True)
doc = fitz.open("1917-內外科看護學.pdf")
page_idx = 24  # Page 25
page = doc[page_idx]
pix = page.get_pixmap(dpi=200)
test_img_path = "cache/test_p25.png"
pix.save(test_img_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is required")
client = genai.Client(api_key=api_key)
myfile = client.files.upload(file=test_img_path)

prompt = """
Detect all illustrations, medical diagrams, anatomical figures, or surgical drawings in this page.
For each figure found, return a JSON array with bounding boxes normalized to [0, 1000]:
[
  {
    "box_2d": [ymin, xmin, ymax, xmax],
    "caption": "Short caption or figure label"
  }
]
If there are no illustrations on this page, return [] empty list.
Output ONLY the JSON list.
"""

resp = client.models.generate_content(
    model="gemini-3.7-flash",
    contents=[prompt, myfile]
)

print("Detection result:")
print(resp.text)

# Clean and crop
try:
    clean_text = resp.text.strip().replace("```json", "").replace("```", "").strip()
    boxes = json.loads(clean_text)
    img = Image.open(test_img_path)
    w, h = img.size
    
    for i, item in enumerate(boxes):
        box = item["box_2d"]
        ymin, xmin, ymax, xmax = box
        crop_box = (
            int(xmin * w / 1000),
            int(ymin * h / 1000),
            int(xmax * w / 1000),
            int(ymax * h / 1000)
        )
        cropped_img = img.crop(crop_box)
        crop_filename = f"page_{page_idx+1:03d}_fig_{i+1:02d}.png"
        crop_path = os.path.join("docs/assets/illustrations", crop_filename)
        cropped_img.save(crop_path)
        print(f"Successfully cropped figure {i+1} to: {crop_path} ({item.get('caption')})")
finally:
    client.files.delete(name=myfile.name)
