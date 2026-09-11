"use client";

import { useState, FormEvent, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { Icon } from "@/components/ui/Icon";
import PasswordInput from "@/components/PasswordInput";

function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const user = await login(email, password);
      const next = params.get("next");
      router.push(next || (user.role === "REVIEWER" ? "/dashboard" : "/"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-[70vh] max-w-sm flex-col justify-center px-4 py-10 sm:px-6">
      <div className="mb-6 text-center">
        <span className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-ocean-800 text-aqua-200">
          <Icon.Droplet className="h-5 w-5" />
        </span>
        <h1 className="text-xl font-semibold text-ocean-900">Log in</h1>
        <p className="mt-1 text-sm text-ocean-500">Citizens and reviewers use the same login.</p>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-4 p-6">
        <div>
          <label htmlFor="email" className="label-field">Email</label>
          <input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="input-field" />
        </div>
        <PasswordInput label="Password" value={password} onChange={setPassword} autoComplete="current-password" />
        <button type="submit" disabled={submitting} className="btn-primary w-full">
          {submitting ? "Logging in…" : "Log in"}
        </button>
        {error && (
          <p className="flex items-center gap-1.5 text-sm text-rose-600">
            <Icon.Warning className="h-4 w-4 flex-shrink-0" />
            {error}
          </p>
        )}
      </form>

      <p className="mt-4 text-center text-sm text-ocean-500">
        No account? <Link href="/signup" className="font-medium text-aqua-600 hover:text-aqua-700">Sign up</Link>
      </p>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
