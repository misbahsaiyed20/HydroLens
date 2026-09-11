"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Role } from "@/lib/auth";
import { Icon } from "@/components/ui/Icon";
import { LoadingState } from "@/components/ui/States";

/**
 * Client-side route guard. This is a UX convenience, NOT the security
 * boundary — every protected page here also calls a reviewer/citizen-only
 * API endpoint that the backend enforces independently (see
 * app/core/deps.py::require_reviewer). Hiding the nav link or this guard
 * alone would never be sufficient.
 */
export default function RequireRole({ role, children }: { role: Role; children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace(`/login?next=${encodeURIComponent(window.location.pathname)}`);
    }
  }, [loading, user, router]);

  if (loading) return <LoadingState label="Checking your session…" rows={2} />;

  if (!user) return null; // redirecting

  if (user.role !== role) {
    return (
      <div className="mx-auto max-w-md py-16 text-center">
        <span className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-rose-50 text-rose-500 shadow-card">
          <Icon.Shield className="h-5 w-5" />
        </span>
        <p className="text-sm font-medium text-ocean-700">
          This page is for {role === "REVIEWER" ? "reviewers" : "citizens"} only.
        </p>
        <Link href="/" className="mt-3 inline-block text-sm font-medium text-aqua-600 hover:text-aqua-700">
          Back to home
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}
