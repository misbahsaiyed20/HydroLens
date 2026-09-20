import Link from "next/link";
import { DashboardSummary } from "@/lib/api";
import { Icon } from "@/components/ui/Icon";

export default function SummaryCards({ summary }: { summary: DashboardSummary }) {
  const cards: { label: string; value: number; hint: string; icon: keyof typeof Icon; tone: string; href: string }[] = [
    { label: "Total reports", value: summary.total_reports, hint: "All citizen submissions", icon: "Droplet", tone: "text-ocean-600 bg-ocean-50", href: "/review-reports" },
    { label: "Pending AI review", value: summary.pending_review, hint: "Waiting for analysis", icon: "Clock", tone: "text-slate-500 bg-slate-100", href: "/review-reports?pending=true" },
    { label: "Analyzed cases", value: summary.analyzed_reports, hint: "Eligible for review", icon: "Layers", tone: "text-aqua-600 bg-aqua-50", href: "/cases" },
    { label: "High confidence", value: summary.high_confidence_cases, hint: "High-confidence cases", icon: "Gauge", tone: "text-aqua-600 bg-aqua-50", href: "/cases?confidence_level=HIGH" },
    { label: "Requiring review", value: summary.cases_requiring_review, hint: "Review or priority review", icon: "Warning", tone: "text-amber-600 bg-amber-50", href: "/cases?review_needed=true" },
    { label: "Verified", value: summary.verified_cases, hint: "Human-confirmed reports", icon: "Check", tone: "text-moss-600 bg-moss-50", href: "/review-reports?verification_status=VERIFIED" },
    { label: "Rejected", value: summary.rejected_cases, hint: "Human-rejected reports", icon: "X", tone: "text-slate-400 bg-slate-100", href: "/review-reports?verification_status=REJECTED" },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {cards.map((c) => {
        const CardIcon = Icon[c.icon];
        return (
          <Link key={c.label} href={c.href} className="card-interactive block p-4 sm:p-5">
            <div className="flex items-start justify-between gap-3">
              <span className={`flex h-9 w-9 items-center justify-center rounded-lg ${c.tone}`}>
                <CardIcon className="h-4 w-4" />
              </span>
              <Icon.ArrowRight className="h-3.5 w-3.5 text-ocean-300" />
            </div>
            <div className="mt-3 text-2xl font-semibold text-ocean-900">{c.value}</div>
            <div className="text-sm font-medium text-ocean-700">{c.label}</div>
            <div className="mt-0.5 text-xs text-ocean-400">{c.hint}</div>
          </Link>
        );
      })}
    </div>
  );
}
