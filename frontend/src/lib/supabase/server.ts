/**
 * Supabase client for **server-side** code: Server Components, Route Handlers,
 * and Server Actions.
 *
 * Uses `@supabase/ssr`'s `createServerClient`, wired to Next.js's request
 * cookie store so the session is read from — and refreshed into — cookies.
 *
 * Notes:
 *  - This `@supabase/ssr` version exposes the per-cookie `get`/`set`/`remove`
 *    interface (rather than the newer `getAll`/`setAll`).
 *  - `cookies()` is read-only inside Server Components. When Supabase tries to
 *    refresh the session there, the `set`/`remove` writes throw; we swallow
 *    that error because the middleware (see `@/lib/supabase/middleware`) is
 *    responsible for persisting refreshed cookies on every request.
 *  - This module is server-only; it must never be imported from a Client
 *    Component (it touches `next/headers`).
 */

import { cookies } from "next/headers";
import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_SUPABASE_URL } from "@/env";

/**
 * Create a request-scoped Supabase client backed by the Next.js cookie store.
 *
 * Must be called within a request scope (Server Component, Route Handler, or
 * Server Action) because it reads `cookies()` from `next/headers`.
 */
export function createClient() {
  const cookieStore = cookies();

  return createServerClient(NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, {
    cookies: {
      get(name: string) {
        return cookieStore.get(name)?.value;
      },
      set(name: string, value: string, options: CookieOptions) {
        try {
          cookieStore.set(name, value, options);
        } catch {
          // Called from a Server Component, where the cookie store is
          // read-only. Safe to ignore: the middleware refreshes the session
          // cookies on every request.
        }
      },
      remove(name: string, options: CookieOptions) {
        try {
          cookieStore.set(name, "", { ...options, maxAge: 0 });
        } catch {
          // See note in `set` above.
        }
      },
    },
  });
}
