import { Link } from "react-router-dom";
import { Button } from "@/shared/ui/button";
import { FileQuestion } from "lucide-react";
import { ROUTES } from "@/shared/constants/routes";

export function NotFoundPage() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-4 p-8 text-center">
      <div className="rounded-full bg-muted p-4">
        <FileQuestion className="h-8 w-8 text-muted-foreground" />
      </div>
      <h1 className="text-2xl font-bold">Page not found</h1>
      <p className="text-sm text-muted-foreground">
        The page you are looking for does not exist.
      </p>
      <Link to={ROUTES.CHAT}>
        <Button>Go to chat</Button>
      </Link>
    </main>
  );
}
