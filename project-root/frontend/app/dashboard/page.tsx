"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DashboardSummary, getDashboardSummary } from "@/lib/api";
import SummaryCards from "@/components/dashboard/SummaryCards";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { Icon } from "@/components/ui/Icon";
import RequireRole from "@/components/RequireRole";
import { useAuth } from "@/contexts/AuthContext";

function DashboardContent() {
  const { token } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    if (!token) return;
    setError(null);
    setSummary(null);
    getDashboardSummary(token)
      .then(setSummary)
      .catch((e) => setError(e.message));
  }

  useEffect(load, [token]);

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-pill bg-ocean-50 px-2.5 py-1 text-[11px] font-medium uppercase tracking-wide text-ocean-500">
            Reviewer workspace
          </span>
          <h1 className="mt-2 text-2xl font-semibold text-ocean-900">Dashboard</h1>
          <p className="mt-1 max-w-xl text-sm text-ocean-500">
            Many imperfect observations → evidence fusion → trustworthy signal → human action.
          </p>
        </div>
        <Link href="/cases" className="btn-secondary">
          View all cases
          <Icon.ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {error && <ErrorState message={error} onRetry={load} />}
      {!error && !summary && <LoadingState label="Loading dashboard…" rows={2} />}
      {summary && <SummaryCards summary={summary} />}
    </main>
  );
}

export default function DashboardPage() {
  return (
    <RequireRole role="REVIEWER">
      <DashboardContent />
    </RequireRole>
  );
}
