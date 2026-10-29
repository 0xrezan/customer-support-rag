import type { ReactNode } from "react";
import { useAdminAuth } from "../hooks/useAdminAuth";

interface ProtectedRouteProps {
  children: ReactNode;
  fallback: ReactNode;
}

export function ProtectedRoute({ children, fallback }: ProtectedRouteProps) {
  const { isAuthenticated } = useAdminAuth();
  return isAuthenticated ? <>{children}</> : <>{fallback}</>;
}
