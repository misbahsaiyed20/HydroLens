"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getImageUrl, getMyReports, ReportListResult } from "@/lib/api";
import Badge from "@/components/ui/Badge";
import RemoteImage from "@/components/ui/RemoteImage";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/States";
import { Icon } from "@/components/ui/Icon";
import RequireRole from "@/components/RequireRole";
import { useAuth } from "@/contexts/AuthContext";

function detectionSummary(report: ReportListResult["items"][number]) {
  const o = report.observation;
  if (!o) return report.status === "ANALYZED" ? "Analysis is complete." : "Waiting for AI analysis.";
  const parts = [
    o.turbidity_indicator && o.turbidity_indicator !== "none" ? `turbidity ${o.turbidity_indicator}` : null,
    o.algae_indicator && o.algae_indicator !== "none" ? `algae ${o.algae_indicator}` : null,
    o.visible_waste ? "visible waste" : null,
    o.color_anomaly && o.color_anomaly !== "none" ? `color ${o.color_anomaly}` : null,
  ].filter(Boolean);
  return parts.length ? `Detected: ${parts.join(" · ")}` : "No obvious visual anomaly recorded.";
}

function MyReportsContent() {
  const { token } = useAuth();
  const [result, setResult] = useState<ReportListResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    if (!token) return;
    setError(null);
    setResult(null);
    getMyReports(token).then(setResult).catch((e) => setError(e.message));
  }

  useEffect(load, [token]);

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="mb-7 flex flex-wrap items-start justify-between gap-4">
        <div>
          <span className="section-title">Citizen space</span>
          <h1 className="mt-2 text-2xl font-semibold text-ocean-900">My reports</h1>
          <p className="mt-1 text-sm text-ocean-500">Track every submission, what HydroLens detected, and its review status.</p>
        </div>
        <Link href="/#report" className="btn-primary">
          <Icon.Upload className="h-4 w-4" />
          New report
        </Link>
      </div>

      {error && <ErrorState message={error} onRetry={load} />}
      {!error && !result && <LoadingState label="Loading your reports…" rows={3} />}
      {result && result.items.length === 0 && (
        <EmptyState message="You haven't submitted any observations yet." hint="Add your first water-body photo from the report page." />
      )}

      {result && result.items.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {result.items.map((r) => (
            <Link key={r.id} href={`/reports/${r.id}`} className="card-interactive overflow-hidden">
              <div className="grid min-h-[190px] sm:grid-cols-[170px_1fr]">
                <RemoteImage
                  src={getImageUrl(r.image_path)}
                  alt="Submitted water observation"
                  className="h-full min-h-[190px] w-full object-cover"
                />
                <div className="flex flex-col p-4 sm:p-5">
                  <div className="mb-3 flex flex-wrap gap-2">
                    <Badge value={r.status} />
                    <Badge value={r.verification_status} />
                  </div>

                  <div className="flex items-start gap-1.5 text-sm font-semibold text-ocean-900">
                    <Icon.Pin className="mt-0.5 h-4 w-4 flex-shrink-0 text-ocean-400" />
                    <span>{r.location.stream_name || "Unnamed location"}</span>
                  </div>

                  <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-ocean-600">{detectionSummary(r)}</p>

                  <div className="mt-auto flex items-center justify-between gap-3 pt-4 text-xs text-ocean-400">
                    <span>{new Date(r.submitted_at).toLocaleString()}</span>
                    <span className="inline-flex items-center gap-1 font-medium text-aqua-700">View details <Icon.ArrowRight className="h-3.5 w-3.5" /></span>
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
