"use client";

import { useId, useState } from "react";

function EyeIcon({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className} aria-hidden="true">
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function EyeOffIcon({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className} aria-hidden="true">
      <path d="M3 3l18 18" />
      <path d="M10.6 5.1A10.9 10.9 0 0 1 12 5c6.5 0 10 7 10 7a17.7 17.7 0 0 1-3.2 4.1M6.3 6.3A17.6 17.6 0 0 0 2 12s3.5 7 10 7c1.3 0 2.5-.2 3.6-.6" />
      <path d="M9.5 9.5a3 3 0 0 0 4.2 4.2" />
    </svg>
  );
}

// The ONLY rule the backend actually enforces (SignupRequest.password:
// min_length=8) — shown as a real requirement. Anything below is purely
// informational strength guidance, never presented as a requirement, so
// the UI never claims the backend enforces more than it does.
const MIN_LENGTH = 8;

function strengthOf(value: string): { label: string; ratio: number; color: string } | null {
  if (value.length === 0) return null;
  let score = 0;
  if (value.length >= MIN_LENGTH) score++;
  if (value.length >= 12) score++;
  if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score++;
  if (/\d/.test(value)) score++;
  if (/[^A-Za-z0-9]/.test(value)) score++;

  if (score <= 1) return { label: "Weak", ratio: 0.33, color: "bg-rose-500" };
  if (score <= 3) return { label: "Fair", ratio: 0.66, color: "bg-amber-500" };
  return { label: "Good", ratio: 1, color: "bg-moss-500" };
}

export default function PasswordInput({
  label,
  value,
  onChange,
  autoComplete,
  showStrength = false,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  autoComplete: string;
  showStrength?: boolean;
}) {
  const id = useId();
  const [visible, setVisible] = useState(false);
  const strength = showStrength ? strengthOf(value) : null;

  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={visible ? "text" : "password"}
          required
          minLength={MIN_LENGTH}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          autoComplete={autoComplete}
          className="input-field pr-10"
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
          aria-pressed={visible}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-slate-400 transition-colors hover:text-moss-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-moss-500"
        >
          {visible ? <EyeOffIcon /> : <EyeIcon />}
        </button>
      </div>

      {showStrength && strength && (
        <div className="mt-1.5">
          <div className="mb-1 h-1 w-full overflow-hidden rounded-full bg-slate-100">
            <div className={`h-full rounded-full transition-all ${strength.color}`} style={{ width: `${strength.ratio * 100}%` }} />
          </div>
          <p className="text-xs text-slate-500">
            Strength: <span className="font-medium">{strength.label}</span>
            {value.length < MIN_LENGTH && <span className="text-rose-600"> · needs at least {MIN_LENGTH} characters</span>}
          </p>
        </div>
      )}
    </div>
  );
}
