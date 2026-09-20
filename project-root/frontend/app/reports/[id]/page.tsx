"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { getImageUrl, getReport, ReportOut } from "@/lib/api";
import Badge from "@/components/ui/Badge";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { Icon } from "@/components/ui/Icon";
import RequireRole from "@/components/RequireRole";
import { useAuth } from "@/contexts/AuthContext";

function indicatorValue(value: string | null | undefined, fallback = "Not detected") {
  if (!value || value === "none") return fallback;
  return value.replace(/_/g, " ");
}

function CitizenReportDetailContent() {
  const { token } = useAuth();
  const params = useParams<{ id: string }>();
  const reportId = params.id;
  const [report, setReport] = useState<ReportOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !reportId) return;
    setError(null);
    getReport(token, reportId)
      .then(setReport)
      .catch((e) => setError(e.message));
  }, [reportId, token]);

  const summary = useMemo(() => {
    const o = report?.observation;
    if (!o) return "Your photo has not finished AI analysis yet.";
    const parts = [
      o.turbidity_indicator && o.turbidity_indicator !== "clear" && o.turbidity_indicator !== "none"
        ? `Turbidity appears ${indicatorValue(o.turbidity_indicator)}`
        : null,
      o.algae_indicator && o.algae_indicator !== "none" ? `algae indicator: ${indicatorValue(o.algae_indicator)}` : null,
      o.visible_waste ? "visible waste detected" : null,
      o.color_anomaly && o.color_anomaly !== "none" ? `color anomaly: ${o.color_anomaly}` : null,
    ].filter(Boolean);

    return parts.length > 0
      ? `HydroLens detected ${parts.join(", ")}.`
      : "HydroLens did not record an obvious visual anomaly in this observation.";
  }, [report]);

  if (error)
    return (
      <main className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        <ErrorState message={error} />
      </main>
    );

  if (!report)
    return (
      <main className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        <LoadingState label="Loading your observation…" rows={3} />
      </main>
    );

  const o = report.observation;

  return (
    <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <Link href="/my-reports" className="inline-flex items-center gap-1.5 text-sm font-medium text-ocean-500 hover:text-ocean-700">
        <Icon.ArrowRight className="h-3.5 w-3.5 rotate-180" />
        Back to my reports
      </Link>

      <div className="mt-5 grid gap-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-start">
        <div className="overflow-hidden rounded-[24px] border border-ocean-200 bg-ocean-900 shadow-card">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={getImageUrl(report.image_path)}
            alt="Your submitted water observation"
            className="aspect-[4/3] w-full object-cover"
          />
        </div>

        <div className="space-y-5">
          <div>
            <span className="section-title">Your observation</span>
            <h1 className="mt-2 text-2xl font-semibold text-ocean-900">
              {report.location.stream_name || "Water-body observation"}
            </h1>
            <p className="mt-1 text-xs text-ocean-400">
              Submitted {new Date(report.submitted_at).toLocaleString()}
            </p>

            <div className="mt-4 flex flex-wrap gap-2">
              <Badge value={report.status} />
              <Badge value={report.verification_status} size="md" />
            </div>
          </div>

          <section className="card p-5">
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-ocean-50 text-ocean-500">
                <Icon.Gauge className="h-4 w-4" />
              </span>
              <h2 className="text-sm font-semibold text-ocean-900">What HydroLens detected</h2>
            </div>

            <p className="mt-4 text-sm leading-relaxed text-ocean-700">{summary}</p>

            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-ocean-50 p-3">
                <div className="text-[10px] font-medium uppercase tracking-wider text-ocean-400">Turbidity</div>
                <div className="mt-1 text-sm font-semibold capitalize text-ocean-900">{indicatorValue(o?.turbidity_indicator)}</div>
              </div>
              <div className="rounded-xl bg-ocean-50 p-3">
                <div className="text-[10px] font-medium uppercase tracking-wider text-ocean-400">Algae</div>
                <div className="mt-1 text-sm font-semibold capitalize text-ocean-900">{indicatorValue(o?.algae_indicator)}</div>
              </div>
              <div className="rounded-xl bg-ocean-50 p-3">
                <div className="text-[10px] font-medium uppercase tracking-wider text-ocean-400">Visible waste</div>
                <div className="mt-1 text-sm font-semibold text-ocean-900">{o?.visible_waste ? "Detected" : "Not detected"}</div>
              </div>
              <div className="rounded-xl bg-ocean-50 p-3">
                <div className="text-[10px] font-medium uppercase tracking-wider text-ocean-400">Image quality</div>
                <div className="mt-1 text-sm font-semibold capitalize text-ocean-900">{indicatorValue(o?.image_quality)}</div>
              </div>
            </div>

            {o?.color_anomaly && o.color_anomaly !== "none" && (
              <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-3">
                <div className="text-[10px] font-medium uppercase tracking-wider text-amber-700">Color anomaly</div>
                <div className="mt-1 text-sm font-semibold capitalize text-amber-900">{o.color_anomaly}</div>
              </div>
            )}

            <div className="mt-3 flex items-center justify-between rounded-xl border border-ocean-100 bg-white px-3 py-2.5 text-xs">
              <span className="text-ocean-500">AI model confidence</span>
              <span className="font-semibold text-ocean-800">
                {o?.model_confidence != null ? o.model_confidence.toFixed(2) : "—"}
              </span>
            </div>
          </section>

          <section className="card p-5">
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-ocean-50 text-ocean-500">
                <Icon.Shield className="h-4 w-4" />
              </span>
              <h2 className="text-sm font-semibold text-ocean-900">Review status</h2>
            </div>

            <div className="mt-4 space-y-3">
              {[
                ["Submitted", true],
                ["AI analysis", report.status === "ANALYZED" || report.status === "UNDER_REVIEW" || report.status === "VERIFIED" || report.status === "DISMISSED"],
                ["Human review", report.verification_status !== "UNVERIFIED"],
              ].map(([label, done]) => (
                <div key={String(label)} className="flex items-center gap-3">
                  <span
                    className={`flex h-6 w-6 items-center justify-center rounded-full ${
                      done ? "bg-moss-100 text-moss-700" : "bg-ocean-50 text-ocean-300"
                    }`}
                  >
                    <Icon.Check className="h-3.5 w-3.5" />
                  </span>
                  <span className={`text-sm ${done ? "font-medium text-ocean-800" : "text-ocean-400"}`}>{label}</span>
                </div>
              ))}
            </div>

            <p className="mt-4 rounded-xl border border-ocean-100 bg-ocean-50/60 p-3 text-xs leading-relaxed text-ocean-600">
              {report.verification_status === "VERIFIED"
                ? "A human reviewer has accepted this observation as a reasonable interpretation of the submitted image."
                : report.verification_status === "REJECTED"
                  ? "A human reviewer rejected this observation for evidentiary use."
                  : "This observation has not yet been human-verified."}
            </p>
          </section>

          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-relaxed text-amber-900">
            HydroLens reports visible image-based indicators only. This is not a laboratory water-quality measurement.
          </div>
        </div>
      </div>
    </main>
  );
}

export default function CitizenReportDetailPage() {
  return (
    <RequireRole role="CITIZEN">
      <CitizenReportDetailContent />
    </RequireRole>
  );
}
