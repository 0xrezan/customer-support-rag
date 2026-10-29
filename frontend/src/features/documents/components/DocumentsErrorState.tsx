import { AlertTriangle } from "lucide-react";
import { Alert, AlertTitle, AlertDescription } from "@/shared/ui/alert";
import { Button } from "@/shared/ui/button";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/shared/api/query-keys";

export function DocumentsErrorState() {
  const queryClient = useQueryClient();

  const handleRetry = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
  };

  return (
    <Alert variant="destructive">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>Failed to load documents</AlertTitle>
      <AlertDescription className="flex items-center gap-2">
        <span>Could not fetch the documents list.</span>
        <Button variant="outline" size="sm" onClick={handleRetry}>
          Retry
        </Button>
      </AlertDescription>
    </Alert>
  );
}
