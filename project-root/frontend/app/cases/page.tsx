"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CaseListResult, getCases } from "@/lib/api";
import CaseCard from "@/components/cases/CaseCard";
import CaseFiltersBar, { CaseFilters } from "@/components/cases/CaseFilters";
import CaseMap from "@/components/map/CaseMap";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/States";
import { Icon } from "@/components/ui/Icon";
import RequireRole from "@/components/RequireRole";
import { useAuth } from "@/contexts/AuthContext";

function CasesContent() {
  const { token } = useAuth();
  const searchParams = useSearchParams();
  const [filters, setFilters] = useState<CaseFilters>({});
  const [reviewNeeded, setReviewNeeded] = useState(false);
  const [search, setSearch] = useState("");
  const [result, setResult] = useState<CaseListResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"list" | "map">("list");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    setFilters({
      confidence_level: searchParams.get("confidence_level") || undefined,
      exposure_risk_level: searchParams.get("exposure_risk_level") || undefined,
      action_level: searchParams.get("action_level") || undefined,
      verification_status: searchParams.get("verification_status") || undefined,
    });
    setReviewNeeded(searchParams.get("review_needed") === "true");
    setSearch(searchParams.get("search") || "");
  }, [searchParams]);

  useEffect(() => {
    if (!token) return;
    const timer = window.setTimeout(() => {
      setError(null);
      setResult(null);
      getCases(token, { ...filters, review_needed: reviewNeeded || undefined, search: search.trim() || undefined, limit: 100 })
        .then(setResult)
        .catch((e) => setError(e.message));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [filters, reviewNeeded, search, token, reloadKey]);

  function clearAll() {
    setFilters({});
    setReviewNeeded(false);
    setSearch("");
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <span className="section-title">Reviewer workspace</span>
          <h1 className="mt-2 text-2xl font-semibold text-ocean-900">Cases</h1>
          <p className="mt-1 text-sm text-ocean-500">Search, filter, and open every analyzed signal with its evidence trail.</p>
        </div>
        {result && <div className="text-xs text-ocean-400">{result.total} matching case{result.total === 1 ? "" : "s"}</div>}
      </div>

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex max-w-xl flex-1 items-center gap-2">
          <div className="relative flex-1">
            <Icon.Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ocean-300" />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by report ID or stream name…" aria-label="Search cases by report ID or stream name" className="input-field pl-9" />
          </div>
          {(search || Object.values(filters).some(Boolean) || reviewNeeded) && <button type="button" onClick={clearAll} className="btn-secondary px-3 py-2 text-xs">Clear</button>}
        </div>

        <div className="flex gap-1 rounded-lg bg-ocean-50 p-1 text-sm">
          <button type="button" onClick={() => setView("list")} className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-medium transition-colors ${view === "list" ? "bg-white text-ocean-800 shadow-card" : "text-ocean-500"}`}><Icon.List className="h-3.5 w-3.5" /> List</button>
          <button type="button" onClick={() => setView("map")} className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-medium transition-colors ${view === "map" ? "bg-white text-ocean-800 shadow-card" : "text-ocean-500"}`}><Icon.Map className="h-3.5 w-3.5" /> Map</button>
        </div>
      </div>

      <CaseFiltersBar filters={filters} onChange={setFilters} />

      {reviewNeeded && <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800">Showing cases that require review.</div>}

      {error && <ErrorState message={error} onRetry={() => setReloadKey((value) => value + 1)} />}
      {!error && !result && <LoadingState label="Loading cases…" rows={4} />}
      {result && result.items.length === 0 && <EmptyState message="No cases match your search or filters." hint="Try clearing a filter or searching for another report ID or stream name." />}

      {result && result.items.length > 0 && view === "list" && <div className="space-y-4">{result.items.map((c) => <CaseCard key={c.report_id} c={c} />)}</div>}
      {result && result.items.length > 0 && view === "map" && <CaseMap cases={result.items} onSelect={(id) => { window.location.href = `/cases/${id}`; }} />}
    </main>
  );
}

export default function CasesPage() {
  return <RequireRole role="REVIEWER"><CasesContent /></RequireRole>;
}
