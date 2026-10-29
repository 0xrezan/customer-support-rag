import { useAdminAuth } from "@/features/admin-auth/hooks/useAdminAuth";
import { AdminLoginPage } from "./AdminLoginPage";
import { AdminDashboardPage } from "./AdminDashboardPage";

export function AdminPage() {
  const { isAuthenticated } = useAdminAuth();
  return isAuthenticated ? <AdminDashboardPage /> : <AdminLoginPage />;
}
