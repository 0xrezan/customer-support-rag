interface UploadProgressBarProps {
  progress: number;
}

export function UploadProgressBar({ progress }: UploadProgressBarProps) {
  return (
    <div className="w-full" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Uploading...</span>
        <span>{progress}%</span>
      </div>
      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-secondary">
        <div
          className="h-full rounded-full bg-primary transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
