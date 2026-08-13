import os
import json
import io

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def extract_text_from_resume(pdf_path: str, min_chars_for_real_text: int = 20) -> str:
    doc = fitz.open(pdf_path)
    pages_text = []
    for page in doc:
        text = page.get_text().strip()
        if len(text) < min_chars_for_real_text:
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img)
        pages_text.append(text)
    doc.close()
    return "\n".join(pages_text)


def extract_resume_info(resume_text: str) -> dict:
    prompt = f"""You are extracting structured information from a resume.
Return ONLY valid JSON — no markdown, no code fences, no explanation — with exactly this structure:

{{
  "skills": ["list of technical skills"],
  "technologies": ["list of tools, frameworks, languages, platforms"],
  "domains": ["domain areas the candidate has worked in, e.g. fintech, healthcare, e-commerce"],
  "experience_level": "junior | mid | senior",
  "summary": "one sentence summary of the candidate's background"
}}

Resume text:
---
{resume_text}
---
"""
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
    return json.loads(raw)