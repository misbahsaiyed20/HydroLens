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

export type ReportOut = {
  id: string;
  user_id: string | null;
  image_path: string;
  description: string | null;
  status: string;
  verification_status: string;
  submitted_at: string;
  updated_at: string;
  location: Location;
  observation: Observation | null;
};

export type ReportListResult = { total: number; items: ReportOut[] };

async function apiFetch<T>(path: string, token?: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
  } catch {
    throw new Error("Unable to connect to Aqua Sentinel. Please make sure the server is running.");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ? String(body.detail) : `Request failed (${res.status}): ${path}`);
  }
  return res.json();
}

export function getDashboardSummary(token: string) {
  return apiFetch<DashboardSummary>("/dashboard/summary", token);
}

export function getCases(token: string, params: Record<string, string | number | undefined> = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "") query.set(k, String(v));
  });
  const qs = query.toString();
  return apiFetch<CaseListResult>(`/cases${qs ? `?${qs}` : ""}`, token);
}

export function getCaseDetail(token: string, reportId: string) {
  return apiFetch<CaseDetail>(`/cases/${reportId}`, token);
}

export function getMyReports(token: string) {
  return apiFetch<ReportListResult>("/reports/me", token);
}

export function submitVerification(token: string, reportId: string, status: "VERIFIED" | "REJECTED", note?: string) {
  return apiFetch2<CaseDetail["verification_history"][number]>(`/reports/${reportId}/verify`, token, {
    method: "POST",
    body: JSON.stringify({ status, note: note || undefined }),
  });
}

async function apiFetch2<T>(path: string, token: string, options: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new Error("Unable to connect to Aqua Sentinel. Please make sure the server is running.");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ? String(body.detail) : `Request failed (${res.status}): ${path}`);
  }
  return res.json();
}

export function getFhirResource(token: string, reportId: string) {
  return apiFetch<Record<string, unknown>>(`/reports/${reportId}/fhir`, token);
}

export function getFhirUrl(reportId: string) {
  return `${API_BASE_URL}/reports/${reportId}/fhir`;
}
