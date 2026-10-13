import { describe, expect, it, vi } from "vitest";

import { api } from "./api";

describe("frontend foundation", () => {
  it("has a test runner configured", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ step: 0, question: "Topic?", complete: false }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.getQuestion()).resolves.toEqual({
      step: 0,
      question: "Topic?",
      complete: false,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/onboarding/questions",
      expect.objectContaining({ headers: { "Content-Type": "application/json" } }),
    );
  });
});
