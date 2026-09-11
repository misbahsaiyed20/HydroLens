"use client";

import { Icon } from "@/components/ui/Icon";

export type CaseFilters = {
  confidence_level?: string;
  exposure_risk_level?: string;
  action_level?: string;
  verification_status?: string;
};

const OPTIONS: Record<keyof CaseFilters, { label: string; options: string[] }> = {
  confidence_level: { label: "Confidence", options: ["LOW", "MODERATE", "HIGH"] },
  exposure_risk_level: { label: "Exposure risk", options: ["LOW", "MODERATE", "ELEVATED"] },
  action_level: { label: "Action", options: ["CONTINUE_MONITORING", "REVIEW_RECOMMENDED", "PRIORITY_REVIEW"] },
  verification_status: { label: "Verification", options: ["UNVERIFIED", "VERIFIED", "REJECTED"] },
};

export default function CaseFiltersBar({
  filters,
  onChange,
}: {
  filters: CaseFilters;
  onChange: (f: CaseFilters) => void;
}) {
  const activeCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      {(Object.keys(OPTIONS) as (keyof CaseFilters)[]).map((key) => (
        <div key={key} className="relative">
          <select
            value={filters[key] || ""}
            onChange={(e) => onChange({ ...filters, [key]: e.target.value || undefined })}
            className="input-field appearance-none py-1.5 pr-8 text-xs font-medium text-ocean-700"
          >
            <option value="">{OPTIONS[key].label}: any</option>
            {OPTIONS[key].options.map((opt) => (
              <option key={opt} value={opt}>
                {opt.replace(/_/g, " ")}
              </option>
            ))}
          </select>
          <Icon.ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ocean-400" />
        </div>
      ))}
      {activeCount > 0 && (
        <button
          onClick={() => onChange({})}
          className="text-xs font-medium text-ocean-400 hover:text-rose-600"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
