/**
 * Role helpers shared by server and client auth code.
 *
 * The authoritative role lives in the Supabase user's `app_metadata`, written
 * by the backend admin API and stamped onto the access token. These pure
 * helpers extract and reason about that role; they hold no Supabase or React
 * dependency so they can be unit tested and used on either side.
 */

import type { UserRole } from "@/lib/types";

export const ROLES: readonly UserRole[] = ["admin", "operator", "viewer"];

/** Shape of the slice of Supabase user metadata we read the role from. */
export interface RoleMetadata {
  // Supabase populates `app_metadata`; we accept both a `roles` array and a
  // scalar `role` to match what the backend writes.
  roles?: unknown;
  role?: unknown;
}

/** True when `value` is one of the recognised application roles. */
export function isRole(value: unknown): value is UserRole {
  return typeof value === "string" && (ROLES as readonly string[]).includes(value);
}

/**
 * Extract the application role from a user's `app_metadata`. Prefers the first
 * valid entry of `roles`, falling back to the scalar `role`. Returns `null`
 * when no application role is present.
 */
export function roleFromMetadata(appMetadata: RoleMetadata | null | undefined): UserRole | null {
  if (!appMetadata) return null;

  const { roles, role } = appMetadata;
  if (Array.isArray(roles)) {
    const found = roles.find(isRole);
    if (found) return found;
  }
  if (isRole(role)) return role;
  return null;
}

// ── Capability checks ────────────────────────────────────────────────────────
// Centralize "what can each role do" so the UI and any guards agree. These
// mirror the backend's `require_role` enforcement (the server is authoritative;
// these only decide what to render).

/** Admins can configure feeds and trigger calls. */
export function canManageFeeds(role: UserRole | null): boolean {
  return role === "admin";
}

export function canTriggerCalls(role: UserRole | null): boolean {
  return role === "admin";
}

/** Operators (and admins) can acknowledge incidents. */
export function canAcknowledgeIncidents(role: UserRole | null): boolean {
  return role === "admin" || role === "operator";
}

/** Only admins can manage users and assign roles. */
export function canManageUsers(role: UserRole | null): boolean {
  return role === "admin";
}
