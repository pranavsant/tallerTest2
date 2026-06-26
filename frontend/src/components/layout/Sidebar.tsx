"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Bot,
  MessageSquare,
  Phone,
  Settings,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Nav items
// ---------------------------------------------------------------------------

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Agents", href: "/dashboard/agents", icon: Bot },
  { label: "Sessions", href: "/dashboard/sessions", icon: MessageSquare },
  { label: "Calls", href: "/dashboard/calls", icon: Phone },
  { label: "Settings", href: "/dashboard/settings", icon: Settings },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function Sidebar() {
  const pathname = usePathname();

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
          {NAV_ITEMS.map(({ label, href, icon: Icon }) => {
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
