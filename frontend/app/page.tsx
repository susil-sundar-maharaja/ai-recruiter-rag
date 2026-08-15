"use client";

import { useState, useRef } from "react";
import {
  uploadResume,
  startSession,
  submitAnswer,
  getSessionSummary,
  ResumeInfo,
  SessionSummary,
} from "../lib/api";

const ROLES = ["AI Engineer", "ML Engineer", "Data Scientist"];
const MAX_QUESTIONS = 5;

type Stage = "entry" | "interview" | "summary";

const TEAL = "#2F6F5E";
const AMBER = "#E8A33D";
const RED = "#B3261E";
const INK = "#1B2430";
const MUTED = "#6B7280";

function sentimentColors(sentiment: string | null) {
  if (sentiment === "negative") return { bg: "#FDECEC", border: RED, label: RED };
  if (sentiment === "mixed") return { bg: "#FEF6E7", border: AMBER, label: "#92620C" };
  return { bg: "#F0F7F5", border: TEAL, label: TEAL }; // positive or unknown defaults to teal
}

function StepRail({ stage }: { stage: Stage }) {
  const steps = [
    { key: "entry", label: "Resume & Role" },
    { key: "interview", label: "Interview" },
    { key: "summary", label: "Summary" },
  ];
  const activeIndex = steps.findIndex((s) => s.key === stage);

  return (
    <div className="flex md:flex-col gap-4 md:gap-8 mb-8 md:mb-0 md:mr-12 md:w-48 shrink-0">
      {steps.map((step, i) => {
        const isDone = i < activeIndex;
        const isActive = i === activeIndex;
        return (
          <div key={step.key} className="flex md:flex-col items-center md:items-start gap-2 md:gap-1">
            <div className="flex items-center gap-2">
              <span
                className="flex items-center justify-center w-7 h-7 rounded-full text-xs shrink-0"
                style={{
                  fontFamily: "var(--font-mono), monospace",
                  backgroundColor: isDone || isActive ? TEAL : "#E5E7EB",
                  color: isDone || isActive ? "#fff" : MUTED,
                }}
              >
                {i + 1}
              </span>
              <span
                className="hidden md:inline text-xs uppercase tracking-wide"
                style={{
                  fontFamily: "var(--font-mono), monospace",
                  color: isActive ? INK : MUTED,
                }}
              >
                {step.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function Home() {
  const [stage, setStage] = useState<Stage>("entry");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [role, setRole] = useState(ROLES[0]);

  const [sessionId, setSessionId] = useState<number | null>(null);
  const [questionId, setQuestionId] = useState<number | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [questionNumber, setQuestionNumber] = useState(1);

  const [summary, setSummary] = useState<SessionSummary | null>(null);

  function handleFileSelect(file: File | null) {
    if (file && file.type !== "application/pdf") {
      setError("Please upload a PDF file.");
      return;
    }
    setError("");
    setResumeFile(file);
  }

  async function handleStart() {
    if (!resumeFile) {
      setError("Please upload your resume first.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const info: ResumeInfo = await uploadResume(resumeFile);
      const session = await startSession(role, info);

      setSessionId(session.session_id);
      setQuestionId(session.question_id);
      setQuestion(session.question);
      setQuestionNumber(1);
      setStage("interview");
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmitAnswer() {
    if (!answer.trim() || sessionId === null || questionId === null) return;
    setError("");
    setLoading(true);
    try {
      const result = await submitAnswer(sessionId, questionId, answer);
      setAnswer("");

      if (result.interview_complete) {
        const finalSummary = await getSessionSummary(sessionId);
        setSummary(finalSummary);
        setStage("summary");
      } else {
        setQuestionId(result.question_id ?? null);
        setQuestion(result.question ?? "");
        setQuestionNumber((n) => n + 1);
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen p-6 md:p-12" style={{ backgroundColor: "#F5F6F8" }}>
      <div className="max-w-4xl mx-auto flex flex-col md:flex-row">
        <StepRail stage={stage} />

        <div className="flex-1 bg-white rounded-2xl shadow-sm border border-gray-100 p-8 md:p-10">
          <h1
            className="text-2xl md:text-3xl mb-1"
            style={{ fontFamily: "var(--font-display), serif", fontWeight: 600, color: INK }}
          >
            AI Recruiter
          </h1>
          <p className="text-sm mb-8" style={{ color: MUTED }}>
            Candidate screening, grounded in your background
          </p>

          {error && (
            <p
              className="mb-5 text-sm rounded-lg px-3 py-2"
              style={{ backgroundColor: "#FDECEC", color: RED }}
            >
              {error}
            </p>
          )}

          {stage === "entry" && (
            <div className="space-y-7">
              <div>
                <label
                  className="block text-xs uppercase tracking-wide mb-2"
                  style={{ fontFamily: "var(--font-mono), monospace", color: MUTED }}
                >
                  01 — Resume
                </label>
                <div
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragOver(true);
                  }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setDragOver(false);
                    handleFileSelect(e.dataTransfer.files?.[0] || null);
                  }}
                  className="cursor-pointer rounded-xl border-2 border-dashed flex flex-col items-center justify-center text-center px-6 py-10 transition-colors"
                  style={{
                    borderColor: dragOver ? TEAL : "#D1D5DB",
                    backgroundColor: dragOver ? "#F0F7F5" : "#FAFAFA",
                  }}
                >
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" style={{ color: TEAL }}>
                    <path
                      d="M12 16V4M12 4L7 9M12 4l5 5M5 20h14"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <p className="mt-3 text-sm" style={{ color: INK }}>
                    {resumeFile ? resumeFile.name : "Click or drag your resume here"}
                  </p>
                  <p className="text-xs mt-1" style={{ color: MUTED }}>
                    PDF only
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="application/pdf"
                    onChange={(e) => handleFileSelect(e.target.files?.[0] || null)}
                    className="hidden"
                  />
                </div>
              </div>

              <div>
                <label
                  className="block text-xs uppercase tracking-wide mb-2"
                  style={{ fontFamily: "var(--font-mono), monospace", color: MUTED }}
                >
                  02 — Target role
                </label>
                <div className="flex flex-wrap gap-2">
                  {ROLES.map((r) => {
                    const active = role === r;
                    return (
                      <button
                        key={r}
                        type="button"
                        onClick={() => setRole(r)}
                        className="px-4 py-2 rounded-full text-sm border transition-colors"
                        style={{
                          borderColor: active ? TEAL : "#D1D5DB",
                          backgroundColor: active ? TEAL : "transparent",
                          color: active ? "#fff" : INK,
                        }}
                      >
                        {r}
                      </button>
                    );
                  })}
                </div>
              </div>

              <button
                onClick={handleStart}
                disabled={loading}
                className="w-full rounded-lg py-3 font-medium text-white transition-opacity disabled:opacity-50"
                style={{ backgroundColor: TEAL }}
              >
                {loading ? "Starting…" : "Start interview"}
              </button>
            </div>
          )}

          {stage === "interview" && (
            <div className="space-y-6">
              <div className="flex items-center gap-2">
                {Array.from({ length: MAX_QUESTIONS }).map((_, i) => (
                  <span
                    key={i}
                    className="h-1.5 flex-1 rounded-full"
                    style={{
                      backgroundColor: i < questionNumber - 1 ? AMBER : i === questionNumber - 1 ? TEAL : "#E5E7EB",
                    }}
                  />
                ))}
              </div>
              <p className="text-xs" style={{ fontFamily: "var(--font-mono), monospace", color: MUTED }}>
                Question {questionNumber} of {MAX_QUESTIONS}
              </p>
              <p
                className="text-xl leading-relaxed"
                style={{ fontFamily: "var(--font-display), serif", color: INK }}
              >
                {question}
              </p>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                rows={6}
                placeholder="Type your answer here..."
                className="w-full rounded-lg p-4 text-sm outline-none border transition-colors"
                style={{ borderColor: "#D1D5DB" }}
                onFocus={(e) => (e.currentTarget.style.borderColor = TEAL)}
                onBlur={(e) => (e.currentTarget.style.borderColor = "#D1D5DB")}
              />
              <button
                onClick={handleSubmitAnswer}
                disabled={loading}
                className="w-full rounded-lg py-3 font-medium text-white transition-opacity disabled:opacity-50"
                style={{ backgroundColor: TEAL }}
              >
                {loading ? "Submitting…" : "Submit answer"}
              </button>
            </div>
          )}

          {stage === "summary" && summary && (
            <div className="space-y-6">
              <h2
                className="text-xl"
                style={{ fontFamily: "var(--font-display), serif", fontWeight: 600, color: INK }}
              >
                Interview summary
              </h2>
              <p className="text-xs" style={{ fontFamily: "var(--font-mono), monospace", color: MUTED }}>
                {summary.role.toUpperCase()} · {summary.status.toUpperCase()}
              </p>

              {summary.insights && (() => {
                const colors = sentimentColors(summary.insights_sentiment);
                return (
                  <div
                    className="rounded-xl p-5"
                    style={{ backgroundColor: colors.bg, border: `1px solid ${colors.border}55` }}
                  >
                    <p
                      className="text-xs uppercase tracking-wide mb-2"
                      style={{ fontFamily: "var(--font-mono), monospace", color: colors.label }}
                    >
                      AI Assessment
                      {summary.insights_sentiment ? ` · ${summary.insights_sentiment.toUpperCase()}` : ""}
                    </p>
                    <p className="text-sm leading-relaxed" style={{ color: INK }}>
                      {summary.insights}
                    </p>
                  </div>
                );
              })()}

              {summary.questions_and_answers.map((qa, i) => (
                <div key={i} className="border-t pt-5" style={{ borderColor: "#E5E7EB" }}>
                  <p className="font-medium mb-2" style={{ color: INK }}>
                    Q{i + 1}: {qa.question}
                  </p>
                  <p className="text-sm mb-3" style={{ color: MUTED }}>
                    {qa.answer || "(not answered)"}
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {qa.sources.map((s, j) => (
                      <span
                        key={j}
                        className="text-[10px] px-2 py-1 rounded-full"
                        style={{
                          fontFamily: "var(--font-mono), monospace",
                          backgroundColor: "#F0F7F5",
                          color: TEAL,
                        }}
                      >
                        {s.replace(".pdf", "")}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
