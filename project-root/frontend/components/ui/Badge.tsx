const STYLES: Record<string, { bg: string; text: string; icon: string; label?: string }> = {
  // confidence / severity / exposure levels
  LOW: { bg: "bg-slate-100", text: "text-slate-700", icon: "○" },
  NONE: { bg: "bg-slate-100", text: "text-slate-500", icon: "–" },
  MODERATE: { bg: "bg-amber-100", text: "text-amber-800", icon: "◐" },
  HIGH: { bg: "bg-red-100", text: "text-red-800", icon: "●" },
  ELEVATED: { bg: "bg-red-100", text: "text-red-800", icon: "●" },

  // verification
  UNVERIFIED: { bg: "bg-slate-100", text: "text-slate-600", icon: "?" },
  VERIFIED: { bg: "bg-emerald-100", text: "text-emerald-800", icon: "✓" },
  REJECTED: { bg: "bg-slate-200", text: "text-slate-500", icon: "✕" },

  // action level
  CONTINUE_MONITORING: { bg: "bg-slate-100", text: "text-slate-700", icon: "○", label: "Continue monitoring" },
  REVIEW_RECOMMENDED: { bg: "bg-amber-100", text: "text-amber-800", icon: "◐", label: "Review recommended" },
  PRIORITY_REVIEW: { bg: "bg-red-100", text: "text-red-800", icon: "●", label: "Priority review" },
};

export default function Badge({ value }: { value: string }) {
  const style = STYLES[value] || { bg: "bg-slate-100", text: "text-slate-700", icon: "•" };
  const label = style.label || value.replace(/_/g, " ");
  return (
    <span
      className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium ${style.bg} ${style.text}`}
    >
      <span aria-hidden="true">{style.icon}</span>
      {label}
    </span>
  );
}
