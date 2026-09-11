"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getMyReports, ReportListResult } from "@/lib/api";
import Badge from "@/components/ui/Badge";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/States";
import { Icon } from "@/components/ui/Icon";
import RequireRole from "@/components/RequireRole";
import { useAuth } from "@/contexts/AuthContext";

function MyReportsContent() {
  const { token } = useAuth();
  const [result, setResult] = useState<ReportListResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    if (!token) return;
    setError(null);
    setResult(null);
    getMyReports(token)
      .then(setResult)
      .catch((e) => setError(e.message));
  }

  useEffect(load, [token]);

  return (
    <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-ocean-900">My reports</h1>
          <p className="mt-1 text-sm text-ocean-500">Observations you&apos;ve submitted and their status.</p>
        </div>
        <Link href="/" className="btn-primary">
          <Icon.Upload className="h-4 w-4" />
          New report
        </Link>
      </div>

      {error && <ErrorState message={error} onRetry={load} />}
      {!error && !result && <LoadingState label="Loading your reports…" />}
      {result && result.items.length === 0 && (
        <EmptyState message="You haven't submitted any observations yet." hint="Report a stream condition from the home page to see it here." />
      )}

      {result && result.items.length > 0 && (
        <div className="space-y-3">
          {result.items.map((r) => (
            <div key={r.id} className="card p-4 sm:p-5">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Badge value={r.status} />
                <Badge value={r.verification_status} />
              </div>
              <div className="mb-1 flex items-center gap-1.5 text-sm font-semibold text-ocean-900">
                <Icon.Pin className="h-4 w-4 flex-shrink-0 text-ocean-400" />
                {r.location.stream_name || "Unnamed location"}
              </div>
              {r.description && <p className="text-sm text-ocean-600">{r.description}</p>}
              <div className="mt-2 text-xs text-ocean-400">
                Submitted {new Date(r.submitted_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}

export default function MyReportsPage() {
  return (
    <RequireRole role="CITIZEN">
      <MyReportsContent />
    </RequireRole>
  );
}
