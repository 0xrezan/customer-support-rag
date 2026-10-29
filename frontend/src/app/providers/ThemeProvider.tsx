import { useEffect, type ReactNode } from "react";

/**
 * Dark-only theme provider.
 * Applies the `dark` class to <html> on mount.
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    document.documentElement.classList.add("dark");
  }, []);

  return <>{children}</>;
}
