import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import { api } from "./api";
import { Chat } from "./components/Chat";
import { Dashboard } from "./components/Dashboard";
import { Onboarding } from "./components/Onboarding";
import { PlanView } from "./components/PlanView";
import { Notes } from "./components/Notes";
import type { LearningPlan, OnboardingQuestion, Profile, ProgressSummary } from "./types";
import "./styles.css";

function App() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [question, setQuestion] = useState<OnboardingQuestion | null>(null);
  const [plan, setPlan] = useState<LearningPlan | null>(null);
  const [progress, setProgress] = useState<ProgressSummary | null>(null);
  const [dark, setDark] = useState(() => localStorage.getItem("tutorai-theme") === "dark");
  const [error, setError] = useState("");

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    localStorage.setItem("tutorai-theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    async function load() {
      try {
        const currentQuestion = await api.getQuestion();
        setQuestion(currentQuestion);
        if (currentQuestion.complete) {
          setProfile(await api.getProfile());
          setPlan(await api.getPlan().catch(() => null));
          setProgress(await api.getProgress().catch(() => null));
        }
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "The API is unavailable.");
      }
    }
    void load();
  }, []);

  if (error && !question) {
    return <main className="app-shell"><section className="panel"><p className="eyebrow">TutorAI</p><h1>We could not connect</h1><p className="error-message">{error}</p><p className="muted">Start the backend with <code>make backend</code>, then refresh this page.</p></section></main>;
  }

  if (!question || !question.complete) {
    return <main className="app-shell"><Onboarding question={question ?? { step: 0, question: "What do you want to learn?", complete: false }} onComplete={() => window.location.reload()} /></main>;
  }
  if (!profile) return <main className="app-shell"><p className="muted">Loading your workspace...</p></main>;

  return (
    <div className="app-shell workspace">
      <header className="topbar">
        <div><p className="eyebrow">Your local learning coach</p><strong className="brand">TutorAI</strong></div>
        <button className="theme-button" onClick={() => setDark((value) => !value)} aria-label="Toggle color theme">{dark ? "Light" : "Dark"} mode</button>
      </header>
      <Dashboard profile={profile} plan={plan} streakDays={progress?.streak_days} weakArea={progress?.weak_area} />
      <main className="workspace-grid">
        <PlanView plan={plan} onPlanChange={setPlan} />
        <Chat />
      </main>
      <Notes />
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode><App /></StrictMode>,
);
