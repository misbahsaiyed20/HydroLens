"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ExploreObservation, getExploreObservations, getImageUrl } from "@/lib/api";
import Badge from "@/components/ui/Badge";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/States";
import { Icon } from "@/components/ui/Icon";

type Filter = "ALL" | "VERIFIED" | "UNDER_REVIEW" | "ALGAE" | "TURBID" | "WASTE";

function matchesFilter(item: ExploreObservation, filter: Filter) {
  if (filter === "ALL") return true;
  if (filter === "VERIFIED") return item.verification_status === "VERIFIED";
  if (filter === "UNDER_REVIEW") return item.verification_status === "UNVERIFIED";
  if (filter === "ALGAE") return Boolean(item.algae_indicator && item.algae_indicator !== "none");
  if (filter === "TURBID") return Boolean(item.turbidity_indicator && !["clear", "none"].includes(item.turbidity_indicator));
  if (filter === "WASTE") return Boolean(item.visible_waste);
  return true;
}

export default function ExplorePage() {
  const [items, setItems] = useState<ExploreObservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("ALL");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const result = await getExploreObservations(24, 0);
      setItems(result.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load observations.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const visibleItems = items.filter((item) => matchesFilter(item, filter));

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-12">
      <div className="max-w-2xl">
        <span className="section-title">Community view</span>
        <h1 className="mt-2 text-3xl font-semibold text-ocean-900">Explore observations</h1>
        <p className="mt-2 text-sm leading-relaxed text-ocean-600">
          Browse recent, anonymized water observations shared through HydroLens. Public views show
          observable signals and review status, not private citizen details or reviewer-only evidence.
        </p>
      </div>

      <div className="mt-7 flex flex-wrap gap-2">
        {[
          ["ALL", "All"],
          ["VERIFIED", "Verified"],
          ["UNDER_REVIEW", "Under review"],
          ["ALGAE", "Algae"],
          ["TURBID", "Turbid"],
          ["WASTE", "Waste"],
        ].map(([value, label]) => (
          <button
            key={value}
            onClick={() => setFilter(value as Filter)}
            className={`rounded-pill px-3 py-1.5 text-xs font-medium ring-1 ring-inset transition ${
              filter === value ? "bg-ocean-800 text-white ring-ocean-800" : "bg-white text-ocean-600 ring-ocean-200 hover:bg-ocean-50"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mt-7">
        {error && <ErrorState message={error} onRetry={load} />}
        {loading && <LoadingState label="Loading community observations…" rows={4} />}
        {!loading && !error && visibleItems.length === 0 && (
          <EmptyState
            message="No observations match this filter."
            hint="Try another filter or check back after more reports are analyzed."
          />
        )}

        {!loading && !error && visibleItems.length > 0 && (
          <>
            <div className="mb-4 text-xs text-ocean-400">
              Showing {visibleItems.length} observation{visibleItems.length === 1 ? "" : "s"}.
            </div>
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {visibleItems.map((item) => (
                <article key={item.id} className="card overflow-hidden">
                  <div className="relative aspect-[4/3] bg-ocean-50">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={getImageUrl(item.image_path)}
                      alt="Community water observation"
                      className="h-full w-full object-cover"
                      loading="lazy"
                    />
                    <div className="absolute left-3 top-3">
                      <Badge value={item.verification_status} />
                    </div>
                  </div>

                  <div className="p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-ocean-900">
                          {item.stream_name || "Local water observation"}
                        </div>
                        <div className="mt-1 text-xs text-ocean-400">
                          {new Date(item.submitted_at).toLocaleString()}
                        </div>
                      </div>
                      <Icon.Droplet className="h-4 w-4 flex-shrink-0 text-aqua-500" />
                    </div>

                    <p className="mt-3 text-sm leading-relaxed text-ocean-700">{item.condition_summary}</p>

                    <div className="mt-4 flex flex-wrap gap-2 text-[11px]">
                      {item.turbidity_indicator && item.turbidity_indicator !== "none" && (
                        <span className="rounded-pill bg-ocean-50 px-2.5 py-1 text-ocean-700">
                          Turbidity: {item.turbidity_indicator}
                        </span>
                      )}
                      {item.algae_indicator && item.algae_indicator !== "none" && (
                        <span className="rounded-pill bg-aqua-50 px-2.5 py-1 text-aqua-700">
                          Algae: {item.algae_indicator}
                        </span>
                      )}
                      {item.visible_waste && (
                        <span className="rounded-pill bg-amber-50 px-2.5 py-1 text-amber-800">
                          Visible waste
                        </span>
                      )}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </>
        )}
      </div>

      <div className="mt-10 rounded-2xl border border-ocean-200 bg-ocean-900 p-6 text-white sm:p-7">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-aqua-200">Have an observation?</div>
            <h2 className="mt-1 text-xl font-semibold">Add your own photo to the evidence stream.</h2>
          </div>
          <Link href="/#report" className="btn-secondary w-fit border-white/15 bg-white text-ocean-900 hover:bg-ocean-50">
            Report an observation
            <Icon.ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </main>
  );
}
