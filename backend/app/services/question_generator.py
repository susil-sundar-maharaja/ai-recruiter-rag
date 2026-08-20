import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "qwen/qwen3.6-27b"


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

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        reasoning_effort="none"
    )
    question_text = response.choices[0].message.content.strip()

    return {
        "question": question_text,
        "role": role,
        "grounded_in_sources": sources,
    }


def generate_session_insights(qas: list[dict], resume_info: dict, role: str) -> dict:
    """
    Called once, after the interview finishes. Returns both a written analysis
    AND a sentiment classification, so the frontend can style the result
    (e.g. green for a positive verdict, red for a negative one).
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

Return ONLY valid JSON — no markdown, no code fences, no explanation — with exactly this structure:

{{
  "sentiment": "positive" | "mixed" | "negative",
  "analysis": "3-5 sentence analysis: overall impression calibrated to how they actually answered, one or two specific strengths shown, and one area that could use deeper follow-up"
}}

Guidance for "sentiment":
- "positive": candidate demonstrated solid understanding across most answers
- "negative": candidate showed significant gaps, or answers were mostly incorrect, vague, or missing
- "mixed": a genuine blend of strong and weak answers

Be honest and calibrated — don't default to "positive" just to be polite.
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
