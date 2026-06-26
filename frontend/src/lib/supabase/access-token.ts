/**
 * Browser access-token provider for the API client.
 *
 * The {@link ApiClient} attaches `Authorization: Bearer <token>` when given a
 * `getAuthToken` hook (see `http.ts`). This module supplies that hook for the
 * browser: it reads the current Supabase session and returns its access token,
 * which the FastAPI backend validates and maps to roles.
 *
 * Guards:
 *  - Returns `null` on the server (no `window`), so importing the shared API
 *    client in a Server Component never reaches into the browser Supabase
 *    client. Server-side callers that need an authenticated request should
 *    build a request-scoped client with the server Supabase session instead.
 *  - `@supabase/ssr`'s browser client refreshes the token from cookies as
 *    needed, so the returned token is always current.
 */

import { createClient } from "./client";

export async function getBrowserAccessToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;

  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return session?.access_token ?? null;
}
