export const CHAT_DEMO_SCRIPT_MESSAGES = [
  "Hello, what does your company do?",
  "Do you sell robot vacuum cleaners?",
  "So I can order smart home devices from you?",
  "What are the delivery times and how much does it cost?",
  "Do you deliver to Saratov?",
  "What happens if the product arrives defective?",
] as const;

const DEMO_TYPING_DELAY_SCALE = 2;

export function isChatDemoScriptEnabled() {
  return (
    !import.meta.env.PROD &&
    (import.meta.env.VITE_CHAT_DEMO_SCRIPT as string | undefined) === "true"
  );
}

export function demoTypingDelayMs(
  char: string,
  index: number,
  mode = import.meta.env.MODE,
) {
  if (mode === "test") return 0;
  const baseDelay = /[.!?]/.test(char)
    ? 34
    : char === " "
      ? 9
      : 10 + (index % 4) * 3;
  return Math.round(baseDelay * DEMO_TYPING_DELAY_SCALE);
}

export function demoMessagePauseMs(mode = import.meta.env.MODE) {
  return mode === "test" ? 0 : 1250;
}

export function demoPreSendPauseMs(mode = import.meta.env.MODE) {
  return mode === "test" ? 0 : 700;
}

export function sleep(ms: number) {
  if (ms <= 0) return Promise.resolve();
  return new Promise<void>((resolve) => window.setTimeout(resolve, ms));
}
