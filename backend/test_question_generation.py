"""
End-to-end test: resume -> queries -> retrieval -> generated question.

Usage:
    python test_question_generation.py
"""

from app.services.resume_parser import extract_text_from_resume, extract_resume_info
from app.services.retrieval import build_queries, retrieve_relevant_chunks
from app.services.question_generator import generate_question

ROLE = "AI Engineer"  # change to test other roles
RESUME_PATH = "data/sample_resume.pdf"

print("Parsing resume...")
text = extract_text_from_resume(RESUME_PATH)
resume_info = extract_resume_info(text)

print("Building queries...")
queries = build_queries(resume_info, ROLE)

print(f"\nRetrieving context for: \"{queries[0]}\"")
chunks = retrieve_relevant_chunks(queries[0], ROLE, top_k=3)

if not chunks:
    print("No chunks found for this role/query — check ROLE_MAP matches exactly.")
else:
    print(f"Retrieved {len(chunks)} chunks from: {sorted({c['source'] for c in chunks})}")

    print("\nGenerating question...")
    result = generate_question(chunks, resume_info, ROLE)

    print("\n--- Generated Question ---")
    print(result["question"])
    print("\nGrounded in sources:", result["grounded_in_sources"])
