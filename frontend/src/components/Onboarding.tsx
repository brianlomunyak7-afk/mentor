import { FormEvent, useState } from "react";

import { api } from "../api";
import type { OnboardingQuestion } from "../types";

type Props = {
  question: OnboardingQuestion;
  onComplete: () => void;
};

export function Onboarding({ question, onComplete }: Props) {
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!answer.trim()) return;
    setBusy(true);
    setError("");
    try {
      await api.answerQuestion(question.step, answer.trim());
      if (question.step >= 8) onComplete();
      else window.location.reload();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not save your answer.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel onboarding-panel" aria-labelledby="onboarding-title">
      <p className="eyebrow">Let&apos;s get to know you</p>
      <h1 id="onboarding-title">Build your learning path</h1>
      <p className="muted">Question {question.step + 1} of 9. Short answers are perfect.</p>
      <form onSubmit={submit}>
        <label htmlFor="onboarding-answer">{question.question}</label>
        <textarea
          id="onboarding-answer"
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
          placeholder="Type your answer..."
          rows={4}
          autoFocus
          required
        />
        {error && <p className="error-message" role="alert">{error}</p>}
        <button className="primary-button" disabled={busy || !answer.trim()}>
          {busy ? "Saving..." : "Continue"}
        </button>
      </form>
    </section>
  );
}
