"use client";

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
  return (
    <div className="mb-4 flex flex-wrap gap-3">
      {(Object.keys(OPTIONS) as (keyof CaseFilters)[]).map((key) => (
        <select
          key={key}
          value={filters[key] || ""}
          onChange={(e) => onChange({ ...filters, [key]: e.target.value || undefined })}
          className="rounded border border-slate-300 px-2 py-1 text-sm"
        >
          <option value="">{OPTIONS[key].label}: any</option>
          {OPTIONS[key].options.map((opt) => (
            <option key={opt} value={opt}>
              {opt.replace(/_/g, " ")}
            </option>
          ))}
        </select>
      ))}
    </div>
  );
}
