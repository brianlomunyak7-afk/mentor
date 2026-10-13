export type Profile = {
  learning_topic: string | null;
  motivation: string | null;
  goal: string | null;
  deadline: string | null;
  current_level: "beginner" | "intermediate" | "advanced" | null;
  daily_minutes: number | null;
  language: string;
  device_limits: string | null;
  internet_limits: string | null;
  preferences: Record<string, unknown>;
  onboarding_step: number;
  created_at: string;
  updated_at: string;
};

export type OnboardingQuestion = {
  step: number;
  question: string | null;
  complete: boolean;
};

export type Lesson = {
  id: number;
  module_number: number;
  lesson_number: number;
  title: string;
  goal: string;
  explanation: string;
  examples: string[];
  practice_task: string;
  quiz: string[];
  estimated_minutes: number;
  status: "not_started" | "in_progress" | "completed";
};

export type LearningPlan = {
  id: number;
  title: string;
  goal: string;
  status: string;
  lessons: Lesson[];
};

export type Resource = {
  title: string;
  url: string;
  source: string;
  duration_seconds: number | null;
  reason: string;
};

export type ChatResponse = {
  answer_id: number;
  message: string;
  provider: string;
  model: string;
  sources: Resource[];
};
