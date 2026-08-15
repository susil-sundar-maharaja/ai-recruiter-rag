const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export interface ResumeInfo {
  skills: string[];
  technologies: string[];
  domains: string[];
  experience_level: string;
  summary: string;
}

export interface StartSessionResult {
  session_id: number;
  question: string;
  question_id: number;
}

export interface SubmitAnswerResult {
  session_id: number;
  question?: string;
  question_id?: number;
  interview_complete: boolean;
}

export interface QuestionAnswerPair {
  question: string;
  answer: string | null;
  sources: string[];
}

export interface SessionSummary {
  session_id: number;
  role: string;
  status: string;
  insights: string | null;
  insights_sentiment: string | null;
  questions_and_answers: QuestionAnswerPair[];
}

export async function uploadResume(file: File): Promise<ResumeInfo> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/upload-resume`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to upload resume");
  const data = await res.json();
  return data.resume_info;
}

export async function startSession(role: string, resumeInfo: ResumeInfo): Promise<StartSessionResult> {
  const res = await fetch(`${API_BASE}/api/start-session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role, resume_info: resumeInfo }),
  });
  if (!res.ok) throw new Error("Failed to start session");
  return res.json();
}

export async function submitAnswer(
  sessionId: number,
  questionId: number,
  answer: string
): Promise<SubmitAnswerResult> {
  const res = await fetch(`${API_BASE}/api/submit-answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question_id: questionId, answer }),
  });
  if (!res.ok) throw new Error("Failed to submit answer");
  return res.json();
}

export async function getSessionSummary(sessionId: number): Promise<SessionSummary> {
  const res = await fetch(`${API_BASE}/api/session-summary/${sessionId}`);
  if (!res.ok) throw new Error("Failed to get summary");
  return res.json();
}
