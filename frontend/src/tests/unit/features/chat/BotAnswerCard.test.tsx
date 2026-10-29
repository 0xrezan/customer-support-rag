import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BotAnswerCard } from "@/features/chat/components/BotAnswerCard";

describe("BotAnswerCard", () => {
  it("renders **bold** facts as <strong> without raw asterisks", () => {
    render(
      <BotAnswerCard
        message={{
          id: "m1",
          role: "bot",
          content: "Employees receive **20 days of PTO** per year.",
        }}
        onFeedback={() => {}}
      />,
    );

    expect(screen.getByText("20 days of PTO").tagName).toBe("STRONG");
    expect(screen.queryByText(/\*\*/)).toBeNull();
  });
});
