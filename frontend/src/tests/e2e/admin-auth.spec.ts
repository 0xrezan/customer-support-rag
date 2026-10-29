import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  // Mock health API
  await page.route("**/api/v1/health/live", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
  });

  // Mock documents API
  await page.route("**/api/v1/admin/documents**", async (route) => {
    const url = new URL(route.request().url());
    if (
      route.request().method() === "GET" &&
      url.pathname.endsWith("/api/v1/admin/documents")
    ) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          documents: [
            {
              id: "doc-001",
              filename: "returns-policy.pdf",
              content_hash: "hash-001",
              file_size: 245760,
              mime_type: "application/pdf",
              version: 1,
              is_active_version: true,
              status: "ready",
              chunk_count_expected: 12,
              chunk_count_actual: 12,
              page_count: 3,
              error_message: null,
              created_at: "2025-01-15T10:30:00Z",
              updated_at: "2025-01-15T10:30:00Z",
            },
          ],
          total: 1,
        }),
      });
      return;
    }
    await route.fallback();
  });
});

test.describe("Admin auth flow", () => {
  test("shows login page when not authenticated", async ({ page }) => {
    await page.goto("/admin");

    await expect(page.getByText("Admin Access")).toBeVisible();
    await expect(
      page.getByPlaceholder("Paste your admin token"),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  });

  test("shows validation error for empty token", async ({ page }) => {
    await page.goto("/admin");

    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page.getByText("Token is required")).toBeVisible();
  });

  test("transitions to dashboard after entering token", async ({ page }) => {
    await page.goto("/admin");

    await page.getByPlaceholder("Paste your admin token").fill("test-token");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page.getByText("Admin Dashboard")).toBeVisible();
    await expect(
      page.locator("header").getByText("Healthy", { exact: true }),
    ).toBeVisible({ timeout: 5000 });
  });

  test("can sign out and return to login", async ({ page }) => {
    await page.goto("/admin");

    // Log in
    await page.getByPlaceholder("Paste your admin token").fill("test-token");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByText("Admin Dashboard")).toBeVisible();

    // Sign out
    await page.getByRole("button", { name: /Sign out/ }).click();
    await expect(page.getByText("Admin Access")).toBeVisible();
  });

  test("shows documents table after login", async ({ page }) => {
    await page.goto("/admin");

    await page.getByPlaceholder("Paste your admin token").fill("test-token");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page.getByText("returns-policy.pdf")).toBeVisible({
      timeout: 5000,
    });
  });
});
