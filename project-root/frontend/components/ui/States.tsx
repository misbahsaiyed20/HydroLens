export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="animate-pulse space-y-3 py-8">
      <div className="h-4 w-1/3 rounded bg-slate-200" />
      <div className="h-24 rounded bg-slate-200" />
      <div className="h-24 rounded bg-slate-200" />
      <p className="text-xs text-slate-400">{label}</p>
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded border border-dashed border-slate-300 py-12 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded border border-red-200 bg-red-50 py-8 text-center text-sm text-red-700">
      <p>{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-3 rounded bg-red-600 px-3 py-1 text-xs text-white">
          Retry
        </button>
      )}
    </div>
  );
}
