import { Sun, Moon, Monitor } from "lucide-react";
import { Button } from "./button";
import { useTheme } from "@/shared/hooks/useTheme";

const icons = {
  light: Sun,
  dark: Moon,
  system: Monitor,
} as const;

const nextTheme = {
  light: "dark",
  dark: "system",
  system: "light",
} as const;

const labels = {
  light: "Switch to dark mode",
  dark: "Switch to system mode",
  system: "Switch to light mode",
} as const;

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const Icon = icons[theme];

  return (
    <Button
      variant="ghost"
      size="icon"
      className="h-9 w-9"
      onClick={() => setTheme(nextTheme[theme])}
      aria-label={labels[theme]}
    >
      <Icon className="h-4 w-4" />
    </Button>
  );
}
