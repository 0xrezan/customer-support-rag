import { QueryProvider } from "./providers/QueryProvider";
import { AuthProvider } from "./providers/AuthProvider";
import { ErrorBoundary } from "./providers/ErrorBoundary";
import { RouterProvider } from "./providers/RouterProvider";
import { ThemeProvider } from "./providers/ThemeProvider";
import { ToastProvider } from "@/shared/ui/toast";

export function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <QueryProvider>
          <AuthProvider>
            <ToastProvider>
              <RouterProvider />
            </ToastProvider>
          </AuthProvider>
        </QueryProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
