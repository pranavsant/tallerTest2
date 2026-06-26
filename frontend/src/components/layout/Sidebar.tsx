"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Bot,
  MessageSquare,
  Phone,
  Settings,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/lib/types";
import { canManageUsers } from "@/lib/auth/roles";

// ---------------------------------------------------------------------------
// Nav items
// ---------------------------------------------------------------------------

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  /** When set, the item is only shown to users holding one of these roles. */
  requiresRole?: UserRole[];
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Agents", href: "/dashboard/agents", icon: Bot },
  { label: "Sessions", href: "/dashboard/sessions", icon: MessageSquare },
  { label: "Calls", href: "/dashboard/calls", icon: Phone },
  { label: "Settings", href: "/dashboard/settings", icon: Settings },
  // Admin-only: user & role management.
  {
    label: "Admin",
    href: "/dashboard/admin",
    icon: ShieldCheck,
    requiresRole: ["admin"],
  },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function Sidebar({ role }: { role: UserRole | null }) {
  const pathname = usePathname();

  const visibleItems = NAV_ITEMS.filter((item) => {
    if (!item.requiresRole) return true;
    // Currently only the admin item is gated; keep the check general.
    return item.href === "/dashboard/admin" ? canManageUsers(role) : true;
  });

  return (
    <aside className="fixed inset-y-0 left-0 z-40 flex w-sidebar flex-col bg-sidebar shadow-sidebar">
      {/* Logo / wordmark */}
      <div className="flex h-topbar shrink-0 items-center gap-3 border-b border-sidebar-border px-5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-600">
          <span className="text-sm font-bold text-white">O</span>
        </div>
        <span className="text-base font-semibold tracking-tight text-sidebar-text-active">
          Overseer AI
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1" role="list">
          {visibleItems.map(({ label, href, icon: Icon }) => {
            // Active if pathname equals the href, or starts with it (for nested routes)
            // except for /dashboard itself which would match everything.
            const isActive =
              href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(href);

            return (
              <li key={href}>
                <Link
                  href={href}
                  className={cn(
                    "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-sidebar-item text-sidebar-text-active"
                      : "text-sidebar-text hover:bg-sidebar-item/60 hover:text-sidebar-text-active",
                  )}
                  aria-current={isActive ? "page" : undefined}
                >
                  <Icon
                    className={cn(
                      "h-4 w-4 shrink-0 transition-colors",
                      isActive
                        ? "text-brand-400"
                        : "text-sidebar-text group-hover:text-brand-400",
                    )}
                    aria-hidden="true"
                  />
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="shrink-0 border-t border-sidebar-border px-5 py-4">
        <p className="text-xs text-sidebar-text">
          Overseer AI &copy; {new Date().getFullYear()}
        </p>
      </div>
    </aside>
  );
}
