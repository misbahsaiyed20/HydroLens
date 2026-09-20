"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { CaseDetail, getCaseDetail, getFhirResource, getImageUrl, submitVerification } from "@/lib/api";
import Badge from "@/components/ui/Badge";
import { LoadingState, ErrorState } from "@/components/ui/States";
import EvidenceTimeline, { VerificationHistoryList } from "@/components/evidence/EvidenceTimeline";
import { Icon } from "@/components/ui/Icon";
import RequireRole from "@/components/RequireRole";
import { useAuth } from "@/contexts/AuthContext";

function SectionHeading({ icon, title }: { icon: keyof typeof Icon; title: string }) {
  const Ic = Icon[icon];
  return (
    <div className="mb-3 flex items-center gap-2">
      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-ocean-50 text-ocean-500">
        <Ic className="h-3.5 w-3.5" />
      </span>
      <h2 className="section-title">{title}</h2>
    </div>
  );
}

function ObservationCard({
  o,
  kind,
}: {
  o: CaseDetail["supporting_observations"][number];
  kind: "supporting" | "conflicting";
}) {
  return (
    <li className={`rounded-lg border p-3 text-xs ${kind === "supporting" ? "border-moss-200 bg-moss-50/40" : "border-rose-200 bg-rose-50/40"}`}>
      <div className="mb-1.5 flex items-center justify-between">
        <span className="font-medium text-ocean-700">{o.distance_meters}m away · {o.minutes_apart}min apart</span>
        <Badge value={o.verification_status} />
      </div>
      <div className="text-ocean-500">
        Turbidity: {o.turbidity_indicator ?? "—"} · Quality: {o.image_quality ?? "—"}
        {kind === "supporting" && o.algae_indicator ? ` · Algae: ${o.algae_indicator}` : ""}
      </div>
    </li>
  );
}

export default function CaseDetailPage() {
  return (
    <RequireRole role="REVIEWER">
      <CaseDetailContent />
    </RequireRole>
  );
}

function CaseDetailContent() {
  const params = useParams<{ id: string }>();
  const { token } = useAuth();
  const [c, setC] = useState<CaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fhir, setFhir] = useState<Record<string, unknown> | null>(null);
  const [fhirLoading, setFhirLoading] = useState(false);
  const [verifying, setVerifying] = useState<"VERIFIED" | "REJECTED" | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  function load() {
    if (!token) return;
    setError(null);
    setC(null);
    getCaseDetail(token, params.id)
      .then(setC)
      .catch((e) => setError(e.message));
  }

  useEffect(load, [params.id, token]);

  async function toggleFhir() {
    if (fhir) {
      setFhir(null);
      return;
    }
    if (!token) return;
    setFhirLoading(true);
    try {
      setFhir(await getFhirResource(token, params.id));
    } catch {
      setFhir(null);
    } finally {
      setFhirLoading(false);
    }
  }

  async function handleVerify(status: "VERIFIED" | "REJECTED") {
    if (!token) return;
    setVerifying(status);
    setVerifyError(null);
    try {
      await submitVerification(token, params.id, status);
      load();
    } catch (err) {
      setVerifyError(err instanceof Error ? err.message : "Action failed.");
    } finally {
      setVerifying(null);
    }
  }

  if (error)
    return (
      <main className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        <ErrorState message={error} onRetry={load} />
      </main>
    );
  if (!c)
    return (
      <main className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        <LoadingState label="Loading case…" />
      </main>
    );

  const isPriority = c.action_level === "PRIORITY_REVIEW";

  return (
    <main className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6">
      <Link href="/cases" className="inline-flex items-center gap-1.5 text-sm font-medium text-ocean-500 hover:text-ocean-700">
        <Icon.ArrowRight className="h-3.5 w-3.5 rotate-180" />
        Back to cases
      </Link>

      {/* HEADER */}
      <div className={`card p-5 sm:p-6 ${isPriority ? "border-l-4 border-l-rose-500" : "border-l-4 border-l-ocean-200"}`}>
        <div className="mb-2 text-xs font-mono text-ocean-400">Case {c.report_id}</div>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <h1 className="flex items-center gap-2 text-xl font-semibold text-ocean-900">
            <Icon.Pin className="h-5 w-5 flex-shrink-0 text-ocean-400" />
            {c.location.stream_name || "Unnamed location"}
            <span className="text-sm font-normal text-ocean-400">
              ({c.location.latitude.toFixed(4)}, {c.location.longitude.toFixed(4)})
            </span>
          </h1>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <Badge value={c.status} />
          <Badge value={c.verification_status} size="md" />
          {isPriority && (
            <span className="inline-flex items-center gap-1 rounded-pill bg-rose-600 px-3 py-1 text-sm font-semibold text-white">
              <Icon.Warning className="h-4 w-4" />
              Priority review
            </span>
          )}
        </div>
      </div>

      <div className="overflow-hidden rounded-[24px] border border-ocean-200 bg-ocean-900 shadow-card">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={getImageUrl(c.image_path)}
          alt="Water observation for this case"
          className="aspect-[16/7] w-full object-cover"
          onError={(event) => {
            event.currentTarget.style.display = "none";
          }}
        />
      </div>

      {/* SIGNAL SUMMARY */}
      <section className="card p-5 sm:p-6">
        <SectionHeading icon="Gauge" title="Signal summary" />
        <p className="mb-4 text-[15px] leading-relaxed text-ocean-800">{c.condition_summary}</p>

        <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg bg-ocean-50 p-3">
            <div className="text-[11px] font-medium uppercase tracking-wide text-ocean-400">Confidence</div>
            <div className="mt-1 text-lg font-semibold text-ocean-900">{c.confidence_score.toFixed(2)}</div>
          </div>
          <div className="rounded-lg bg-ocean-50 p-3">
            <div className="text-[11px] font-medium uppercase tracking-wide text-ocean-400">Severity</div>
            <div className="mt-1 text-lg font-semibold capitalize text-ocean-900">{c.indicator_severity.toLowerCase()}</div>
          </div>
          <div className="rounded-lg bg-ocean-50 p-3">
            <div className="text-[11px] font-medium uppercase tracking-wide text-ocean-400">Exposure risk</div>
            <div className="mt-1 text-lg font-semibold capitalize text-ocean-900">{c.exposure_risk_level.toLowerCase()}</div>
          </div>
          <div className="rounded-lg bg-ocean-50 p-3">
            <div className="text-[11px] font-medium uppercase tracking-wide text-ocean-400">Recommended action</div>
            <div className="mt-1 text-sm font-semibold text-ocean-900">{c.recommended_action}</div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Badge value={c.confidence_level} />
          <Badge value={c.indicator_severity} />
          <Badge value={c.exposure_risk_level} />
          <Badge value={c.action_level} />
        </div>
      </section>

      {/* EVIDENCE */}
      <section className="card p-5 sm:p-6">
        <SectionHeading icon="Layers" title="Evidence" />
        <p className="mb-3 text-xs text-ocean-400">
          {c.supporting_observations.length + c.conflicting_observations.length} nearby observation(s) considered for this signal.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-moss-700">
              <Icon.Check className="h-3.5 w-3.5" />
              Supporting ({c.supporting_observations.length})
            </div>
            <ul className="space-y-2">
              {c.supporting_observations.map((o) => (
                <ObservationCard key={o.report_id} o={o} kind="supporting" />
              ))}
              {c.supporting_observations.length === 0 && <li className="text-xs text-ocean-400">None</li>}
            </ul>
          </div>
          <div>
            <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-rose-700">
              <Icon.X className="h-3.5 w-3.5" />
              Conflicting ({c.conflicting_observations.length})
            </div>
            <ul className="space-y-2">
              {c.conflicting_observations.map((o) => (
                <ObservationCard key={o.report_id} o={o} kind="conflicting" />
              ))}
              {c.conflicting_observations.length === 0 && <li className="text-xs text-ocean-400">None</li>}
            </ul>
          </div>
        </div>

        {c.evidence_reasons.length > 0 && (
          <div className="mt-5 border-t border-ocean-100 pt-4">
            <div className="mb-2 text-xs font-semibold text-ocean-500">Why this signal</div>
            <ul className="space-y-1.5">
              {c.evidence_reasons.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-ocean-700">
                  <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-aqua-400" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {/* BASELINE */}
      <section className="card p-5 sm:p-6">
        <SectionHeading icon="Gauge" title="Baseline" />
        {c.baseline.available ? (
          <div>
            <p className="text-sm leading-relaxed text-ocean-700">
              Based on {c.baseline.historical_observation_count} historical observation(s) at this location: typical
              turbidity <span className="font-medium text-ocean-900">{c.baseline.turbidity_baseline ?? "n/a"}</span>,
              typical algae <span className="font-medium text-ocean-900">{c.baseline.algae_baseline ?? "n/a"}</span>.
            </p>
            <div className="mt-3">
              {c.baseline.deviates ? (
                <span className="inline-flex items-center gap-1.5 rounded-pill bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800 ring-1 ring-inset ring-amber-200">
                  <Icon.Warning className="h-3.5 w-3.5" /> Deviates from baseline
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 rounded-pill bg-moss-50 px-3 py-1 text-xs font-medium text-moss-700 ring-1 ring-inset ring-moss-200">
                  <Icon.Check className="h-3.5 w-3.5" /> Consistent with baseline
                </span>
              )}
            </div>
          </div>
        ) : (
          <p className="text-sm text-ocean-400">No baseline available yet for this location.</p>
        )}
      </section>

      {/* TIMELINE */}
      <section className="card p-5 sm:p-6">
        <SectionHeading icon="Clock" title="Evidence timeline" />
        <EvidenceTimeline c={c} />
      </section>

      {/* VERIFICATION */}
      <section className="card border-2 border-ocean-100 p-5 sm:p-6">
        <SectionHeading icon="Shield" title="Human verification" />
        <p className="mb-3 text-xs text-ocean-400">
          Verification is a separate, human step — it is never inferred from AI confidence.
        </p>
        {c.verification_status === "UNVERIFIED" && (
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <button
              onClick={() => handleVerify("VERIFIED")}
              disabled={verifying !== null}
              className="btn-primary bg-moss-600 hover:bg-moss-700 active:bg-moss-800"
            >
              <Icon.Check className="h-4 w-4" />
              {verifying === "VERIFIED" ? "Verifying…" : "Verify"}
            </button>
            <button
              onClick={() => handleVerify("REJECTED")}
              disabled={verifying !== null}
              className="btn-secondary border-rose-200 text-rose-700 hover:bg-rose-50"
            >
              <Icon.X className="h-4 w-4" />
              {verifying === "REJECTED" ? "Rejecting…" : "Reject"}
            </button>
          </div>
        )}
        {verifyError && (
          <p className="mb-3 flex items-center gap-1.5 text-sm text-rose-600">
            <Icon.Warning className="h-4 w-4 flex-shrink-0" />
            {verifyError}
          </p>
        )}
        <VerificationHistoryList c={c} />
      </section>

      {/* FHIR */}
      <section className="card p-5 sm:p-6">
        <SectionHeading icon="FileCheck" title="FHIR representation" />
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-ocean-50 px-4 py-3">
          <div>
            <div className="text-sm font-medium text-ocean-800">FHIR Observation</div>
            <div className="text-xs text-ocean-400">Structured interoperability resource for this case.</div>
          </div>
          <button onClick={toggleFhir} className="btn-secondary text-xs">
            {fhirLoading ? "Loading…" : fhir ? "Hide" : "View"} structured resource
          </button>
        </div>
        {fhir && (
          <pre className="mt-3 max-h-72 overflow-auto rounded-lg border border-ocean-100 bg-ocean-900 p-3 text-[11px] leading-relaxed text-aqua-200">
{JSON.stringify(fhir, null, 2)}
          </pre>
        )}
      </section>
    </main>
  );
}
