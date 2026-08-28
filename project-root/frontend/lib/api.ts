const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

export type DashboardSummary = {
  total_reports: number;
  pending_review: number;
  analyzed_reports: number;
  high_confidence_cases: number;
  verified_cases: number;
  rejected_cases: number;
  cases_requiring_review: number;
};

export type Location = {
  id: string;
  latitude: number;
  longitude: number;
  stream_name: string | null;
  stream_segment: string | null;
};

export type CaseSummary = {
  report_id: string;
  location: Location;
  condition_summary: string;
  confidence_score: number;
  confidence_level: "LOW" | "MODERATE" | "HIGH";
  exposure_risk_level: "LOW" | "MODERATE" | "ELEVATED";
  action_level: "CONTINUE_MONITORING" | "REVIEW_RECOMMENDED" | "PRIORITY_REVIEW";
  verification_status: "UNVERIFIED" | "VERIFIED" | "REJECTED";
  supporting_count: number;
  conflicting_count: number;
  created_at: string;
  updated_at: string;
};

export type CaseListResult = { total: number; items: CaseSummary[] };

export type RelatedObservation = {
  report_id: string;
  distance_meters: number;
  minutes_apart: number;
  algae_indicator: string | null;
  color_anomaly: string | null;
  turbidity_indicator: string | null;
  visible_waste: boolean | null;
  image_quality: string | null;
  verification_status: string;
};

export type BaselineSummary = {
  available: boolean;
  historical_observation_count: number;
  turbidity_baseline: string | null;
  algae_baseline: string | null;
  waste_rate: number | null;
  deviates: boolean | null;
};

export type VerificationEvent = {
  id: string;
  report_id: string;
  event_type: string;
  previous_status: string;
  new_status: string;
  verifier_reference: string;
  note: string | null;
  created_at: string;
};

export type Observation = {
  id: string;
  algae_indicator: string | null;
  color_anomaly: string | null;
  visible_waste: boolean | null;
  turbidity_indicator: string | null;
  image_quality: string | null;
  model_confidence: number | null;
};

export type CaseDetail = {
  report_id: string;
  status: string;
  verification_status: string;
  location: Location;
  observation: Observation | null;
  description: string | null;
  created_at: string;
  updated_at: string;
  condition_summary: string;
  confidence_score: number;
  confidence_level: "LOW" | "MODERATE" | "HIGH";
  indicator_severity: "NONE" | "LOW" | "MODERATE" | "HIGH";
  exposure_risk_level: "LOW" | "MODERATE" | "ELEVATED";
  action_level: "CONTINUE_MONITORING" | "REVIEW_RECOMMENDED" | "PRIORITY_REVIEW";
  recommended_action: string;
  supporting_observations: RelatedObservation[];
  conflicting_observations: RelatedObservation[];
  evidence_reasons: string[];
  baseline: BaselineSummary;
  verification_history: VerificationEvent[];
  fhir_url: string;
};

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Request failed (${res.status}): ${path}`);
  }
  return res.json();
}

export function getDashboardSummary() {
  return apiFetch<DashboardSummary>("/dashboard/summary");
}

export function getCases(params: Record<string, string | number | undefined> = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "") query.set(k, String(v));
  });
  const qs = query.toString();
  return apiFetch<CaseListResult>(`/cases${qs ? `?${qs}` : ""}`);
}

export function getCaseDetail(reportId: string) {
  return apiFetch<CaseDetail>(`/cases/${reportId}`);
}

export function getFhirUrl(reportId: string) {
  return `${API_BASE_URL}/reports/${reportId}/fhir`;
}
