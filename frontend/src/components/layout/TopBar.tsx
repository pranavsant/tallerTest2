"use client";

import { usePathname } from "next/navigation";
import { Bell, LogOut } from "lucide-react";
import { logout } from "@/app/login/actions";

// ---------------------------------------------------------------------------
// Derive a human-readable page title from the current pathname
// ---------------------------------------------------------------------------

function deriveTitle(pathname: string): string {
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return "Home";

  // /dashboard → "Dashboard"
  // /dashboard/agents → "Agents"
  // /dashboard/agents/[id] → "Agent Details"
  // /dashboard/sessions/new → "New Session"
  const last = segments[segments.length - 1];

  // If the last segment looks like a UUID, use "Details" as the suffix
  const uuidRe =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (uuidRe.test(last)) {
    const parent = segments[segments.length - 2] ?? "";
    return `${capitalise(parent.replace(/-/g, " "))} Details`;
  }

  return capitalise(last.replace(/-/g, " "));
}

function capitalise(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function TopBar({ userEmail }: { userEmail?: string | null }) {
  const pathname = usePathname();
  const title = deriveTitle(pathname);

  // Initial for the avatar; falls back to "U" when the email is unavailable.
  const initial = userEmail?.trim()?.[0]?.toUpperCase() ?? "U";

  return (
    <header className="fixed right-0 top-0 z-30 flex h-topbar items-center justify-between border-b border-topbar-border bg-topbar px-6 dark:border-topbar-border-dark dark:bg-topbar-dark"
      style={{ left: "var(--sidebar-width, 16rem)" }}
    >
      {/* Page title */}
      <h1 className="text-base font-semibold text-gray-900 dark:text-white">{title}</h1>

      {/* Right controls */}
      <div className="flex items-center gap-3">
        {/* Notification bell (placeholder) */}
        <button
          type="button"
          aria-label="Notifications"
          className="relative rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white"
        >
          <Bell className="h-4 w-4" aria-hidden="true" />
        </button>

        {/* User avatar */}
        <div
          aria-label="User menu"
          title={userEmail ?? undefined}
          className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white"
        >
          {initial}
        </div>

        {/* Logout — posts to the `logout` Server Action, which clears the
            session and redirects to /login (acceptance criterion 5). */}
        <form action={logout}>
          <button
            type="submit"
            aria-label="Sign out"
            className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white"
          >
            <LogOut className="h-4 w-4" aria-hidden="true" />
          </button>
        </form>
      </div>
    </header>
  );
}
