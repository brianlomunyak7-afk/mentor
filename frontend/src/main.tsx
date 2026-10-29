import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";

function App() {
  return (
    <main className="app-shell">
      <section className="welcome-card" aria-labelledby="welcome-title">
        <p className="eyebrow">Your local learning coach</p>
        <h1 id="welcome-title">TutorAI</h1>
        <p>
          A calm, adaptive space to learn step by step. Your tutor workspace
          will be ready in the next phase.
        </p>
        <span className="status-pill">Foundation ready</span>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
