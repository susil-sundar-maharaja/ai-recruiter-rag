"""
Quick manual test for the resume parser — run this directly to check it works
before we wire it into the actual API.

Usage:
    1. Put any resume PDF into the data/ folder, name it sample_resume.pdf
    2. Run: python test_resume_parser.py
"""

import json
from app.services.resume_parser import extract_text_from_resume, extract_resume_info

RESUME_PATH = "data/sample_resume.pdf"

print("Extracting text from resume...")
text = extract_text_from_resume(RESUME_PATH)
print(f"Extracted {len(text)} characters\n")

print("Sending to Gemini for structuring...")
info = extract_resume_info(text)

print("\n--- Structured Resume Info ---")
print(json.dumps(info, indent=2))
