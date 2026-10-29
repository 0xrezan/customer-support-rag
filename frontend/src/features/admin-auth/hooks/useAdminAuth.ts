import { useContext } from "react";
import { AuthContext } from "@/app/providers/auth-context";
import type { AuthContextValue } from "../types/auth.types";

export function useAdminAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAdminAuth must be used within an AuthProvider");
  }
  return context;
}
