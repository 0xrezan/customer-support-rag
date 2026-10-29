export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 py-2" aria-label="Bot is typing" role="status">
      <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
      <span className="sr-only">Bot is typing</span>
    </div>
  );
}
