"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { getImageUrl, getReport, ReportOut } from "@/lib/api";
import Badge from "@/components/ui/Badge";
import RemoteImage from "@/components/ui/RemoteImage";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { Icon } from "@/components/ui/Icon";
import RequireRole from "@/components/RequireRole";
import { useAuth } from "@/contexts/AuthContext";

function pretty(value: string | null | undefined) {
  if (!value || value === "none") return "Not detected";
  return value.replace(/_/g, " ");
}

function ReviewerReportContent() {
  const { token } = useAuth();
  const params = useParams<{ id: string }>();
  const [report, setReport] = useState<ReportOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !params.id) return;
    getReport(token, params.id).then(setReport).catch((e) => setError(e.message));
  }, [token, params.id]);

  if (error) return <main className="mx-auto max-w-4xl px-4 py-10 sm:px-6"><ErrorState message={error} /></main>;
  if (!report) return <main className="mx-auto max-w-4xl px-4 py-10 sm:px-6"><LoadingState label="Loading report…" rows={3} /></main>;

  const analyzed = report.status === "ANALYZED";
  const o = report.observation;

  return (
    <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <Link href="/review-reports" className="inline-flex items-center gap-1.5 text-sm font-medium text-ocean-500 hover:text-ocean-700"><Icon.ArrowRight className="h-3.5 w-3.5 rotate-180" /> Back to review queue</Link>

      <div className="mt-5 grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="overflow-hidden rounded-[24px] border border-ocean-200 bg-ocean-900 shadow-card"><RemoteImage src={getImageUrl(report.image_path)} alt="Reported water observation" className="aspect-[4/3] w-full object-cover" loading="eager" /></div>
        <div className="space-y-5">
          <div><span className="section-title">Reviewer report</span><h1 className="mt-2 text-2xl font-semibold text-ocean-900">{report.location.stream_name || "Unnamed location"}</h1><p className="mt-1 text-xs text-ocean-400">{new Date(report.submitted_at).toLocaleString()}</p><div className="mt-4 flex flex-wrap gap-2"><Badge value={report.status} size="md" /><Badge value={report.verification_status} size="md" /></div></div>

          <section className="card p-5"><div className="text-sm font-semibold text-ocean-900">Observation</div>{analyzed && o ? <div className="mt-4 grid grid-cols-2 gap-3">{[["Turbidity", pretty(o.turbidity_indicator)],["Algae", pretty(o.algae_indicator)],["Visible waste", o.visible_waste ? "Detected" : "Not detected"],["Color anomaly", pretty(o.color_anomaly)],["Image quality", pretty(o.image_quality)],["Model confidence", o.model_confidence != null ? o.model_confidence.toFixed(2) : "—"]].map(([label,value])=><div key={label} className="rounded-xl bg-ocean-50 p-3"><div className="text-[10px] font-medium uppercase tracking-wider text-ocean-400">{label}</div><div className="mt-1 text-sm font-semibold capitalize text-ocean-900">{value}</div></div>)}</div> : <p className="mt-3 text-sm text-ocean-600">This report is still in the AI processing stage. There is no observation to review yet.</p>}</section>

          {report.description && <section className="card p-5"><div className="text-xs font-semibold uppercase tracking-wider text-ocean-400">Citizen description</div><p className="mt-2 text-sm leading-relaxed text-ocean-700">{report.description}</p></section>}

          {analyzed ? <Link href={`/cases/${report.id}`} className="btn-primary w-full">Open full case <Icon.ArrowRight className="h-4 w-4" /></Link> : <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-relaxed text-amber-900">Wait for AI analysis to complete. Once analyzed, this report becomes available as a case.</div>}
        </div>
      </div>
    </main>
  );
}

export default function ReviewerReportPage() {
  return <RequireRole role="REVIEWER"><ReviewerReportContent /></RequireRole>;
}
