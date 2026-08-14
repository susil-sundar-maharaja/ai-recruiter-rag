import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_question(chunks: list[dict], resume_info: dict, role: str, asked_questions: list[str] = None) -> dict:
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


def generate_session_insights(qas: list[dict], resume_info: dict, role: str) -> str:
    """
    Called once, after the interview finishes. Reads the full transcript and
    produces a short analysis — this is the "basic insights or analysis of the
    session" the assignment asks for, separate from the raw Q&A transcript itself.
    """
    transcript = "\n\n".join(
        f"Q: {qa['question']}\nA: {qa['answer'] or '(not answered)'}"
        for qa in qas
    )

    prompt = f"""You are a technical interviewer summarizing a completed {role} screening interview.

Candidate background summary: {resume_info.get("summary", "N/A")}

Full interview transcript:
---
{transcript}
---

Write a brief analysis (3-5 sentences) covering:
- Overall impression of the candidate's understanding, calibrated to how they actually answered
- One or two specific strengths shown in their answers
- One area that could use deeper follow-up in a next round

Return plain text only. No headers, no markdown formatting, no bullet points.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()
