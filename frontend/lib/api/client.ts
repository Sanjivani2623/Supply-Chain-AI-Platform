/**
 * Thin fetch wrapper around the FastAPI backend.
 *
 * - Attaches the JWT access token from localStorage as a Bearer token.
 * - On a 401, silently exchanges the refresh token for a new access token
 *   and retries the request once. This is what actually fixes "everything
 *   breaks after ~60 minutes" - previously a 401 just surfaced as a raw
 *   error on every card with no recovery.
 * - If refresh also fails (or there's no refresh token), it clears auth,
 *   shows a toast, and redirects to /login - once, even if many requests
 *   401 at the same time (single-flight refresh + a redirect guard).
 */
import { toast } from "@/lib/toast/store";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("refresh_token");
}

function setTokens(access: string, refresh: string) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

/** A 401/expired-session error that has already been surfaced to the user
 * (toast shown, redirect triggered) - callers should not toast it again. */
export class SessionExpiredError extends Error {
  handled = true;
  constructor() {
    super("Session expired");
    this.name = "SessionExpiredError";
  }
}

let refreshPromise: Promise<boolean> | null = null;
let redirecting = false;

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  if (!refreshPromise) {
    refreshPromise = fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
      .then(async (res) => {
        if (!res.ok) return false;
        const data = await res.json();
        setTokens(data.access_token, data.refresh_token);
        return true;
      })
      .catch(() => false)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

function redirectToLogin(message: string) {
  clearTokens();
  if (!redirecting) {
    redirecting = true;
    toast.error(message);
    if (typeof window !== "undefined" && window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
    setTimeout(() => (redirecting = false), 2000);
  }
}

async function doFetch(path: string, options: RequestInit, token: string | null): Promise<Response> {
  const headers: Record<string, string> = {
    ...(options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return fetch(`${API_URL}${path}`, { ...options, headers });
}

export async function apiFetch<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  let token = getAccessToken();
  let res = await doFetch(path, options, token);

  if (res.status === 401 && path !== "/api/v1/auth/login" && path !== "/api/v1/auth/refresh") {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      token = getAccessToken();
      res = await doFetch(path, options, token);
    }
    if (res.status === 401) {
      redirectToLogin("Your session expired. Please log in again.");
      throw new SessionExpiredError();
    }
  }

  if (!res.ok) {
    let detail = "";
    try {
      const body = await res.json();
      detail = body.detail ? (typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail)) : JSON.stringify(body);
    } catch {
      detail = await res.text().catch(() => res.statusText);
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export async function login(email: string, password: string) {
  const data = await apiFetch<{ access_token: string; refresh_token: string }>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export function logout() {
  clearTokens();
}

export function isLoggedIn(): boolean {
  return !!getAccessToken();
}
