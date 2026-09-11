import { CaseDetail } from "@/lib/api";
import Badge from "@/components/ui/Badge";
import { Icon } from "@/components/ui/Icon";

export default function EvidenceTimeline({ c }: { c: CaseDetail }) {
  const steps: { icon: keyof typeof Icon; title: string; detail: string; time?: string; done: boolean }[] = [
    {
      icon: "Image",
      title: "Citizen report submitted",
      detail: c.description || "No description provided.",
      time: c.created_at,
      done: true,
    },
    {
      icon: "Gauge",
      title: "AI observation",
      detail: c.observation
        ? `Turbidity: ${c.observation.turbidity_indicator ?? "?"} · Algae: ${c.observation.algae_indicator ?? "?"} · Waste visible: ${String(c.observation.visible_waste)}`
        : "Not yet analyzed.",
      done: !!c.observation,
    },
    {
      icon: "Layers",
      title: "Related observations",
      detail: `${c.supporting_observations.length} supporting, ${c.conflicting_observations.length} conflicting nearby report(s).`,
      done: true,
    },
    {
      icon: "Layers",
      title: "Evidence fusion",
      detail: c.evidence_reasons.join("; ") || "No specific reasons recorded.",
      done: true,
    },
    {
      icon: "Gauge",
      title: "Confidence scored",
      detail: `${c.confidence_level} (${c.confidence_score.toFixed(3)})`,
      done: true,
    },
    {
      icon: "Shield",
      title: "Human verification",
      detail:
        c.verification_history.length > 0
          ? `${c.verification_status.replace(/_/g, " ").toLowerCase()} by ${c.verification_history[c.verification_history.length - 1].verifier_reference}`
          : "Not yet reviewed by a human.",
      time: c.verification_history[c.verification_history.length - 1]?.created_at,
      done: c.verification_status !== "UNVERIFIED",
    },
  ];

  return (
    <ol className="relative space-y-6 border-l-2 border-ocean-100 pl-6">
      {steps.map((s, i) => {
        const StepIcon = Icon[s.icon];
        return (
          <li key={i} className="relative">
            <span
              className={`absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full ring-4 ring-white ${
                s.done ? "bg-ocean-800 text-white" : "bg-slate-200 text-slate-400"
              }`}
            >
              <StepIcon className="h-3 w-3" />
            </span>
            <div className="text-sm font-semibold text-ocean-900">{s.title}</div>
            <div className="mt-0.5 text-sm text-ocean-600">{s.detail}</div>
            {s.time && <div className="mt-0.5 text-xs text-ocean-400">{new Date(s.time).toLocaleString()}</div>}
          </li>
        );
      })}
    </ol>
  );
}

export function VerificationHistoryList({ c }: { c: CaseDetail }) {
  if (c.verification_history.length === 0) {
    return (
      <p className="rounded-lg bg-ocean-50 px-4 py-3 text-sm text-ocean-500">
        No verification actions recorded yet.
      </p>
    );
  }
  return (
    <ul className="space-y-2">
      {c.verification_history.map((e) => (
        <li key={e.id} className="rounded-lg border border-ocean-100 bg-white p-3 text-sm">
          <div className="flex items-center gap-2">
            <Badge value={e.previous_status} />
            <Icon.ArrowRight className="h-3.5 w-3.5 text-ocean-300" />
            <Badge value={e.new_status} />
          </div>
          <div className="mt-1.5 text-xs text-ocean-400">
            by {e.verifier_reference} on {new Date(e.created_at).toLocaleString()}
          </div>
          {e.note && <div className="mt-1.5 text-xs italic text-ocean-600">&ldquo;{e.note}&rdquo;</div>}
        </li>
      ))}
    </ul>
  );
}
