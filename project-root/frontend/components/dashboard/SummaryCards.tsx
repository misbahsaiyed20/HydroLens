import { DashboardSummary } from "@/lib/api";
import { Icon } from "@/components/ui/Icon";

export default function SummaryCards({ summary }: { summary: DashboardSummary }) {
  const cards: { label: string; value: number; hint: string; icon: keyof typeof Icon; tone: string }[] = [
    { label: "Total reports", value: summary.total_reports, hint: "All citizen submissions", icon: "Droplet", tone: "text-ocean-600 bg-ocean-50" },
    { label: "Pending AI review", value: summary.pending_review, hint: "Not yet analyzed", icon: "Clock", tone: "text-slate-500 bg-slate-100" },
    { label: "Analyzed cases", value: summary.analyzed_reports, hint: "Eligible for review", icon: "Layers", tone: "text-aqua-600 bg-aqua-50" },
    { label: "High confidence", value: summary.high_confidence_cases, hint: "Strong corroborated evidence", icon: "Gauge", tone: "text-aqua-600 bg-aqua-50" },
    { label: "Requiring review", value: summary.cases_requiring_review, hint: "Review or priority review", icon: "Warning", tone: "text-amber-600 bg-amber-50" },
    { label: "Verified", value: summary.verified_cases, hint: "Human-confirmed", icon: "Check", tone: "text-moss-600 bg-moss-50" },
    { label: "Rejected", value: summary.rejected_cases, hint: "Human-rejected", icon: "X", tone: "text-slate-400 bg-slate-100" },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {cards.map((c) => {
        const CardIcon = Icon[c.icon];
        return (
          <div key={c.label} className="card p-4 sm:p-5">
            <span className={`mb-3 flex h-9 w-9 items-center justify-center rounded-lg ${c.tone}`}>
              <CardIcon className="h-4.5 w-4.5" />
            </span>
            <div className="text-2xl font-semibold text-ocean-900">{c.value}</div>
            <div className="text-sm font-medium text-ocean-700">{c.label}</div>
            <div className="mt-0.5 text-xs text-ocean-400">{c.hint}</div>
          </div>
        );
      })}
    </div>
  );
}
