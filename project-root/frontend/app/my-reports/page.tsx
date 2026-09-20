"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getImageUrl, getMyReports, ReportListResult } from "@/lib/api";
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
    <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <div className="mb-7 flex flex-wrap items-start justify-between gap-4">
        <div>
          <span className="section-title">Citizen space</span>
          <h1 className="mt-2 text-2xl font-semibold text-ocean-900">My reports</h1>
          <p className="mt-1 text-sm text-ocean-500">Track what you submitted and see what HydroLens detected.</p>
        </div>
        <Link href="/#report" className="btn-primary">
          <Icon.Upload className="h-4 w-4" />
          New report
        </Link>
      </div>

      {error && <ErrorState message={error} onRetry={load} />}
      {!error && !result && <LoadingState label="Loading your reports…" />}
      {result && result.items.length === 0 && (
        <EmptyState
          message="You haven't submitted any observations yet."
          hint="Upload a water-body photo from the home page and it will appear here."
        />
      )}

      {result && result.items.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {result.items.map((r) => (
            <Link key={r.id} href={`/reports/${r.id}`} className="card-interactive overflow-hidden">
              <div className="grid grid-cols-[110px_1fr]">
                <div className="h-full min-h-[135px] bg-ocean-50">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={getImageUrl(r.image_path)}
                    alt="Submitted water observation"
                    className="h-full w-full object-cover"
                    loading="lazy"
                  />
                </div>
                <div className="p-4 sm:p-5">
                  <div className="mb-3 flex flex-wrap gap-2">
                    <Badge value={r.status} />
                    <Badge value={r.verification_status} />
                  </div>
                  <div className="flex items-start gap-1.5 text-sm font-semibold text-ocean-900">
                    <Icon.Pin className="mt-0.5 h-4 w-4 flex-shrink-0 text-ocean-400" />
                    <span>{r.location.stream_name || "Unnamed location"}</span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-sm text-ocean-600">
                    {r.observation?.turbidity_indicator || r.observation?.algae_indicator || r.observation?.visible_waste
                      ? `Detected: ${[
                          r.observation?.turbidity_indicator && `turbidity ${r.observation.turbidity_indicator}`,
                          r.observation?.algae_indicator && `algae ${r.observation.algae_indicator}`,
                          r.observation?.visible_waste ? "visible waste" : null,
                        ]
                          .filter(Boolean)
                          .join(" · ")}`
                      : "No notable visual indicator recorded yet."}
                  </p>
                  <div className="mt-3 flex items-center justify-between gap-3 text-xs text-ocean-400">
                    <span>{new Date(r.submitted_at).toLocaleString()}</span>
                    <span className="inline-flex items-center gap-1 font-medium text-aqua-700">
                      View observation <Icon.ArrowRight className="h-3.5 w-3.5" />
                    </span>
                  </div>
                </div>
              </div>
            </Link>
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
