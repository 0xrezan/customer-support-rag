import { AdminTokenForm } from "@/features/admin-auth/components/AdminTokenForm";
import { Shield } from "lucide-react";

export function AdminLoginPage() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-6 p-8">
      <div className="flex flex-col items-center gap-2">
        <div className="rounded-full bg-muted p-3">
          <Shield className="h-6 w-6 text-muted-foreground" />
        </div>
        <h1 className="text-xl font-semibold">Admin Access</h1>
        <p className="text-sm text-muted-foreground">
          Enter your admin token to access the dashboard.
        </p>
      </div>
      <AdminTokenForm />
    </main>
  );
}
