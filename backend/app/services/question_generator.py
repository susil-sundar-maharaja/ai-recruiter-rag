"""
Question Generation Module
----------------------------
Takes retrieved knowledge-base chunks + resume info + role, and asks Gemini to write
ONE real interview question grounded in that context — not generic, not templated.

Also tracks which source chunks each question was grounded in, for traceability
(the assignment explicitly asks for this: Context -> Question -> Answer -> Storage).
"""

import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_question(chunks: list[dict], resume_info: dict, role: str, asked_questions: list[str] = None) -> dict:
    """
    chunks: retrieved chunks from retrieval.retrieve_relevant_chunks()
    resume_info: structured dict from resume_parser.extract_resume_info()
    role: the selected role, e.g. "AI Engineer"
    asked_questions: list of question strings already asked this session (avoids repeats)
    """
    asked_questions = asked_questions or []

    context = "\n\n---\n\n".join(c["text"] for c in chunks)
    sources = sorted({c["source"] for c in chunks})

    already_asked = "\n".join(f"- {q}" for q in asked_questions) if asked_questions else "(none yet)"

    prompt = f"""You are an experienced technical interviewer conducting a {role} interview.

Candidate background:
- Summary: {resume_info.get("summary", "N/A")}
- Skills: {", ".join(resume_info.get("skills", []))}
- Technologies: {", ".join(resume_info.get("technologies", []))}
- Experience level: {resume_info.get("experience_level", "N/A")}

Reference material (grounded context from the knowledge base — base your question on this, don't invent facts outside it):
---
{context}
---

Questions already asked this session (do NOT repeat these or ask something too similar):
{already_asked}

Write exactly ONE interview question that:
- Is grounded in the reference material above
- Is calibrated to the candidate's experience level and background
- Requires real understanding, not a yes/no or definition-recall answer
- Is NOT generic or templated — it should feel like it was written for this specific candidate and this specific content

Return ONLY the question text. No preamble, no "Here's a question:", no numbering.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    question_text = response.text.strip()

    return {
        "question": question_text,
        "role": role,
        "grounded_in_sources": sources,
    }
