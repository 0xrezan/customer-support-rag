import { type KeyboardEvent, useRef, useEffect } from "react";
import { Textarea } from "@/shared/ui/textarea";
import { Send } from "lucide-react";
import { MAX_QUESTION_LENGTH } from "@/shared/config/security";
import { cn } from "@/shared/lib/cn";

interface ChatComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void | Promise<void>;
  disabled: boolean;
}

export function ChatComposer({
  value,
  onChange,
  onSubmit,
  disabled,
}: ChatComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled) {
        onSubmit();
      }
    }
  };

  const isActive = !disabled && !!value.trim();

  return (
    <div className="flex items-end gap-2">
      <Textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question..."
        maxLength={MAX_QUESTION_LENGTH}
        disabled={disabled}
        className="min-h-[48px] max-h-[200px] resize-none"
        rows={1}
        aria-label="Chat message input"
      />
      <button
        type="button"
        onClick={() => onSubmit()}
        disabled={!isActive}
        aria-label="Send message"
        className={cn(
          "btn-emerald inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md text-sm font-medium transition-all",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:pointer-events-none disabled:opacity-40",
        )}
      >
        <Send className="h-4 w-4" />
      </button>
    </div>
  );
}
