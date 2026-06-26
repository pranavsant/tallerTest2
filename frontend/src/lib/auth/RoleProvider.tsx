"use client";

/**
 * Client-side role context.
 *
 * The role is resolved once on the server (see `lib/auth/server.ts`) and passed
 * into this provider from the dashboard layout, so Client Components can gate
 * UI on the user's role without each re-fetching the session.
 *
 * This drives *rendering* only. Authorization is enforced server-side by the
 * backend's `require_role`; hiding an action here is a UX nicety, not a
 * security boundary.
 */

import { createContext, useContext, type ReactNode } from "react";
import type { UserRole } from "@/lib/types";
import {
  canAcknowledgeIncidents,
  canManageFeeds,
  canManageUsers,
  canTriggerCalls,
} from "./roles";

interface RoleContextValue {
  role: UserRole | null;
  is: (role: UserRole) => boolean;
  canManageFeeds: boolean;
  canTriggerCalls: boolean;
  canAcknowledgeIncidents: boolean;
  canManageUsers: boolean;
}

const RoleContext = createContext<RoleContextValue | null>(null);

export function RoleProvider({
  role,
  children,
}: {
  role: UserRole | null;
  children: ReactNode;
}) {
  const value: RoleContextValue = {
    role,
    is: (r) => role === r,
    canManageFeeds: canManageFeeds(role),
    canTriggerCalls: canTriggerCalls(role),
    canAcknowledgeIncidents: canAcknowledgeIncidents(role),
    canManageUsers: canManageUsers(role),
  };

  return <RoleContext.Provider value={value}>{children}</RoleContext.Provider>;
}

/**
 * Read the current user's role and capability flags. Must be called within a
 * {@link RoleProvider} (the dashboard layout provides one).
 */
export function useRole(): RoleContextValue {
  const ctx = useContext(RoleContext);
  if (ctx === null) {
    throw new Error("useRole must be used within a <RoleProvider>");
  }
  return ctx;
}
