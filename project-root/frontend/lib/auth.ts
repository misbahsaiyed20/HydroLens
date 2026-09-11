const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

export type Role = "CITIZEN" | "REVIEWER";

export type AuthUser = {
  id: string;
  email: string | null;
  display_name: string | null;
  role: Role;
  created_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user: AuthUser;
};

const TOKEN_KEY = "aqua_sentinel_token";

// Token lives in localStorage (not an httpOnly cookie) — the simplest fit for
// this project's current architecture (no server-rendered session, no
// separate auth service). It never touches NEXT_PUBLIC_* env vars or
// anything bundled into client JS beyond what the user explicitly stores.
export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

async function authFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
  } catch {
    // fetch() itself threw — the request never reached the server at all
    // (backend down, wrong URL, CORS, offline). This is the actual source
    // of the raw browser "Failed to fetch" TypeError; replace it with a
    // message the user can act on.
    throw new Error("Unable to connect to Aqua Sentinel. Please make sure the server is running.");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ? String(body.detail) : `Request failed (${res.status}).`);
  }
  return res.json();
}

export function signup(email: string, password: string, displayName?: string) {
  return authFetch<TokenResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password, display_name: displayName || undefined }),
  });
}

export function login(email: string, password: string) {
  return authFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function fetchCurrentUser(token: string) {
  return authFetch<AuthUser>("/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}
