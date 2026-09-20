import Link from "next/link";
import ReportForm from "@/components/ReportForm";
import { Icon } from "@/components/ui/Icon";

const DETECTORS = [
  { icon: "Droplet" as const, title: "Turbidity", detail: "Clear, cloudy, or opaque-looking water." },
  { icon: "Layers" as const, title: "Algae", detail: "Visible green or algae-like appearance." },
  { icon: "Warning" as const, title: "Visible waste", detail: "Floating or clearly visible debris." },
  { icon: "Gauge" as const, title: "Image quality", detail: "Whether the photo provides usable visual evidence." },
];

const STEPS = [
  { icon: "Image" as const, number: "01", title: "Observe", detail: "Take a photo and share where you saw it." },
  { icon: "Gauge" as const, number: "02", title: "Analyze", detail: "AI identifies visible environmental indicators." },
  { icon: "Layers" as const, number: "03", title: "Build evidence", detail: "Nearby observations and history add context." },
  { icon: "Shield" as const, number: "04", title: "Review", detail: "A human reviewer makes the final call." },
];

export default function HomePage() {
  return (
    <main>
      <section className="overflow-hidden border-b border-ocean-100 bg-hero-wash">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 sm:px-6 sm:py-16 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:py-20">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-1.5 rounded-pill bg-white px-3 py-1 text-xs font-medium text-ocean-600 shadow-card ring-1 ring-ocean-100">
              <Icon.Droplet className="h-3.5 w-3.5" />
              Community water observations
            </span>

            <h1 className="mt-5 max-w-xl text-4xl font-semibold leading-tight tracking-tight text-ocean-950 sm:text-5xl">
              See something unusual in your water?
            </h1>

            <p className="mt-4 max-w-xl text-base leading-relaxed text-ocean-700 sm:text-[17px]">
              Snap a photo, share where you saw it, and let HydroLens turn the visible condition into a
              structured observation that can be checked with other evidence.
            </p>

            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="#report" className="btn-primary">
                <Icon.Upload className="h-4 w-4" />
                Report an observation
              </Link>
              <Link href="/explore" className="btn-secondary">
                Explore observations
                <Icon.ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="mt-7 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-ocean-500">
              <span className="inline-flex items-center gap-1.5">
                <Icon.Check className="h-3.5 w-3.5 text-moss-600" />
                AI-assisted observation
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Icon.Check className="h-3.5 w-3.5 text-moss-600" />
                Evidence-aware workflow
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Icon.Check className="h-3.5 w-3.5 text-moss-600" />
                Human verification
              </span>
            </div>
          </div>

          <div className="relative">
            <div className="relative overflow-hidden rounded-[28px] border border-ocean-200 bg-ocean-900 p-2 shadow-card-hover">
              <div className="relative min-h-[340px] overflow-hidden rounded-[22px] bg-gradient-to-b from-ocean-700 via-aqua-700 to-ocean-950">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_25%,rgba(255,255,255,0.22),transparent_28%),radial-gradient(circle_at_75%_70%,rgba(255,255,255,0.12),transparent_30%)]" />
                <div className="absolute -left-8 top-10 h-32 w-[125%] rotate-[-7deg] rounded-[50%] border border-white/15 bg-white/5" />
                <div className="absolute -left-10 top-28 h-28 w-[130%] rotate-[-7deg] rounded-[50%] border border-white/10 bg-white/5" />
                <div className="absolute inset-x-8 bottom-8 h-20 rounded-2xl border border-white/10 bg-black/10 backdrop-blur-sm" />

                <div className="absolute left-5 top-5 rounded-xl bg-white/95 px-3 py-2 shadow-card">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-ocean-400">Example</div>
                  <div className="mt-0.5 text-sm font-semibold text-ocean-900">Observation preview</div>
                </div>

                <div className="absolute bottom-5 right-5 w-[min(270px,calc(100%-40px))] rounded-2xl border border-white/50 bg-white/95 p-4 shadow-card-hover backdrop-blur">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-ocean-400">AI observation</span>
                    <span className="rounded-pill bg-aqua-50 px-2 py-1 text-[10px] font-medium text-aqua-700">Example</span>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <div className="rounded-lg bg-ocean-50 p-2.5">
                      <div className="text-ocean-400">Turbidity</div>
                      <div className="mt-0.5 font-semibold text-ocean-900">Clear</div>
                    </div>
                    <div className="rounded-lg bg-ocean-50 p-2.5">
                      <div className="text-ocean-400">Algae</div>
                      <div className="mt-0.5 font-semibold text-ocean-900">None</div>
                    </div>
                    <div className="rounded-lg bg-ocean-50 p-2.5">
                      <div className="text-ocean-400">Visible waste</div>
                      <div className="mt-0.5 font-semibold text-ocean-900">Not detected</div>
                    </div>
                    <div className="rounded-lg bg-ocean-50 p-2.5">
                      <div className="text-ocean-400">Image quality</div>
                      <div className="mt-0.5 font-semibold text-ocean-900">Good</div>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center gap-2 border-t border-ocean-100 pt-3 text-xs text-ocean-500">
                    <Icon.Shield className="h-3.5 w-3.5" />
                    Human review remains separate
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-b border-ocean-100 bg-white">
        <div className="mx-auto grid max-w-6xl gap-3 px-4 py-7 sm:grid-cols-2 sm:px-6 lg:grid-cols-4">
          {STEPS.map((step) => {
            const StepIcon = Icon[step.icon];
            return (
              <div key={step.number} className="rounded-2xl border border-ocean-100 bg-ocean-50/45 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-semibold tracking-[0.18em] text-ocean-300">{step.number}</span>
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-ocean-500 shadow-card">
                    <StepIcon className="h-4 w-4" />
                  </span>
                </div>
                <div className="mt-4 text-sm font-semibold text-ocean-900">{step.title}</div>
                <p className="mt-1 text-xs leading-relaxed text-ocean-500">{step.detail}</p>
              </div>
            );
          })}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
        <div className="max-w-2xl">
          <span className="section-title">What HydroLens looks for</span>
          <h2 className="mt-2 text-2xl font-semibold text-ocean-900 sm:text-3xl">Visible signals, explained simply.</h2>
          <p className="mt-2 text-sm leading-relaxed text-ocean-600">
            HydroLens focuses on what can actually be observed in a photograph.
          </p>
        </div>

        <div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {DETECTORS.map((detector) => {
            const DetectorIcon = Icon[detector.icon];
            return (
              <div key={detector.title} className="card-interactive p-5">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-ocean-50 text-ocean-600">
                  <DetectorIcon className="h-5 w-5" />
                </span>
                <h3 className="mt-4 text-sm font-semibold text-ocean-900">{detector.title}</h3>
                <p className="mt-1.5 text-xs leading-relaxed text-ocean-500">{detector.detail}</p>
              </div>
            );
          })}
        </div>

        <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-relaxed text-amber-900">
          Visual indicators are not laboratory water-quality measurements.
        </div>
      </section>

      <section id="report" className="border-y border-ocean-100 bg-ocean-50/40">
        <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 sm:px-6 sm:py-16 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div className="max-w-lg">
            <span className="section-title">Report an observation</span>
            <h2 className="mt-2 text-2xl font-semibold text-ocean-900 sm:text-3xl">Put a real observation into the evidence pipeline.</h2>
            <p className="mt-3 text-sm leading-relaxed text-ocean-600">
              A photo and location are enough to get started. HydroLens keeps the AI observation,
              supporting evidence, and human verification as separate stages.
            </p>

            <div className="mt-6 space-y-3">
              {[
                "Photo-based environmental observation",
                "Related reports and historical context",
                "Explainable confidence and review status",
              ].map((item) => (
                <div key={item} className="flex items-start gap-2.5 text-sm text-ocean-700">
                  <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-moss-100 text-moss-700">
                    <Icon.Check className="h-3 w-3" />
                  </span>
                  {item}
                </div>
              ))}
            </div>

            <Link href="/my-reports" className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-aqua-700 hover:text-aqua-800">
              View your reports <Icon.ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <div className="card p-5 sm:p-7">
            <h3 className="text-lg font-semibold text-ocean-900">Submit a photo</h3>
            <p className="mb-5 mt-1 text-sm text-ocean-500">Share what you saw. HydroLens handles the analysis workflow.</p>
            <ReportForm />
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
        <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <div className="card p-6 sm:p-8">
            <span className="section-title">Trust by design</span>
            <h2 className="mt-2 text-2xl font-semibold text-ocean-900">AI helps organize evidence. Humans make the final call.</h2>
            <p className="mt-3 max-w-xl text-sm leading-relaxed text-ocean-600">
              HydroLens separates AI analysis from human verification. A model can suggest what a
              photograph appears to show, while the broader evidence and review workflow decide how that
              observation should be treated.
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              <span className="rounded-pill bg-aqua-50 px-3 py-1.5 text-xs font-medium text-aqua-700">AI observation</span>
              <span className="rounded-pill bg-ocean-50 px-3 py-1.5 text-xs font-medium text-ocean-700">Evidence fusion</span>
              <span className="rounded-pill bg-moss-50 px-3 py-1.5 text-xs font-medium text-moss-700">Human verification</span>
            </div>
          </div>

          <div className="rounded-2xl border border-ocean-200 bg-ocean-900 p-6 text-white shadow-card">
            <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-aqua-200">Explore</span>
            <h2 className="mt-2 text-2xl font-semibold">See what the community is observing.</h2>
            <p className="mt-2 text-sm leading-relaxed text-ocean-100/80">
              Browse anonymized observations and their review status without exposing private citizen details.
            </p>
            <Link href="/explore" className="mt-6 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-medium text-ocean-900 hover:bg-ocean-50">
              Explore observations
              <Icon.ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
