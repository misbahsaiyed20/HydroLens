"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ExploreObservation, getExploreObservation, getImageUrl } from "@/lib/api";
import Badge from "@/components/ui/Badge";
import RemoteImage from "@/components/ui/RemoteImage";
import { LoadingState, ErrorState } from "@/components/ui/States";
import { Icon } from "@/components/ui/Icon";

function pretty(value: string | null | undefined) {
  if (!value || value === "none") return "Not detected";
  return value.replace(/_/g, " ");
}

export default function ExploreObservationDetailPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<ExploreObservation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.id) return;
    getExploreObservation(params.id).then(setItem).catch((e) => setError(e.message));
  }, [params.id]);

  if (error) return <main className="mx-auto max-w-4xl px-4 py-10 sm:px-6"><ErrorState message={error} /></main>;
  if (!item) return <main className="mx-auto max-w-4xl px-4 py-10 sm:px-6"><LoadingState label="Loading observation…" rows={3} /></main>;

  return (
    <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <Link href="/explore" className="inline-flex items-center gap-1.5 text-sm font-medium text-ocean-500 hover:text-ocean-700"><Icon.ArrowRight className="h-3.5 w-3.5 rotate-180" /> Back to Explore</Link>

      <div className="mt-5 grid gap-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-start">
        <div className="overflow-hidden rounded-[24px] border border-ocean-200 bg-ocean-900 shadow-card">
          <RemoteImage src={getImageUrl(item.image_path)} alt="Community water observation" className="aspect-[4/3] w-full object-cover" loading="eager" />
        </div>

        <div className="space-y-5">
          <div>
            <span className="section-title">Community observation</span>
            <h1 className="mt-2 text-2xl font-semibold text-ocean-900">{item.stream_name || "Local water observation"}</h1>
            <p className="mt-1 text-xs text-ocean-400">Observed {new Date(item.submitted_at).toLocaleString()}</p>
            <div className="mt-4"><Badge value={item.verification_status} size="md" /></div>
          </div>

          <section className="card p-5">
            <div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-ocean-50 text-ocean-500"><Icon.Gauge className="h-4 w-4" /></span><h2 className="text-sm font-semibold text-ocean-900">What HydroLens detected</h2></div>
            <p className="mt-4 text-sm leading-relaxed text-ocean-700">{item.condition_summary}</p>

            <div className="mt-4 grid grid-cols-2 gap-3">
              {[
                ["Turbidity", pretty(item.turbidity_indicator)],
                ["Algae", pretty(item.algae_indicator)],
                ["Visible waste", item.visible_waste ? "Detected" : "Not detected"],
                ["Color anomaly", pretty(item.color_anomaly)],
                ["Image quality", pretty(item.image_quality)],
                ["Review", item.verification_status.replace(/_/g, " ")],
              ].map(([label, value]) => <div key={label} className="rounded-xl bg-ocean-50 p-3"><div className="text-[10px] font-medium uppercase tracking-wider text-ocean-400">{label}</div><div className="mt-1 text-sm font-semibold capitalize text-ocean-900">{value}</div></div>)}
            </div>
          </section>

          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-relaxed text-amber-900">HydroLens reports visible image-based indicators only. This is not a laboratory water-quality measurement.</div>
        </div>
      </div>
    </main>
  );
}
