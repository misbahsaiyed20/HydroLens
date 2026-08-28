"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { CaseDetail, getCaseDetail, getFhirUrl } from "@/lib/api";
import Badge from "@/components/ui/Badge";
import { LoadingState, ErrorState } from "@/components/ui/States";
import EvidenceTimeline, { VerificationHistoryList } from "@/components/evidence/EvidenceTimeline";

export default function CaseDetailPage() {
  const params = useParams<{ id: string }>();
  const [c, setC] = useState<CaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setError(null);
    setC(null);
    getCaseDetail(params.id)
      .then(setC)
      .catch((e) => setError(e.message));
  }

  useEffect(load, [params.id]);

  if (error) return <main className="mx-auto max-w-3xl px-4 py-10"><ErrorState message={error} onRetry={load} /></main>;
  if (!c) return <main className="mx-auto max-w-3xl px-4 py-10"><LoadingState label="Loading case…" /></main>;

  return (
    <main className="mx-auto max-w-3xl space-y-8 px-4 py-10">
      {/* HEADER */}
      <div>
        <div className="mb-2 text-xs text-slate-400">Case {c.report_id}</div>
        <h1 className="mb-2 text-xl font-semibold">
          {c.location.stream_name || "Unnamed location"} ({c.location.latitude.toFixed(4)}, {c.location.longitude.toFixed(4)})
        </h1>
        <div className="flex flex-wrap gap-2">
          <Badge value={c.status} />
          <Badge value={c.verification_status} />
        </div>
      </div>

      {/* SIGNAL SUMMARY */}
      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Signal summary</h2>
        <p className="mb-3 text-sm text-slate-700">{c.condition_summary}</p>
        <div className="flex flex-wrap gap-2">
          <Badge value={c.confidence_level} />
          <Badge value={c.indicator_severity} />
          <Badge value={c.exposure_risk_level} />
          <Badge value={c.action_level} />
        </div>
        <p className="mt-2 text-sm text-slate-600">
          Confidence score: {c.confidence_score.toFixed(3)} · {c.recommended_action}
        </p>
      </section>

      {/* EVIDENCE */}
      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Evidence</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <div className="mb-1 text-xs font-medium text-slate-500">Supporting ({c.supporting_observations.length})</div>
            <ul className="space-y-1">
              {c.supporting_observations.map((o) => (
                <li key={o.report_id} className="rounded border border-slate-200 p-2 text-xs">
                  {o.distance_meters}m away, {o.minutes_apart}min apart — turbidity={o.turbidity_indicator ?? "?"}, quality={o.image_quality ?? "?"}{" "}
                  <Badge value={o.verification_status} />
                </li>
              ))}
              {c.supporting_observations.length === 0 && <li className="text-xs text-slate-400">None</li>}
            </ul>
          </div>
          <div>
            <div className="mb-1 text-xs font-medium text-slate-500">Conflicting ({c.conflicting_observations.length})</div>
            <ul className="space-y-1">
              {c.conflicting_observations.map((o) => (
                <li key={o.report_id} className="rounded border border-slate-200 p-2 text-xs">
                  {o.distance_meters}m away, {o.minutes_apart}min apart — turbidity={o.turbidity_indicator ?? "?"}{" "}
                  <Badge value={o.verification_status} />
                </li>
              ))}
              {c.conflicting_observations.length === 0 && <li className="text-xs text-slate-400">None</li>}
            </ul>
          </div>
        </div>
      </section>

      {/* BASELINE */}
      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Baseline</h2>
        {c.baseline.available ? (
          <p className="text-sm text-slate-700">
            Based on {c.baseline.historical_observation_count} historical observation(s): typical turbidity{" "}
            {c.baseline.turbidity_baseline ?? "n/a"}, typical algae {c.baseline.algae_baseline ?? "n/a"}.{" "}
            {c.baseline.deviates ? "This report deviates from baseline." : "Consistent with baseline."}
          </p>
        ) : (
          <p className="text-sm text-slate-500">No baseline available yet for this location.</p>
        )}
      </section>

      {/* EXPLANATION */}
      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Why this signal</h2>
        <ul className="list-inside list-disc space-y-1 text-sm text-slate-700">
          {c.evidence_reasons.map((r, i) => (
            <li key={i}>{r}</li>
          ))}
        </ul>
      </section>

      {/* TIMELINE */}
      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Evidence timeline</h2>
        <EvidenceTimeline c={c} />
      </section>

      {/* VERIFICATION */}
      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Verification history</h2>
        <VerificationHistoryList c={c} />
      </section>

      {/* FHIR */}
      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">FHIR representation</h2>
        <a href={getFhirUrl(c.report_id)} target="_blank" rel="noreferrer" className="text-sm text-blue-600 hover:underline">
          View FHIR Observation resource →
        </a>
      </section>
    </main>
  );
}
