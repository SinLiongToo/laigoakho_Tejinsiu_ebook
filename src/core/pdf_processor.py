# -*- coding: utf-8 -*-
"""
PDF processing module using PyMuPDF (fitz).
Extracts high quality images for OCR.
"""

import os
import fitz

class PDFProcessor:
    def __init__(self, pdf_path: str, temp_dir: str = "cache/temp_images"):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        self.pdf_path = pdf_path
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        self.doc = fitz.open(self.pdf_path)
        self.total_pages = len(self.doc)

    def extract_page_image(self, page_number: int, dpi: int = 200) -> str:
        """
        Extract page (1-based index) as PNG image.
        Returns the absolute file path of the extracted image.
        """
        if page_number < 1 or page_number > self.total_pages:
            raise ValueError(f"Page number {page_number} out of range (1 - {self.total_pages})")

        page_index = page_number - 1
        page = self.doc[page_index]
        
        # Render page to high-res image (200 DPI gives great OCR balance)
        pix = page.get_pixmap(dpi=dpi)
        image_filename = f"page_{page_number:03d}.png"
        image_path = os.path.join(self.temp_dir, image_filename)
        pix.save(image_path)
        return image_path

    def cleanup_image(self, image_path: str):
        """Remove temporary image file."""
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception:
            pass

    def close(self):
        """Close PDF document."""
        if self.doc:
            self.doc.close()
