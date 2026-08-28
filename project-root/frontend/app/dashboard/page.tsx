"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DashboardSummary, getDashboardSummary } from "@/lib/api";
import SummaryCards from "@/components/dashboard/SummaryCards";
import { LoadingState, ErrorState } from "@/components/ui/States";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setError(null);
    setSummary(null);
    getDashboardSummary()
      .then(setSummary)
      .catch((e) => setError(e.message));
  }

  useEffect(load, []);

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <div className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">
        Development / officer workflow — no authentication yet
      </div>
      <h1 className="mb-1 text-2xl font-semibold">Dashboard</h1>
      <p className="mb-6 text-sm text-slate-600">
        Many imperfect observations → evidence fusion → trustworthy signal → human action.
      </p>

      {error && <ErrorState message={error} onRetry={load} />}
      {!error && !summary && <LoadingState label="Loading dashboard…" />}
      {summary && <SummaryCards summary={summary} />}

      <div className="mt-8">
        <Link href="/cases" className="text-sm font-medium text-blue-600 hover:underline">
          View all cases →
        </Link>
      </div>
    </main>
  );
}
