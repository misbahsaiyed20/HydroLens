import { DashboardSummary } from "@/lib/api";

export default function SummaryCards({ summary }: { summary: DashboardSummary }) {
  const cards: { label: string; value: number; hint: string }[] = [
    { label: "Total reports", value: summary.total_reports, hint: "all citizen submissions" },
    { label: "Pending AI review", value: summary.pending_review, hint: "not yet analyzed" },
    { label: "Analyzed (cases)", value: summary.analyzed_reports, hint: "eligible for review" },
    { label: "High confidence", value: summary.high_confidence_cases, hint: "strong corroborated evidence" },
    { label: "Needs review", value: summary.cases_requiring_review, hint: "review or priority review" },
    { label: "Verified", value: summary.verified_cases, hint: "human-confirmed" },
    { label: "Rejected", value: summary.rejected_cases, hint: "human-rejected" },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {cards.map((c) => (
        <div key={c.label} className="rounded border border-slate-200 bg-white p-4">
          <div className="text-2xl font-semibold">{c.value}</div>
          <div className="text-sm font-medium text-slate-700">{c.label}</div>
          <div className="text-xs text-slate-400">{c.hint}</div>
        </div>
      ))}
    </div>
  );
}
