import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { AuthProvider } from "@/app/providers/AuthProvider";
import { ThemeProvider } from "@/app/providers/ThemeProvider";
import { ToastProvider } from "@/shared/ui/toast";
import { AdminPage } from "@/pages/admin/AdminPage";
import { clearToken } from "@/features/admin-auth/lib/auth-memory-store";

function renderAdminPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ToastProvider>
            <MemoryRouter>
              <AdminPage />
            </MemoryRouter>
          </ToastProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>,
  );
}

describe("AdminPage", () => {
  beforeEach(() => {
    clearToken();
  });

  it("shows login form when not authenticated", () => {
    renderAdminPage();

    expect(screen.getByText("Admin Access")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Paste your admin token"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Sign in" }),
    ).toBeInTheDocument();
  });

  it("shows validation error for empty token", async () => {
    renderAdminPage();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(screen.getByText("Token is required")).toBeInTheDocument();
    });
  });

  it("transitions to dashboard after entering token", async () => {
    renderAdminPage();
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText("Paste your admin token");
    await user.type(input, "test-admin-token");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(screen.getByText("Admin Dashboard")).toBeInTheDocument();
    });
  });

  it("shows documents table after auth", async () => {
    renderAdminPage();
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText("Paste your admin token");
    await user.type(input, "test-admin-token");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(screen.getByText("Documents")).toBeInTheDocument();
    });

    // Documents load from MSW
    await waitFor(
      () => {
        expect(screen.getByText("returns-policy.pdf")).toBeInTheDocument();
      },
      { timeout: 5000 },
    );

    expect(screen.getByText("faq.md")).toBeInTheDocument();
  });

  it("shows sign out button and can logout", async () => {
    renderAdminPage();
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText("Paste your admin token");
    await user.type(input, "test-admin-token");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(screen.getByText("Admin Dashboard")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Sign out/ }));

    await waitFor(() => {
      expect(screen.getByText("Admin Access")).toBeInTheDocument();
    });
  });

  it("shows health badge on dashboard", async () => {
    renderAdminPage();
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText("Paste your admin token");
    await user.type(input, "test-admin-token");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    // Wait for the dashboard to appear first
    await waitFor(() => {
      expect(screen.getByText("Admin Dashboard")).toBeInTheDocument();
    });

    // The health badge and metrics card both show "Healthy"
    await waitFor(
      () => {
        const healthyElements = screen.getAllByText("Healthy");
        expect(healthyElements.length).toBeGreaterThanOrEqual(1);
      },
      { timeout: 5000 },
    );
  });

  it("shows upload dropzone on dashboard", async () => {
    renderAdminPage();
    const user = userEvent.setup();

    const input = screen.getByPlaceholderText("Paste your admin token");
    await user.type(input, "test-admin-token");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(
        screen.getByText(/Drag & drop a file/),
      ).toBeInTheDocument();
    });
  });
});
