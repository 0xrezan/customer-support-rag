import { cn } from "@/shared/lib/cn";

interface SourceOption {
  readonly value: string;
  readonly label: string;
}

interface SourceSelectorProps {
  options: readonly SourceOption[];
  value: string;
  onChange: (value: string) => void;
}

export function SourceSelector({
  options,
  value,
  onChange,
}: SourceSelectorProps) {
  return (
    <div
      className="flex items-center gap-1"
      role="radiogroup"
      aria-label="Search source"
    >
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          role="radio"
          aria-checked={value === opt.value}
          onClick={() => onChange(opt.value)}
          className={cn(
            "rounded-full px-3 py-1 text-xs font-medium transition-all",
            value === opt.value
              ? "btn-emerald shadow-sm"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
