import Link from "next/link";
import { CaseSummary } from "@/lib/api";
import Badge from "@/components/ui/Badge";
import { Icon } from "@/components/ui/Icon";

const ACCENT: Record<string, string> = {
  CONTINUE_MONITORING: "border-l-slate-300",
  REVIEW_RECOMMENDED: "border-l-amber-400",
  PRIORITY_REVIEW: "border-l-rose-500",
};

export default function CaseCard({ c }: { c: CaseSummary }) {
  const isPriority = c.action_level === "PRIORITY_REVIEW";

  return (
    <Link
      href={`/cases/${c.report_id}`}
      className={`card-interactive block border-l-4 p-4 sm:p-5 ${ACCENT[c.action_level] || "border-l-slate-300"}`}
    >
      <div className="mb-3 flex flex-wrap items-center gap-2">
        {isPriority && (
          <span className="inline-flex items-center gap-1 rounded-pill bg-rose-600 px-2.5 py-1 text-xs font-semibold text-white">
            <Icon.Warning className="h-3.5 w-3.5" />
            Priority
          </span>
        )}
        <Badge value={c.confidence_level} />
        <Badge value={c.exposure_risk_level} />
        <Badge value={c.verification_status} />
      </div>

      <div className="mb-1 flex items-center gap-1.5 text-sm font-semibold text-ocean-900">
        <Icon.Pin className="h-4 w-4 flex-shrink-0 text-ocean-400" />
        {c.location.stream_name || "Unnamed location"}
        <span className="font-normal text-ocean-400">
          ({c.location.latitude.toFixed(4)}, {c.location.longitude.toFixed(4)})
        </span>
      </div>
      <p className="mb-3 text-sm leading-relaxed text-ocean-600">{c.condition_summary}</p>

      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-ocean-100 pt-3 text-xs text-ocean-400">
        <span className="flex items-center gap-1.5">
          <Icon.Layers className="h-3.5 w-3.5" />
          {c.supporting_count} supporting · {c.conflicting_count} conflicting
        </span>
        <span>{new Date(c.updated_at).toLocaleString()}</span>
      </div>
    </Link>
  );
}
