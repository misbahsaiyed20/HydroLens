import { Icon } from "@/components/ui/Icon";

export function LoadingState({ label = "Loading…", rows = 3 }: { label?: string; rows?: number }) {
  return (
    <div className="space-y-3 py-4" role="status" aria-live="polite">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="card animate-pulse space-y-3 p-5">
          <div className="h-3 w-1/4 rounded bg-ocean-100" />
          <div className="h-3 w-3/4 rounded bg-ocean-100" />
          <div className="h-3 w-1/2 rounded bg-ocean-100" />
        </div>
      ))}
      <p className="text-center text-xs text-ocean-400">{label}</p>
    </div>
  );
}

export function EmptyState({
  message,
  hint,
}: {
  message: string;
  hint?: string;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-card border border-dashed border-ocean-200 bg-ocean-50/50 px-6 py-14 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-ocean-400 shadow-card">
        <Icon.Layers className="h-5 w-5" />
      </span>
      <p className="text-sm font-medium text-ocean-700">{message}</p>
      {hint && <p className="max-w-xs text-xs text-ocean-400">{hint}</p>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-card border border-rose-200 bg-rose-50 px-6 py-10 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-rose-500 shadow-card">
        <Icon.Warning className="h-5 w-5" />
      </span>
      <p className="text-sm font-medium text-rose-700">Unable to load data.</p>
      <p className="max-w-sm text-xs text-rose-500">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary mt-1 border-rose-200 text-rose-700 hover:bg-rose-100">
          Try again
        </button>
      )}
    </div>
  );
}
