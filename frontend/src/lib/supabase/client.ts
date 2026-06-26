/**
 * Supabase client for **Client Components** (browser).
 *
 * Uses `@supabase/ssr`'s `createBrowserClient`, which reads and writes the
 * auth session from cookies so it stays in sync with the server-side client
 * and the middleware. Import this only from `"use client"` modules.
 */

import { createBrowserClient } from "@supabase/ssr";
import { NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_SUPABASE_URL } from "@/env";

/**
 * Create a Supabase client bound to the browser's cookie store.
 *
 * `createBrowserClient` is internally memoized by `@supabase/ssr`, so calling
 * this per component render is cheap and returns the same underlying client.
 */
export function createClient() {
  return createBrowserClient(NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY);
}
