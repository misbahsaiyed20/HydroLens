import { Icon } from "@/components/ui/Icon";

type Tone = "neutral" | "info" | "caution" | "critical" | "success";

const TONE_STYLES: Record<Tone, string> = {
  neutral: "bg-slate-100 text-slate-600 ring-slate-200",
  info: "bg-aqua-50 text-aqua-700 ring-aqua-200",
  caution: "bg-amber-50 text-amber-800 ring-amber-200",
  critical: "bg-rose-50 text-rose-700 ring-rose-200",
  success: "bg-moss-50 text-moss-700 ring-moss-200",
};

const CONFIG: Record<string, { tone: Tone; icon: keyof typeof Icon; label?: string }> = {
  LOW: { tone: "neutral", icon: "Gauge" },
  NONE: { tone: "neutral", icon: "Gauge" },
  MODERATE: { tone: "caution", icon: "Gauge" },
  HIGH: { tone: "critical", icon: "Warning" },
  ELEVATED: { tone: "critical", icon: "Warning" },

  UNVERIFIED: { tone: "neutral", icon: "Clock", label: "Unverified" },
  VERIFIED: { tone: "success", icon: "Check", label: "Verified" },
  REJECTED: { tone: "neutral", icon: "X", label: "Rejected" },

  CONTINUE_MONITORING: { tone: "neutral", icon: "Gauge", label: "Continue monitoring" },
  REVIEW_RECOMMENDED: { tone: "caution", icon: "Warning", label: "Review recommended" },
  PRIORITY_REVIEW: { tone: "critical", icon: "Warning", label: "Priority review" },
};

export default function Badge({ value, size = "sm" }: { value: string; size?: "sm" | "md" }) {
  const cfg = CONFIG[value] || { tone: "neutral" as Tone, icon: "Gauge" as const };
  const label = cfg.label || value.replace(/_/g, " ");
  const IconCmp = Icon[cfg.icon];
  const sizing = size === "md" ? "px-3 py-1 text-sm" : "px-2.5 py-1 text-xs";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-pill font-medium ring-1 ring-inset ${TONE_STYLES[cfg.tone]} ${sizing}`}
    >
      <IconCmp className="h-3.5 w-3.5" />
      <span className="capitalize">{label.toLowerCase()}</span>
    </span>
  );
}
