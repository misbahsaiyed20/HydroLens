"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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
  const router = useRouter();
  const [filters, setFilters] = useState<CaseFilters>({});
  const [search, setSearch] = useState("");
  const [result, setResult] = useState<CaseListResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"list" | "map">("list");

  function load() {
    if (!token) return;
    setError(null);
    setResult(null);
    getCases(token, filters as Record<string, string>)
      .then(setResult)
      .catch((e) => setError(e.message));
  }

  useEffect(load, [filters, token]);

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = search.trim();
    if (/^[0-9a-fA-F-]{8,}$/.test(trimmed)) {
      router.push(`/cases/${trimmed}`);
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-ocean-900">Cases</h1>
        <p className="mt-1 text-sm text-ocean-500">Analyzed reports, fused into evidence-backed cases.</p>
      </div>

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <form onSubmit={handleSearchSubmit} className="relative max-w-sm flex-1">
          <Icon.Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ocean-300" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by case or report ID…"
            aria-label="Search by case or report ID"
            className="input-field pl-9"
          />
        </form>

        <div className="flex gap-1 rounded-lg bg-ocean-50 p-1 text-sm">
          <button
            onClick={() => setView("list")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-medium transition-colors ${
              view === "list" ? "bg-white text-ocean-800 shadow-card" : "text-ocean-500"
            }`}
          >
            <Icon.List className="h-3.5 w-3.5" /> List
          </button>
          <button
            onClick={() => setView("map")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-medium transition-colors ${
              view === "map" ? "bg-white text-ocean-800 shadow-card" : "text-ocean-500"
            }`}
          >
            <Icon.Map className="h-3.5 w-3.5" /> Map
          </button>
        </div>
      </div>

      <CaseFiltersBar filters={filters} onChange={setFilters} />

      {error && <ErrorState message={error} onRetry={load} />}
      {!error && !result && <LoadingState label="Loading cases…" />}
      {result && result.items.length === 0 && (
        <EmptyState message="No environmental signals to review yet." hint="Cases appear here once reports are analyzed and fused into evidence." />
      )}

      {result && result.items.length > 0 && view === "list" && (
        <div className="space-y-3">
          {result.items.map((c) => (
            <CaseCard key={c.report_id} c={c} />
          ))}
        </div>
      )}

      {result && result.items.length > 0 && view === "map" && (
        <CaseMap cases={result.items} onSelect={(id) => router.push(`/cases/${id}`)} />
      )}
    </main>
  );
}

export default function CasesPage() {
  return (
    <RequireRole role="REVIEWER">
      <CasesContent />
    </RequireRole>
  );
}
