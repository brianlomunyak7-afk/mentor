import type { LearningPlan, Profile } from "../types";

type Props = { profile: Profile; plan: LearningPlan | null };

export function Dashboard({ profile, plan }: Props) {
  const completed = plan?.lessons.filter((lesson) => lesson.status === "completed").length ?? 0;
  return (
    <aside className="dashboard" aria-label="Progress dashboard">
      <div><span className="dashboard-value">{completed}</span><span className="dashboard-label">Lessons complete</span></div>
      <div><span className="dashboard-value">{profile.daily_minutes ?? "—"}</span><span className="dashboard-label">Minutes per day</span></div>
      <div><span className="dashboard-value">{profile.current_level ?? "New"}</span><span className="dashboard-label">Current level</span></div>
    </aside>
  );
}
