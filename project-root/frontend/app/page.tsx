import Link from "next/link";
import ReportForm from "@/components/ReportForm";

export default function HomePage() {
  return (
    <main className="max-w-xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-semibold mb-1">Aqua Sentinel</h1>
      <p className="text-sm text-slate-600 mb-8">
        Report an observable condition in a local stream. This does not diagnose
        water quality — it records an observation for review.
      </p>
      <ReportForm />
      <div className="mt-8 border-t border-slate-200 pt-4">
        <Link href="/dashboard" className="text-sm text-blue-600 hover:underline">
          Officer dashboard →
        </Link>
      </div>
    </main>
  );
}
