"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { Icon } from "@/components/ui/Icon";
import PasswordInput from "@/components/PasswordInput";

export default function SignupPage() {
  const { signup } = useAuth();
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const passwordsMatch = confirmPassword.length > 0 && password === confirmPassword;
  const passwordTooShort = password.length > 0 && password.length < 8;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (password.length < 8) return setError("Password must be at least 8 characters.");
    if (password !== confirmPassword) return setError("Passwords do not match.");

    setSubmitting(true);
    try {
      await signup(email, password, displayName || undefined);
      router.push("/"); // public signup always creates a CITIZEN account
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed.");
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
        <h1 className="text-xl font-semibold text-ocean-900">Create an account</h1>
        <p className="mt-1 text-sm text-ocean-500">Sign up to submit and track stream observations.</p>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-4 p-6" noValidate>
        <div>
          <label htmlFor="name" className="label-field">Name <span className="font-normal text-ocean-400">(optional)</span></label>
          <input id="name" type="text" value={displayName} onChange={(e) => setDisplayName(e.target.value)} className="input-field" />
        </div>
        <div>
          <label htmlFor="email" className="label-field">Email</label>
          <input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="input-field" />
        </div>

        <PasswordInput label="Password" value={password} onChange={setPassword} autoComplete="new-password" showStrength />

        <div>
          <PasswordInput label="Confirm password" value={confirmPassword} onChange={setConfirmPassword} autoComplete="new-password" />
          {confirmPassword.length > 0 && (
            <p className={`mt-1 flex items-center gap-1 text-xs ${passwordsMatch ? "text-moss-700" : "text-rose-600"}`}>
              {passwordsMatch ? <><Icon.Check className="h-3.5 w-3.5" /> Passwords match</> : "Passwords do not match."}
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={submitting || passwordTooShort || !passwordsMatch}
          className="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Creating account…" : "Create account"}
        </button>
        {error && (
          <p className="flex items-center gap-1.5 text-sm text-rose-600" role="alert">
            <Icon.Warning className="h-4 w-4 flex-shrink-0" />
            {error}
          </p>
        )}
      </form>

      <p className="mt-4 text-center text-sm text-ocean-500">
        Already have an account? <Link href="/login" className="font-medium text-aqua-600 hover:text-aqua-700">Log in</Link>
      </p>
    </main>
  );
}
