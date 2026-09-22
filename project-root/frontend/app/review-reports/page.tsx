"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { getImageUrl, getReviewerReports, ReportListResult } from "@/lib/api";
import Badge from "@/components/ui/Badge";
import RemoteImage from "@/components/ui/RemoteImage";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/States";
import { Icon } from "@/components/ui/Icon";
import { useAuth } from "@/contexts/AuthContext";

function detectionSummary(r: ReportListResult["items"][number]) {
  const o = r.observation;

  if (!o) {
    return r.status === "ANALYZED"
      ? "Analysis complete; evidence can be reviewed."
      : "Awaiting AI analysis.";
  }

  const parts = [
    o.turbidity_indicator && o.turbidity_indicator !== "none"
      ? `turbidity ${o.turbidity_indicator}`
      : null,
    o.algae_indicator && o.algae_indicator !== "none"
      ? `algae ${o.algae_indicator}`
      : null,
    o.visible_waste ? "visible waste" : null,
    o.color_anomaly && o.color_anomaly !== "none"
      ? `color ${o.color_anomaly}`
      : null,
  ].filter(Boolean);

  return parts.length
    ? `Detected: ${parts.join(" · ")}`
    : "No obvious visual anomaly recorded.";
}

function ReviewReportsContent() {
  const { token } = useAuth();
  const params = useSearchParams();

  const [result, setResult] = useState<ReportListResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [verification, setVerification] = useState("");

  const pending = params.get("pending") === "true";

  useEffect(() => {
    if (!token) return;

    setError(null);

    getReviewerReports(token, {
      verification_status: verification || undefined,
      limit: 100,
      search: search.trim() || undefined,
    })
      .then(setResult)
      .catch((e) => setError(e.message));
  }, [token, verification, search]);

  const visibleItems = useMemo(() => {
    if (!result) return [];

    if (!pending) return result.items;

    return result.items.filter(
      (r) => r.status === "SUBMITTED" || r.status === "ANALYZING"
    );
  }, [pending, result]);

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <span className="section-title">Reviewer workspace</span>
          <h1 className="mt-2 text-2xl font-semibold text-ocean-900">
            Review queue
          </h1>
          <p className="mt-1 text-sm text-ocean-500">
            All citizen submissions, including reports still waiting for AI
            analysis.
          </p>
        </div>

        {result && (
          <span className="text-xs text-ocean-400">
            {visibleItems.length} shown
          </span>
        )}
      </div>

      <div className="mb-5 flex flex-col gap-3 md:flex-row">
        <div className="relative flex-1">
          <Icon.Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ocean-300" />

          <input
            className="input-field pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search report ID or stream name…"
            aria-label="Search reviewer reports"
          />
        </div>

        <select
          className="input-field md:w-48"
          value={verification}
          onChange={(e) => setVerification(e.target.value)}
          aria-label="Filter by verification status"
        >
          <option value="">Verification: any</option>
          <option value="UNVERIFIED">Unverified</option>
          <option value="VERIFIED">Verified</option>
          <option value="REJECTED">Rejected</option>
        </select>

        {pending && (
          <Link href="/review-reports" className="btn-secondary">
            Show all
          </Link>
        )}
      </div>

      {error && <ErrorState message={error} />}

      {!error && !result && (
        <LoadingState label="Loading review queue…" rows={5} />
      )}

      {result && visibleItems.length === 0 && (
        <EmptyState
          message="No reports match this view."
          hint="Try another search or filter."
        />
      )}

      {result && visibleItems.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {visibleItems.map((r) => (
            <Link
              key={r.id}
              href={`/review-reports/${r.id}`}
              className="card-interactive overflow-hidden"
            >
              <div className="grid min-h-[180px] sm:grid-cols-[145px_1fr]">
                <RemoteImage
                  src={getImageUrl(r.image_path)}
                  alt="Reported water observation"
                  className="h-full min-h-[180px] w-full object-cover"
                />

                <div className="p-4 sm:p-5">
                  <div className="mb-3 flex flex-wrap gap-2">
                    <Badge value={r.status} />
                    <Badge value={r.verification_status} />
                  </div>

                  <div className="text-sm font-semibold text-ocean-900">
                    {r.location.stream_name || "Unnamed location"}
                  </div>

                  <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-ocean-600">
                    {detectionSummary(r)}
                  </p>

                  <div className="mt-4 flex items-center justify-between text-xs text-ocean-400">
                    <span>
                      {new Date(r.submitted_at).toLocaleString()}
                    </span>

                    <span className="font-medium text-aqua-700">
                      Open report{" "}
                      <Icon.ArrowRight className="ml-1 inline h-3.5 w-3.5" />
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

export default function ReviewReportsPage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
          <LoadingState label="Loading review queue…" rows={5} />
        </main>
      }
    >
      <ReviewReportsContent />
    </Suspense>
  );
}