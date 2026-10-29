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

  // Mock documents list
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
            {
              id: "doc-002",
              filename: "faq.md",
              content_hash: "hash-002",
              file_size: 15360,
              mime_type: "text/markdown",
              version: 2,
              is_active_version: true,
              status: "processing",
              chunk_count_expected: 8,
              chunk_count_actual: 4,
              page_count: null,
              error_message: null,
              created_at: "2025-01-16T14:20:00Z",
              updated_at: "2025-01-16T14:20:00Z",
            },
          ],
          total: 2,
        }),
      });
      return;
    }
    await route.fallback();
  });

  // Mock upload
  await page.route("**/api/v1/admin/upload", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        document_id: "doc-003",
        filename: "new-doc.pdf",
        status: "processing",
      }),
    });
  });

  // Mock delete
  await page.route("**/api/v1/admin/documents/doc-001*", async (route) => {
    if (route.request().method() === "DELETE") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          message: "Document deleted",
          document_id: "doc-001",
        }),
      });
    } else {
      await route.fallback();
    }
  });

  // Mock reindex
  await page.route(
    "**/api/v1/admin/documents/doc-001/reindex",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          message: "Reindexing started",
          document_id: "doc-001",
        }),
      });
    },
  );

  // Navigate and authenticate
  await page.goto("/admin");
  await page.getByPlaceholder("Paste your admin token").fill("test-token");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("Admin Dashboard")).toBeVisible();
});

test.describe("Documents management", () => {
  test("shows documents table with data", async ({ page }) => {
    await expect(page.getByText("returns-policy.pdf")).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByText("faq.md")).toBeVisible();
  });

  test("shows status badges for documents", async ({ page }) => {
    await expect(page.getByText("returns-policy.pdf")).toBeVisible({
      timeout: 5000,
    });
    await expect(
      page.getByRole("row", { name: /returns-policy\.pdf/ }).getByText("ready"),
    ).toBeVisible();
    await expect(
      page.getByRole("row", { name: /faq\.md/ }).getByText("processing"),
    ).toBeVisible();
  });

  test("shows upload dropzone", async ({ page }) => {
    await expect(page.getByText(/Drag & drop a file/)).toBeVisible();
    await expect(page.getByText(/PDF, TXT, MD, or DOCX/)).toBeVisible();
  });

  test("shows refresh button", async ({ page }) => {
    await expect(page.getByRole("button", { name: /Refresh/ })).toBeVisible();
  });

  test("shows delete confirm dialog", async ({ page }) => {
    await expect(page.getByText("returns-policy.pdf")).toBeVisible({
      timeout: 5000,
    });

    // Click delete for the first document
    await page
      .getByRole("button", { name: /Delete returns-policy\.pdf/ })
      .click();

    // Confirm dialog appears
    await expect(page.getByText("Delete Document")).toBeVisible();
    await expect(page.getByText(/Are you sure you want to delete/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Cancel" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();
  });

  test("shows reindex confirm dialog", async ({ page }) => {
    await expect(page.getByText("returns-policy.pdf")).toBeVisible({
      timeout: 5000,
    });

    // Click reindex for the first document
    await page
      .getByRole("button", { name: /Reindex returns-policy\.pdf/ })
      .click();

    // Confirm dialog appears
    await expect(page.getByText("Reindex Document")).toBeVisible();
    await expect(
      page.getByText(/Are you sure you want to reindex/),
    ).toBeVisible();
  });

  test("can confirm delete action", async ({ page }) => {
    await expect(page.getByText("returns-policy.pdf")).toBeVisible({
      timeout: 5000,
    });

    await page
      .getByRole("button", { name: /Delete returns-policy\.pdf/ })
      .click();
    await page.getByRole("button", { name: "Confirm" }).click();

    // Dialog should close after confirm
    await expect(page.getByText("Delete Document")).not.toBeVisible({
      timeout: 3000,
    });
  });

  test("can confirm reindex action", async ({ page }) => {
    await expect(page.getByText("returns-policy.pdf")).toBeVisible({
      timeout: 5000,
    });

    await page
      .getByRole("button", { name: /Reindex returns-policy\.pdf/ })
      .click();
    await page.getByRole("button", { name: "Confirm" }).click();

    // Dialog should close after confirm
    await expect(page.getByText("Reindex Document")).not.toBeVisible({
      timeout: 3000,
    });
  });

  test("can cancel delete action", async ({ page }) => {
    await expect(page.getByText("returns-policy.pdf")).toBeVisible({
      timeout: 5000,
    });

    await page
      .getByRole("button", { name: /Delete returns-policy\.pdf/ })
      .click();
    await page.getByRole("button", { name: "Cancel" }).click();

    await expect(page.getByText("Delete Document")).not.toBeVisible();
  });
});
