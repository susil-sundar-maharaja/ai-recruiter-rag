import os
import json
import io

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "qwen/qwen3.6-27b"

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
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        reasoning_effort="none"
    )
    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()

    return json.loads(raw)
