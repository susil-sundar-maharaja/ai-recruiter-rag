"""
Quick manual test for query construction + retrieval.

Usage:
    python test_retrieval.py
"""

from app.services.resume_parser import extract_text_from_resume, extract_resume_info
from app.services.retrieval import build_queries, retrieve_relevant_chunks

ROLE = "AI Engineer"  # change to "ML Engineer" or "Data Scientist" to test other roles
RESUME_PATH = "data/sample_resume.pdf"

print("Parsing resume...")
text = extract_text_from_resume(RESUME_PATH)
resume_info = extract_resume_info(text)

print("\nBuilding queries...")
queries = build_queries(resume_info, ROLE)
for q in queries:
    print(" -", q)

first_query = queries[0]
print(f"\n--- Retrieval for: \"{first_query}\" ---")
chunks = retrieve_relevant_chunks(first_query, ROLE, top_k=3)

if not chunks:
    print("No chunks returned — check that ROLE matches a role in your ROLE_MAP exactly.")
else:
    for i, c in enumerate(chunks, 1):
        print(f"\n[{i}] source: {c['source']}")
        print(c["text"][:300], "...")
