import Link from "next/link";
import { CaseSummary } from "@/lib/api";
import Badge from "@/components/ui/Badge";

export default function CaseCard({ c }: { c: CaseSummary }) {
  return (
    <Link
      href={`/cases/${c.report_id}`}
      className="block rounded border border-slate-200 bg-white p-4 hover:border-slate-400"
    >
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <Badge value={c.confidence_level} />
        <Badge value={c.exposure_risk_level} />
        <Badge value={c.action_level} />
        <Badge value={c.verification_status} />
      </div>
      <div className="mb-1 text-sm font-medium">
        {c.location.stream_name || "Unnamed location"} ({c.location.latitude.toFixed(4)}, {c.location.longitude.toFixed(4)})
      </div>
      <p className="mb-2 text-sm text-slate-600">{c.condition_summary}</p>
      <div className="flex justify-between text-xs text-slate-400">
        <span>{c.supporting_count} supporting · {c.conflicting_count} conflicting</span>
        <span>{new Date(c.updated_at).toLocaleString()}</span>
      </div>
    </Link>
  );
}
