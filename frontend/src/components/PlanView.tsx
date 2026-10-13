import { useState } from "react";

import { api } from "../api";
import type { LearningPlan, Resource } from "../types";

type Props = {
  plan: LearningPlan | null;
  onPlanChange: (plan: LearningPlan) => void;
};

export function PlanView({ plan, onPlanChange }: Props) {
  const [busy, setBusy] = useState(false);
  const [resourceMap, setResourceMap] = useState<Record<number, Resource[]>>({});
  const [error, setError] = useState("");

  async function createPlan() {
    setBusy(true);
    setError("");
    try {
      onPlanChange(await api.createPlan());
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not create a plan.");
    } finally {
      setBusy(false);
    }
  }

  async function updateLesson(id: number, status: "in_progress" | "completed") {
    const updated = await api.updateProgress(id, status);
    if (plan) onPlanChange({ ...plan, lessons: plan.lessons.map((lesson) => lesson.id === id ? updated : lesson) });
  }

  async function loadResources(id: number) {
    try {
      const resources = await api.getResources(id);
      setResourceMap((current) => ({ ...current, [id]: resources }));
    } catch {
      setError("Resources could not be loaded. Check your API keys and try again.");
    }
  }

  if (!plan) {
    return (
      <section className="panel">
        <p className="eyebrow">Your roadmap</p>
        <h2>Create a plan that fits you</h2>
        <p className="muted">TutorAI will turn your goal and available time into short, practical lessons.</p>
        {error && <p className="error-message" role="alert">{error}</p>}
        <button className="primary-button" onClick={createPlan} disabled={busy}>{busy ? "Creating..." : "Create learning plan"}</button>
      </section>
    );
  }

  const completed = plan.lessons.filter((lesson) => lesson.status === "completed").length;
  return (
    <section className="panel plan-panel" aria-labelledby="plan-title">
      <div className="panel-heading">
        <div><p className="eyebrow">Your roadmap</p><h2 id="plan-title">{plan.title}</h2></div>
        <span className="progress-label">{completed}/{plan.lessons.length} complete</span>
      </div>
      <div className="progress-track"><span style={{ width: `${plan.lessons.length ? (completed / plan.lessons.length) * 100 : 0}%` }} /></div>
      <p className="muted">{plan.goal}</p>
      <div className="lesson-list">
        {plan.lessons.map((lesson) => (
          <article className={`lesson-card ${lesson.status}`} key={lesson.id}>
            <div className="lesson-number">{lesson.lesson_number}</div>
            <div className="lesson-content">
              <p className="lesson-meta">Module {lesson.module_number} · {lesson.estimated_minutes} min</p>
              <h3>{lesson.title}</h3>
              <p>{lesson.goal}</p>
              <details><summary>Lesson preview</summary><p>{lesson.explanation}</p><ul>{lesson.examples.map((example) => <li key={example}>{example}</li>)}</ul></details>
              <div className="lesson-actions">
                {lesson.status !== "completed" && <button className="secondary-button" onClick={() => updateLesson(lesson.id, "completed")}>Mark complete</button>}
                <button className="text-button" onClick={() => loadResources(lesson.id)}>Find resources</button>
              </div>
              {resourceMap[lesson.id]?.map((resource) => <a className="resource-link" href={resource.url} target="_blank" rel="noreferrer" key={resource.url}><strong>{resource.title}</strong><span>{resource.source} · {resource.reason}</span></a>)}
              {resourceMap[lesson.id]?.map((resource) => (
                <button className="text-button" key={`${resource.url}-bookmark`} onClick={() => void api.createBookmark({ title: resource.title, url: resource.url, source: resource.source })}>
                  Bookmark resource
                </button>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
