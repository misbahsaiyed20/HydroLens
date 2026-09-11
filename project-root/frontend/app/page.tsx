import Link from "next/link";
import ReportForm from "@/components/ReportForm";
import { Icon } from "@/components/ui/Icon";

const STEPS = [
  { icon: "Image" as const, title: "You observe", detail: "Snap a photo of a stream and share its location." },
  { icon: "Layers" as const, title: "Evidence fuses", detail: "Nearby reports and history combine into one signal." },
  { icon: "Gauge" as const, title: "Signal is scored", detail: "Confidence, exposure risk and severity are calculated." },
  { icon: "Shield" as const, title: "A human decides", detail: "Reviewers verify before any action is taken." },
];

export default function HomePage() {
  return (
    <main>
      <section className="bg-hero-wash border-b border-ocean-100">
        <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6 sm:py-20">
          <div className="grid gap-12 lg:grid-cols-[1.05fr_1fr] lg:items-start">
            <div className="max-w-xl">
              <span className="inline-flex items-center gap-1.5 rounded-pill bg-white px-3 py-1 text-xs font-medium text-ocean-600 shadow-card ring-1 ring-ocean-100">
                <Icon.Droplet className="h-3.5 w-3.5" />
                Community stream observations
              </span>
              <h1 className="mt-4 text-3xl font-semibold text-ocean-900 sm:text-4xl">
                Report what you see in your stream.
              </h1>
              <p className="mt-3 text-[15px] leading-relaxed text-ocean-700">
                Aqua Sentinel turns many small observations into evidence‑backed environmental
                signal. Your report doesn&apos;t diagnose water quality on its own — it becomes one
                more piece of trustworthy evidence for a human reviewer.
              </p>

              <dl className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
                {STEPS.map((s, i) => {
                  const StepIcon = Icon[s.icon];
                  return (
                    <div key={s.title} className="relative">
                      <dt className="mb-2 flex h-9 w-9 items-center justify-center rounded-lg bg-white text-ocean-600 shadow-card ring-1 ring-ocean-100">
                        <StepIcon className="h-4 w-4" />
                      </dt>
                      <dd>
                        <div className="text-xs font-semibold text-ocean-800">{s.title}</div>
                        <div className="mt-0.5 text-[11px] leading-snug text-ocean-500">{s.detail}</div>
                      </dd>
                      {i < STEPS.length - 1 && (
                        <Icon.ArrowRight className="absolute -right-3 top-2 hidden h-3.5 w-3.5 text-ocean-200 sm:block" />
                      )}
                    </div>
                  );
                })}
              </dl>

              <div className="mt-8 hidden lg:block">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-ocean-600 hover:text-ocean-800"
                >
                  See the reviewer dashboard <Icon.ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>

            <div className="card p-5 sm:p-7">
              <h2 className="mb-1 text-lg font-semibold text-ocean-900">Submit an observation</h2>
              <p className="mb-5 text-sm text-ocean-500">Takes about a minute. A photo and location are required.</p>
              <ReportForm />
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <Link
          href="/dashboard"
          className="flex items-center justify-between rounded-card border border-ocean-100 bg-white px-5 py-4 text-sm font-medium text-ocean-700 shadow-card hover:border-aqua-200 lg:hidden"
        >
          See the reviewer dashboard
          <Icon.ArrowRight className="h-4 w-4" />
        </Link>
      </section>
    </main>
  );
}
