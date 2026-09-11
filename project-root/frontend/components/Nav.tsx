"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { Icon } from "@/components/ui/Icon";
import { useAuth } from "@/contexts/AuthContext";

export default function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const links =
    user?.role === "REVIEWER"
      ? [
          { href: "/dashboard", label: "Dashboard" },
          { href: "/cases", label: "Cases" },
        ]
      : user?.role === "CITIZEN"
        ? [
            { href: "/", label: "Report" },
            { href: "/my-reports", label: "My reports" },
          ]
        : [{ href: "/", label: "Report" }];

  function isActive(href: string) {
    if (href === "/") return pathname === "/";
    return pathname?.startsWith(href);
  }

  function handleLogout() {
    logout();
    setMenuOpen(false);
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-40 border-b border-ocean-100 bg-white/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5 font-semibold text-ocean-800">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-ocean-800 text-aqua-200">
            <Icon.Droplet className="h-5 w-5" />
          </span>
          <span className="text-[15px] leading-tight">
            Aqua Sentinel
            <span className="block text-[10px] font-medium uppercase tracking-wider text-ocean-400">
              Environmental Intelligence
            </span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 sm:flex">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
                isActive(l.href) ? "bg-ocean-800 text-white" : "text-ocean-700 hover:bg-ocean-50"
              }`}
            >
              {l.label}
            </Link>
          ))}

          {user ? (
            <div className="relative ml-2">
              <button
                onClick={() => setMenuOpen((v) => !v)}
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-ocean-700 hover:bg-ocean-50"
              >
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-aqua-100 text-[11px] font-semibold text-aqua-700">
                  {(user.display_name || user.email || "?").charAt(0).toUpperCase()}
                </span>
                {user.display_name || user.email}
                <Icon.ChevronDown className="h-3.5 w-3.5 text-ocean-400" />
              </button>
              {menuOpen && (
                <div className="absolute right-0 mt-1 w-44 rounded-lg border border-ocean-100 bg-white py-1 shadow-card-hover">
                  <div className="border-b border-ocean-100 px-3 py-2 text-xs text-ocean-400">
                    {user.role === "REVIEWER" ? "Reviewer" : "Citizen"}
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full px-3 py-2 text-left text-sm text-rose-600 hover:bg-rose-50"
                  >
                    Log out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="ml-2 flex items-center gap-2">
              <Link href="/login" className="rounded-lg px-3.5 py-2 text-sm font-medium text-ocean-700 hover:bg-ocean-50">
                Log in
              </Link>
              <Link href="/signup" className="btn-primary px-3.5 py-2 text-sm">
                Sign up
              </Link>
            </div>
          )}
        </nav>

        <button
          className="flex h-9 w-9 items-center justify-center rounded-lg text-ocean-700 hover:bg-ocean-50 sm:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
        >
          {open ? <Icon.X className="h-5 w-5" /> : <Icon.Menu className="h-5 w-5" />}
        </button>
      </div>

      {open && (
        <nav className="border-t border-ocean-100 bg-white px-4 py-2 sm:hidden">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className={`block rounded-lg px-3 py-2.5 text-sm font-medium ${
                isActive(l.href) ? "bg-ocean-800 text-white" : "text-ocean-700 hover:bg-ocean-50"
              }`}
            >
              {l.label}
            </Link>
          ))}
          {user ? (
            <button
              onClick={handleLogout}
              className="block w-full rounded-lg px-3 py-2.5 text-left text-sm font-medium text-rose-600 hover:bg-rose-50"
            >
              Log out ({user.display_name || user.email})
            </button>
          ) : (
            <>
              <Link href="/login" onClick={() => setOpen(false)} className="block rounded-lg px-3 py-2.5 text-sm font-medium text-ocean-700 hover:bg-ocean-50">
                Log in
              </Link>
              <Link href="/signup" onClick={() => setOpen(false)} className="block rounded-lg px-3 py-2.5 text-sm font-medium text-ocean-700 hover:bg-ocean-50">
                Sign up
              </Link>
            </>
          )}
        </nav>
      )}
    </header>
  );
}
