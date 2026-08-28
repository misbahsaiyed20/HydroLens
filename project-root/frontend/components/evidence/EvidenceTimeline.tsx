import { CaseDetail } from "@/lib/api";
import Badge from "@/components/ui/Badge";

export default function EvidenceTimeline({ c }: { c: CaseDetail }) {
  const steps: { title: string; detail: string; time?: string }[] = [
    { title: "Citizen report submitted", detail: c.description || "No description provided.", time: c.created_at },
    {
      title: "AI observation",
      detail: c.observation
        ? `turbidity=${c.observation.turbidity_indicator ?? "?"}, algae=${c.observation.algae_indicator ?? "?"}, waste=${String(c.observation.visible_waste)}`
        : "Not yet analyzed.",
    },
    {
      title: "Related observations",
      detail: `${c.supporting_observations.length} supporting, ${c.conflicting_observations.length} conflicting nearby report(s).`,
    },
    { title: "Evidence fusion", detail: c.evidence_reasons.join("; ") || "No specific reasons recorded." },
    { title: "Confidence", detail: `${c.confidence_level} (${c.confidence_score.toFixed(3)})` },
    {
      title: "Human verification",
      detail:
        c.verification_history.length > 0
          ? `${c.verification_status} by ${c.verification_history[c.verification_history.length - 1].verifier_reference}`
          : "Not yet reviewed by a human.",
      time: c.verification_history[c.verification_history.length - 1]?.created_at,
    },
  ];

  return (
    <ol className="space-y-4 border-l border-slate-200 pl-4">
      {steps.map((s, i) => (
        <li key={i} className="relative">
          <span className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-slate-400" />
          <div className="text-sm font-medium">{s.title}</div>
          <div className="text-sm text-slate-600">{s.detail}</div>
          {s.time && <div className="text-xs text-slate-400">{new Date(s.time).toLocaleString()}</div>}
        </li>
      ))}
    </ol>
  );
}

export function VerificationHistoryList({ c }: { c: CaseDetail }) {
  if (c.verification_history.length === 0) {
    return <p className="text-sm text-slate-500">No verification actions recorded yet.</p>;
  }
  return (
    <ul className="space-y-2">
      {c.verification_history.map((e) => (
        <li key={e.id} className="rounded border border-slate-200 p-2 text-sm">
          <div className="flex items-center gap-2">
            <Badge value={e.previous_status} />
            <span>→</span>
            <Badge value={e.new_status} />
          </div>
          <div className="mt-1 text-xs text-slate-500">
            by {e.verifier_reference} on {new Date(e.created_at).toLocaleString()}
          </div>
          {e.note && <div className="mt-1 text-xs text-slate-600">"{e.note}"</div>}
        </li>
      ))}
    </ul>
  );
}
