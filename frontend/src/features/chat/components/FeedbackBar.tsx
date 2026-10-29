import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { cn } from "@/shared/lib/cn";
import { FeedbackCommentModal } from "./FeedbackCommentModal";
import type { FeedbackRating } from "../types/chat.types";

interface FeedbackBarProps {
  messageId: string;
  feedbackRating: FeedbackRating | null | undefined;
  onFeedback: (messageId: string, rating: FeedbackRating, comment?: string) => void;
}

export function FeedbackBar({
  messageId,
  feedbackRating,
  onFeedback,
}: FeedbackBarProps) {
  const [showCommentModal, setShowCommentModal] = useState(false);
  const hasVoted = feedbackRating !== null && feedbackRating !== undefined;

  const handleThumbsDown = () => {
    setShowCommentModal(true);
  };

  const handleCommentSubmit = (comment: string) => {
    setShowCommentModal(false);
    onFeedback(messageId, "down", comment || undefined);
  };

  const handleCommentCancel = () => {
    setShowCommentModal(false);
  };

  return (
    <>
      <div
        className="mt-2 flex items-center gap-1"
        role="group"
        aria-label="Rate this answer"
      >
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            "h-7 w-7 p-0",
            feedbackRating === "up" && "text-success",
          )}
          onClick={() => onFeedback(messageId, "up")}
          disabled={hasVoted}
          aria-label="Helpful"
          aria-pressed={feedbackRating === "up"}
        >
          <ThumbsUp className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            "h-7 w-7 p-0",
            feedbackRating === "down" && "text-destructive",
          )}
          onClick={handleThumbsDown}
          disabled={hasVoted}
          aria-label="Not helpful"
          aria-pressed={feedbackRating === "down"}
        >
          <ThumbsDown className="h-3.5 w-3.5" />
        </Button>
      </div>

      <FeedbackCommentModal
        open={showCommentModal}
        onSubmit={handleCommentSubmit}
        onCancel={handleCommentCancel}
      />
    </>
  );
}
