/**
 * Session refresh + route protection for Next.js middleware.
 *
 * `updateSession` runs on every matched request (see `@/middleware`). It:
 *  1. Constructs a Supabase server client bound to the request/response cookies.
 *  2. Calls `getUser()`, which refreshes the access token when it has expired
 *     and writes the rotated auth cookies onto the outgoing response.
 *  3. Redirects unauthenticated users away from protected routes to `/login`.
 *
 * Why `getUser()` and not `getSession()`: `getUser()` revalidates the token
 * with the Supabase Auth server, so the auth decision can't be spoofed by a
 * forged cookie. `getSession()` trusts the cookie as-is and must not gate
 * access in middleware.
 *
 * This `@supabase/ssr` version uses the per-cookie `get`/`set`/`remove`
 * interface. Each write is mirrored onto both the request cookies (so a later
 * read in this same pass sees it) and the outgoing response (so the browser
 * persists the refreshed session).
 */

import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_SUPABASE_URL } from "@/env";
import { isPublicPath } from "./paths";

export async function updateSession(request: NextRequest): Promise<NextResponse> {
  // Mutable response we hand back; cookie writes are layered onto it below.
  const response = NextResponse.next({ request });

  const supabase = createServerClient(
    NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value;
        },
        set(name: string, value: string, options: CookieOptions) {
          request.cookies.set({ name, value, ...options });
          response.cookies.set({ name, value, ...options });
        },
        remove(name: string, options: CookieOptions) {
          request.cookies.set({ name, value: "", ...options });
          response.cookies.set({ name, value: "", ...options, maxAge: 0 });
        },
      },
    },
  );

  // Refreshes the session and rotates cookies when the access token expired.
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { pathname } = request.nextUrl;

  // Unauthenticated user hitting a protected route → send to /login,
  // preserving where they were going via ?redirect=.
  if (!user && !isPublicPath(pathname)) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.search = "";
    if (pathname && pathname !== "/") {
      loginUrl.searchParams.set("redirect", pathname);
    }
    return NextResponse.redirect(loginUrl);
  }

  // Authenticated user on the login page → bounce to the dashboard.
  if (user && pathname === "/login") {
    const dashboardUrl = request.nextUrl.clone();
    dashboardUrl.pathname = "/dashboard";
    dashboardUrl.search = "";
    return NextResponse.redirect(dashboardUrl);
  }

  return response;
}
