/**
 * Pure path helpers shared by the auth middleware and the login Server Action.
 *
 * Kept dependency-free (no Next.js / Supabase imports) so they can be unit
 * tested directly and reused on both the edge (middleware) and the server
 * (actions, route handlers).
 */

/** Routes that may be visited without an authenticated session. */
export const PUBLIC_PATHS = ["/login", "/auth"] as const;

/** True when `pathname` is one of the public routes (or nested under one). */
export function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some(
    (base) => pathname === base || pathname.startsWith(`${base}/`),
  );
}

/**
 * Sanitize a post-login redirect target. Only internal, absolute, single-slash
 * paths are allowed; anything else (external URLs, protocol-relative `//host`,
 * empty) falls back to the dashboard. Prevents open-redirect abuse via a
 * crafted `?redirect=` query param.
 */
export function safeRedirect(
  target: string | null | undefined,
  fallback = "/dashboard",
): string {
  if (target && target.startsWith("/") && !target.startsWith("//")) {
    return target;
  }
  return fallback;
}
