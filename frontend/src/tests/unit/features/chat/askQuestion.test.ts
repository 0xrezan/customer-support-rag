import { describe, it, expect } from "vitest";
import { askQuestion } from "@/features/chat/api/askQuestion";

describe("askQuestion", () => {
  it("sends a question and returns answer with citations", async () => {
    const result = await askQuestion({ question: "What is the return policy?" });

    expect(result.status).toBe("success");
    expect(result.answer).toContain("return policy");
    expect(result.citations).toHaveLength(1);
    expect(result.citations[0]?.document_name).toBe("returns-policy.pdf");
    expect(result.latency_ms).toBeGreaterThan(0);
  });

  it("includes optional source and user_id in request", async () => {
    const result = await askQuestion({
      question: "Test question",
      source: "web",
      user_id: "user-123",
    });

    expect(result.status).toBe("success");
    expect(result.answer).toBeDefined();
  });
});
