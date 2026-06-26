/**
 * Server-side current-user/role access.
 *
 * Reads the authenticated user via the cookie-bound Supabase server client and
 * extracts their application role from `app_metadata`. Use this in Server
 * Components, Route Handlers, and Server Actions — never from a Client
 * Component (it touches `next/headers`).
 */

import { createClient } from "@/lib/supabase/server";
import type { UserRole } from "@/lib/types";
import { roleFromMetadata } from "./roles";

export interface CurrentUser {
  id: string;
  email: string | null;
  role: UserRole | null;
}

/**
 * Return the current authenticated user and their role, or `null` when there
 * is no session. Uses `getUser()` (revalidated against Supabase Auth) rather
 * than `getSession()`, matching the middleware's trust model.
 */
export async function getCurrentUser(): Promise<CurrentUser | null> {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) return null;

  return {
    id: user.id,
    email: user.email ?? null,
    role: roleFromMetadata(user.app_metadata as Record<string, unknown>),
  };
}
