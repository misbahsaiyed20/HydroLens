"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CaseListResult, DashboardSummary, getCases, getDashboardSummary } from "@/lib/api";
import SummaryCards from "@/components/dashboard/SummaryCards";
import CaseCard from "@/components/cases/CaseCard";
import { LoadingState, ErrorState, EmptyState } from "@/components/ui/States";
import { Icon } from "@/components/ui/Icon";
import RequireRole from "@/components/RequireRole";
import { useAuth } from "@/contexts/AuthContext";

function DashboardContent() {
  const { token } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [queue, setQueue] = useState<CaseListResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    setError(null);
    try {
      const [summaryResult, queueResult] = await Promise.all([
        getDashboardSummary(token),
        getCases(token, { review_needed: true, limit: 5 }),
      ]);
      setSummary(summaryResult);
      setQueue(queueResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load dashboard.");
    }
  }

  useEffect(() => { load(); }, [token]);

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="mb-7 flex flex-wrap items-start justify-between gap-4">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-pill bg-ocean-50 px-2.5 py-1 text-[11px] font-medium uppercase tracking-wide text-ocean-500">Environmental officer workspace</span>
          <h1 className="mt-2 text-2xl font-semibold text-ocean-900">Dashboard</h1>
          <p className="mt-1 max-w-2xl text-sm text-ocean-500">Monitor incoming observations, open the numbers, and move from signal to review.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/review-reports?pending=true" className="btn-secondary text-xs">Incoming reports <Icon.ArrowRight className="h-3.5 w-3.5" /></Link>
          <Link href="/cases?review_needed=true" className="btn-primary text-xs">Review queue <Icon.ArrowRight className="h-3.5 w-3.5" /></Link>
        </div>
      </div>

      {error && <ErrorState message={error} onRetry={load} />}
      {!error && !summary && <LoadingState label="Loading dashboard…" rows={3} />}
      {summary && <SummaryCards summary={summary} />}

      {summary && (
        <section className="mt-8">
          <div className="mb-4 flex items-end justify-between gap-4"><div><span className="section-title">Needs attention</span><h2 className="mt-1 text-lg font-semibold text-ocean-900">Recent review queue</h2></div><Link href="/cases?review_needed=true" className="text-xs font-medium text-aqua-700 hover:text-aqua-800">Open full queue <Icon.ArrowRight className="ml-1 inline h-3.5 w-3.5" /></Link></div>
          {queue && queue.items.length > 0 ? <div className="space-y-3">{queue.items.map((c) => <CaseCard key={c.report_id} c={c} />)}</div> : <EmptyState message="No cases currently require review." hint="New analyzed reports will appear here when their actionability calls for reviewer attention." />}
        </section>
      )}
    </main>
  );
}

export default function DashboardPage() {
  return <RequireRole role="REVIEWER"><DashboardContent /></RequireRole>;
}
