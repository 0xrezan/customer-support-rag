import { AlertTriangle } from "lucide-react";
import { Alert, AlertTitle, AlertDescription } from "@/shared/ui/alert";

interface ChatErrorStateProps {
  message?: string;
}

export function ChatErrorState({ message }: ChatErrorStateProps) {
  return (
    <div className="flex flex-1 items-center justify-center p-8">
      <Alert variant="destructive" className="max-w-md">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Chat unavailable</AlertTitle>
        <AlertDescription>
          {message ?? "Unable to connect to the chat service. Please try again later."}
        </AlertDescription>
      </Alert>
    </div>
  );
}
