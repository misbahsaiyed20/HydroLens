"use client";

import { useMemo, useState } from "react";
import { CaseSummary } from "@/lib/api";

const COLOR_BY_ACTION: Record<string, string> = {
  CONTINUE_MONITORING: "#94a3b8",
  REVIEW_RECOMMENDED: "#f59e0b",
  PRIORITY_REVIEW: "#e11d48",
};

const LABEL_BY_ACTION: Record<string, string> = {
  CONTINUE_MONITORING: "Continue monitoring",
  REVIEW_RECOMMENDED: "Review recommended",
  PRIORITY_REVIEW: "Priority review",
};

/**
 * Simple normalized lat/lon scatter plot rendered as SVG. This is
 * deliberately NOT a real tile-based map (Leaflet/Mapbox) — for this
 * project's current scale, a lightweight dependency-free scatter communicates
 * "many observations -> spatial cluster -> one signal" without adding a
 * new npm package or external tile requests. A real interactive map
 * (Leaflet + OpenStreetMap, free) is the natural upgrade path later.
 */
export default function CaseMap({ cases, onSelect }: { cases: CaseSummary[]; onSelect?: (id: string) => void }) {
  const [hovered, setHovered] = useState<string | null>(null);

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
      x: 30 + ((c.location.longitude - minLon) / lonSpan) * 340,
      y: 24 + (1 - (c.location.latitude - minLat) / latSpan) * 250,
    }));
  }, [cases]);

  if (points.length === 0) {
    return (
      <div className="rounded-card border border-dashed border-ocean-200 bg-ocean-50/50 py-12 text-center text-sm text-ocean-400">
        No located cases to show.
      </div>
    );
  }

  const active = points.find((p) => p.case.report_id === hovered)?.case;

  return (
    <div className="card overflow-hidden">
      <svg
        viewBox="0 0 400 300"
        className="w-full bg-gradient-to-b from-ocean-50 to-aqua-50/40"
        role="img"
        aria-label="Case location map"
      >
        <defs>
          <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#d7e9ea" strokeWidth="0.75" />
          </pattern>
        </defs>
        <rect width="400" height="300" fill="url(#grid)" />
        {points.map(({ case: c, x, y }) => (
          <g
            key={c.report_id}
            className="cursor-pointer"
            onClick={() => onSelect?.(c.report_id)}
            onMouseEnter={() => setHovered(c.report_id)}
            onMouseLeave={() => setHovered(null)}
          >
            {c.action_level === "PRIORITY_REVIEW" && (
              <circle cx={x} cy={y} r={11} fill={COLOR_BY_ACTION[c.action_level]} opacity={0.18} />
            )}
            <circle
              cx={x}
              cy={y}
              r={hovered === c.report_id ? 8.5 : 7}
              fill={COLOR_BY_ACTION[c.action_level] || "#94a3b8"}
              className="transition-all"
            />
            <circle cx={x} cy={y} r={hovered === c.report_id ? 8.5 : 7} fill="none" stroke="white" strokeWidth={1.5} />
            <title>
              {(c.location.stream_name || "Unnamed location")} — {LABEL_BY_ACTION[c.action_level]} — {c.confidence_level} confidence
            </title>
          </g>
        ))}
      </svg>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-ocean-100 px-4 py-3">
        <div className="flex flex-wrap items-center gap-4 text-xs text-ocean-600">
          {Object.entries(LABEL_BY_ACTION).map(([key, label]) => (
            <span key={key} className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: COLOR_BY_ACTION[key] }} />
              {label}
            </span>
          ))}
        </div>
        <div className="min-h-[16px] text-xs font-medium text-ocean-700">
          {active ? (active.location.stream_name || "Unnamed location") : ""}
        </div>
      </div>
    </div>
  );
}
