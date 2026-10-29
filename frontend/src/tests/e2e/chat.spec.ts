import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  // Mock the chat API
  await page.route("**/api/v1/chat/ask", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "success",
        answer:
          "Based on the documentation, the return policy allows returns within 30 days of purchase.",
        citations: [
          {
            document_name: "returns-policy.pdf",
            page: 1,
            chunk_id: "chunk-001",
          },
        ],
        latency_ms: 245,
      }),
    });
  });

  // Mock the feedback API
  await page.route("**/api/v1/feedback/submit", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "fb-001",
        answer_id: "ans-001",
        rating: "up",
      }),
    });
  });
});

test.describe("Chat flow", () => {
  test("shows empty state on first visit", async ({ page }) => {
    await page.goto("/chat");

    await expect(page.getByText("How can I help you?")).toBeVisible();
    await expect(page.getByPlaceholder("Ask a question...")).toBeVisible();
  });

  test("can ask a question and receive a response", async ({ page }) => {
    await page.goto("/chat");

    // Type a question
    const input = page.getByPlaceholder("Ask a question...");
    await input.fill("What is the return policy?");

    // Send
    await page.getByRole("button", { name: "Send message" }).click();

    // User message appears
    await expect(
      page.getByText("What is the return policy?"),
    ).toBeVisible();

    // Bot response appears
    await expect(page.getByText(/return policy allows/)).toBeVisible({
      timeout: 5000,
    });

    // Citation appears
    await expect(page.getByText("returns-policy.pdf")).toBeVisible();

    // Input is cleared
    await expect(input).toHaveValue("");
  });

  test("can submit feedback on an answer", async ({ page }) => {
    await page.goto("/chat");

    const input = page.getByPlaceholder("Ask a question...");
    await input.fill("Hello");
    await page.getByRole("button", { name: "Send message" }).click();

    // Wait for bot response
    await expect(page.getByText(/return policy allows/)).toBeVisible({
      timeout: 5000,
    });

    // Click thumbs up
    const helpfulButton = page.getByRole("button", { name: "Helpful", exact: true });
    await helpfulButton.click();

    // Button should be disabled after feedback
    await expect(helpfulButton).toBeDisabled();
  });

  test("send button is disabled when input is empty", async ({ page }) => {
    await page.goto("/chat");

    const sendButton = page.getByRole("button", { name: "Send message" });
    await expect(sendButton).toBeDisabled();
  });
});
