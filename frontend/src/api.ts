import type {
  ChatResponse,
  LearningPlan,
  Lesson,
  OnboardingQuestion,
  Profile,
  Resource,
} from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  getQuestion: () => request<OnboardingQuestion>("/api/onboarding/questions"),
  answerQuestion: (step: number, answer: string | string[]) =>
    request<Profile>("/api/onboarding/answers", {
      method: "POST",
      body: JSON.stringify({ step, answer }),
    }),
  getProfile: () => request<Profile>("/api/profile"),
  getPlan: () => request<LearningPlan>("/api/plans/latest"),
  createPlan: () =>
    request<LearningPlan>("/api/plans", { method: "POST" }),
  updateProgress: (id: number, status: Lesson["status"]) =>
    request<Lesson>(`/api/lessons/${id}/progress`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  getResources: (id: number) =>
    request<Resource[]>(`/api/lessons/${id}/resources`),
  chat: (message: string) =>
    request<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
};
