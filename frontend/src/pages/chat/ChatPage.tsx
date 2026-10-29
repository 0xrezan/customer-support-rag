import { useCallback, useState } from "react";
import { useChatSession } from "@/features/chat/hooks/useChatSession";
import { ChatTimeline } from "@/features/chat/components/ChatTimeline";
import { ChatComposer } from "@/features/chat/components/ChatComposer";
import { ChatEmptyState } from "@/features/chat/components/ChatEmptyState";
import { SourceSelector } from "@/features/chat/components/SourceSelector";
import { Particles } from "@/shared/ui/particles";
import { cn } from "@/shared/lib/cn";
import { Play, RefreshCw } from "lucide-react";
import {
  CHAT_DEMO_SCRIPT_MESSAGES,
  demoMessagePauseMs,
  demoPreSendPauseMs,
  demoTypingDelayMs,
  isChatDemoScriptEnabled,
  sleep,
} from "./demoScript";

const SOURCE_OPTIONS = [
  { value: "web", label: "All sources" },
  { value: "docs", label: "Documentation" },
  { value: "faq", label: "FAQ" },
] as const;

export function ChatPage() {
  const [source, setSource] = useState("web");
  const [demoRunning, setDemoRunning] = useState(false);

  const {
    messages,
    draft,
    setDraft,
    askQuestion,
    isAsking,
    submitFeedback,
    retryMessage,
  } = useChatSession({ source });

  const demoScriptEnabled = isChatDemoScriptEnabled();
  const demoScriptDisabled = isAsking || demoRunning;

  const runDemoScript = useCallback(async () => {
    if (!demoScriptEnabled || demoScriptDisabled) return;

    setDemoRunning(true);

    try {
      for (const message of CHAT_DEMO_SCRIPT_MESSAGES) {
        setDraft("");

        for (let i = 0; i < message.length; i += 1) {
          setDraft(message.slice(0, i + 1));
          await sleep(demoTypingDelayMs(message.charAt(i), i));
        }

        await sleep(demoPreSendPauseMs());
        await askQuestion(message, { bypassCache: true });
        await sleep(demoMessagePauseMs());
      }
    } finally {
      setDraft("");
      setDemoRunning(false);
    }
  }, [askQuestion, demoScriptDisabled, demoScriptEnabled, setDraft]);

  return (
    <main className="ambient-glow relative mx-auto flex min-h-dvh w-full max-w-4xl flex-col">
      <Particles />

      <header className="relative z-10 grid grid-cols-[1fr_auto_1fr] items-center border-b border-border/50 px-4 py-3">
        <span aria-hidden="true" />
        <h1 className="brand-foil text-xl font-bold tracking-tight">
          Arch Tech
        </h1>
        <div className="flex justify-end">
          {demoScriptEnabled && (
            <button
              type="button"
              onClick={runDemoScript}
              disabled={demoScriptDisabled}
              aria-label="Run demo script"
              title="Run demo script"
              className={cn(
                "grid h-6 w-6 place-items-center rounded-full transition",
                "text-muted-foreground/50 hover:bg-secondary hover:text-foreground",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                "disabled:cursor-not-allowed disabled:opacity-35",
              )}
            >
              {demoRunning ? (
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Play className="h-3.5 w-3.5" />
              )}
            </button>
          )}
        </div>
      </header>

      <div className="relative z-10 flex flex-1 flex-col">
        {messages.length === 0 ? (
          <ChatEmptyState />
        ) : (
          <ChatTimeline
            messages={messages}
            onFeedback={submitFeedback}
            onRetry={retryMessage}
          />
        )}
      </div>

      <div className="sticky bottom-0 z-10 border-t border-border/50 bg-background/80 p-4 backdrop-blur-sm">
        <div className="mb-2">
          <SourceSelector
            options={SOURCE_OPTIONS}
            value={source}
            onChange={setSource}
          />
        </div>
        <ChatComposer
          value={draft}
          onChange={setDraft}
          onSubmit={askQuestion}
          disabled={isAsking || demoRunning}
        />
      </div>
    </main>
  );
}
