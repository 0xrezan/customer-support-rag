import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod/v4";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { useAdminAuth } from "../hooks/useAdminAuth";
import { MAX_TOKEN_LENGTH } from "@/shared/config/security";

const tokenSchema = z.object({
  token: z
    .string()
    .min(1, "Token is required")
    .max(MAX_TOKEN_LENGTH, `Token must be at most ${MAX_TOKEN_LENGTH} characters`),
});

type TokenFormValues = z.infer<typeof tokenSchema>;

export function AdminTokenForm() {
  const { login } = useAdminAuth();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<TokenFormValues>({
    resolver: zodResolver(tokenSchema),
    defaultValues: { token: "" },
  });

  const onSubmit = (values: TokenFormValues) => {
    login(values.token);
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex w-full max-w-sm flex-col gap-4"
    >
      <div className="space-y-2">
        <label htmlFor="admin-token" className="text-sm font-medium">
          Admin Token
        </label>
        <Input
          id="admin-token"
          type="password"
          placeholder="Paste your admin token"
          autoComplete="off"
          {...register("token")}
          aria-invalid={!!errors.token}
          aria-describedby={errors.token ? "token-error" : undefined}
        />
        {errors.token && (
          <p id="token-error" className="text-sm text-destructive">
            {errors.token.message}
          </p>
        )}
      </div>
      <Button type="submit" disabled={isSubmitting}>
        Sign in
      </Button>
    </form>
  );
}
