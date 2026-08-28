# -*- coding: utf-8 -*-
"""
Gemini OCR Engine using the new google-genai SDK.
Equipped with retry logic, rate limit handling, and multi-model fallback.
"""

import os
import time
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

FALLBACK_API_KEY = "YOUR_GEMINI_API_KEY"

def is_transient_error(exception: BaseException) -> bool:
    """Check if the error is retryable."""
    err_str = str(exception).lower()
    return any(keyword in err_str for keyword in [
        "429", "resource_exhausted", "quota", "503", "500", "timeout", 
        "connection", "remote disconnected", "internal error"
    ])

class GeminiOCREngine:
    def __init__(self, api_key: str = None, model: str = "gemini-3.7-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or FALLBACK_API_KEY
        self.model = model
        self.client = genai.Client(api_key=self.api_key)

    @retry(
        retry=retry_if_exception(is_transient_error),
        stop=stop_after_attempt(12),
        wait=wait_exponential(multiplier=2, min=3, max=90)
    )
    def process_image(self, image_path: str, prompt: str) -> str:
        """
        Upload image to Gemini File API and call vision generation.
        Deletes uploaded file after generation to keep quota clean.
        """
        myfile = None
        try:
            myfile = self.client.files.upload(file=image_path)
            
            # Call Gemini vision model
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt, myfile]
            )
            
            if not response.text:
                raise ValueError("Received empty text response from Gemini API")
                
            return response.text
        finally:
            if myfile is not None:
                try:
                    self.client.files.delete(name=myfile.name)
                except Exception:
                    pass
