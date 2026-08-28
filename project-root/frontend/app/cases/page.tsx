"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CaseListResult, getCases } from "@/lib/api";
import CaseCard from "@/components/cases/CaseCard";
import CaseFiltersBar, { CaseFilters } from "@/components/cases/CaseFilters";
import CaseMap from "@/components/map/CaseMap";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/States";

export default function CasesPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<CaseFilters>({});
  const [search, setSearch] = useState("");
  const [result, setResult] = useState<CaseListResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"list" | "map">("list");

  function load() {
    setError(null);
    setResult(null);
    getCases(filters as Record<string, string>)
      .then(setResult)
      .catch((e) => setError(e.message));
  }

  useEffect(load, [filters]);

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = search.trim();
    if (/^[0-9a-fA-F-]{8,}$/.test(trimmed)) {
      router.push(`/cases/${trimmed}`);
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="mb-1 text-2xl font-semibold">Cases</h1>
      <p className="mb-6 text-sm text-slate-600">Analyzed reports, fused into evidence-backed cases.</p>

      <form onSubmit={handleSearchSubmit} className="mb-4 flex gap-2">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by case/report ID…"
          className="flex-1 rounded border border-slate-300 px-3 py-1.5 text-sm"
        />
        <button type="submit" className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white">
          Open
        </button>
      </form>

      <CaseFiltersBar filters={filters} onChange={setFilters} />

      <div className="mb-4 flex gap-2 text-sm">
        <button
          onClick={() => setView("list")}
          className={`rounded px-3 py-1 ${view === "list" ? "bg-slate-900 text-white" : "bg-slate-100"}`}
        >
          List
        </button>
        <button
          onClick={() => setView("map")}
          className={`rounded px-3 py-1 ${view === "map" ? "bg-slate-900 text-white" : "bg-slate-100"}`}
        >
          Map
        </button>
      </div>

      {error && <ErrorState message={error} onRetry={load} />}
      {!error && !result && <LoadingState label="Loading cases…" />}
      {result && result.items.length === 0 && <EmptyState message="No cases match these filters." />}

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
