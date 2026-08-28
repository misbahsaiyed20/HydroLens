"use client";

import { useMemo } from "react";
import { CaseSummary } from "@/lib/api";

const COLOR_BY_ACTION: Record<string, string> = {
  CONTINUE_MONITORING: "#94a3b8",
  REVIEW_RECOMMENDED: "#f59e0b",
  PRIORITY_REVIEW: "#dc2626",
};

/**
 * Simple normalized lat/lon scatter plot rendered as SVG. This is
 * deliberately NOT a real tile-based map (Leaflet/Mapbox) — for this
 * sprint's scale, a lightweight dependency-free scatter communicates
 * "many observations -> spatial cluster -> one signal" without adding a
 * new npm package or external tile requests. A real interactive map
 * (Leaflet + OpenStreetMap, free) is the natural upgrade path if the
 * project needs real basemap context later.
 */
export default function CaseMap({ cases, onSelect }: { cases: CaseSummary[]; onSelect?: (id: string) => void }) {
  const points = useMemo(() => {
    const withLoc = cases.filter((c) => c.location);
    if (withLoc.length === 0) return [];

    const lats = withLoc.map((c) => c.location.latitude);
    const lons = withLoc.map((c) => c.location.longitude);
    const minLat = Math.min(...lats), maxLat = Math.max(...lats);
    const minLon = Math.min(...lons), maxLon = Math.max(...lons);
    const latSpan = maxLat - minLat || 0.001;
    const lonSpan = maxLon - minLon || 0.001;

    return withLoc.map((c) => ({
      case: c,
      x: 20 + ((c.location.longitude - minLon) / lonSpan) * 360,
      y: 20 + (1 - (c.location.latitude - minLat) / latSpan) * 260,
    }));
  }, [cases]);

  if (points.length === 0) {
    return <div className="rounded border border-dashed border-slate-300 py-12 text-center text-sm text-slate-500">No located cases to show.</div>;
  }

  return (
    <svg viewBox="0 0 400 300" className="w-full rounded border border-slate-200 bg-slate-50" role="img" aria-label="Case location map">
      {points.map(({ case: c, x, y }) => (
        <g key={c.report_id} className="cursor-pointer" onClick={() => onSelect?.(c.report_id)}>
          <circle cx={x} cy={y} r={7} fill={COLOR_BY_ACTION[c.action_level] || "#94a3b8"} opacity={0.85} />
          <circle cx={x} cy={y} r={7} fill="none" stroke="white" strokeWidth={1.5} />
          <title>
            {(c.location.stream_name || "Unnamed location")} — {c.action_level.replace(/_/g, " ")} — {c.confidence_level} confidence
          </title>
        </g>
      ))}
    </svg>
  );
}
