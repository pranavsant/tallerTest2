import type { Metadata } from "next";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";

export const metadata: Metadata = {
  title: "Dashboard",
};

/**
 * Shell layout shared by all /dashboard/** routes.
 *
 * Structure:
 *   ┌──────────┬──────────────────────────────┐
 *   │          │  TopBar (h-topbar = 64 px)    │
 *   │ Sidebar  ├──────────────────────────────┤
 *   │ (w-sidebar = 256 px)                    │
 *   │          │  <children>                  │
 *   └──────────┴──────────────────────────────┘
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />

      {/* Content area — offset by sidebar width */}
      <div className="flex flex-1 flex-col pl-sidebar">
        <TopBar />

        {/* Page content — padded below the fixed topbar */}
        <main className="flex-1 overflow-auto pt-topbar">
          <div className="px-6 py-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
