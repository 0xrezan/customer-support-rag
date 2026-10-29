import { MessageSquare } from "lucide-react";

export function ChatEmptyState() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
      <div className="rounded-full bg-muted p-4">
        <MessageSquare className="h-8 w-8 text-muted-foreground" />
      </div>
      <div>
        <h2 className="text-lg font-semibold">How can I help you?</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Ask a question and I will search through the knowledge base to find an answer.
        </p>
      </div>
    </div>
  );
}
