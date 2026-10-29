import { useState } from "react";
import { Button } from "@/shared/ui/button";
import { Textarea } from "@/shared/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/shared/ui/dialog";
import { MAX_COMMENT_LENGTH } from "@/shared/config/security";

interface FeedbackCommentModalProps {
  open: boolean;
  onSubmit: (comment: string) => void;
  onCancel: () => void;
}

export function FeedbackCommentModal({
  open,
  onSubmit,
  onCancel,
}: FeedbackCommentModalProps) {
  const [comment, setComment] = useState("");

  const handleSubmit = () => {
    onSubmit(comment.trim());
    setComment("");
  };

  const handleSkip = () => {
    onSubmit("");
    setComment("");
  };

  const handleClose = () => {
    onCancel();
    setComment("");
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && handleClose()}>
      <DialogContent onClose={handleClose}>
        <DialogHeader>
          <DialogTitle>What went wrong?</DialogTitle>
          <DialogDescription>
            Help us improve by telling us what was wrong with this answer. This
            is optional.
          </DialogDescription>
        </DialogHeader>
        <Textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="The answer was inaccurate because..."
          maxLength={MAX_COMMENT_LENGTH}
          rows={3}
          className="resize-none"
          aria-label="Feedback comment"
        />
        <p className="text-right text-xs text-muted-foreground">
          {comment.length}/{MAX_COMMENT_LENGTH}
        </p>
        <DialogFooter>
          <Button variant="outline" onClick={handleSkip}>
            Skip
          </Button>
          <Button onClick={handleSubmit} disabled={!comment.trim()}>
            Submit
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
