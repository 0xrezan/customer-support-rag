const UNITS = ["B", "KB", "MB", "GB", "TB"] as const;

export function formatBytes(bytes: number, decimals = 1): string {
  if (bytes === 0) return "0 B";
  if (bytes < 0) return "Invalid size";

  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const unitIndex = Math.min(i, UNITS.length - 1);
  const unit = UNITS[unitIndex];

  if (!unit) return `${bytes} B`;

  const value = bytes / Math.pow(k, unitIndex);
  return `${value.toFixed(decimals)} ${unit}`;
}
