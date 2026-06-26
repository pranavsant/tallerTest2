import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { getCurrentUser } from "@/lib/auth/server";
import { RoleProvider } from "@/lib/auth/RoleProvider";

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
export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Belt-and-suspenders: the middleware already gates /dashboard, but guarding
  // here too means a Server Component never renders for an anonymous user even
  // if the matcher is ever misconfigured.
  const user = await getCurrentUser();

  if (!user) {
    redirect("/login");
  }

  return (
    // The role is resolved server-side and provided to Client Components so
    // they can conditionally render role-gated actions.
    <RoleProvider role={user.role}>
      <div className="flex min-h-screen">
        <Sidebar role={user.role} />

        {/* Content area — offset by sidebar width */}
        <div className="flex flex-1 flex-col pl-sidebar">
          <TopBar userEmail={user.email} role={user.role} />

          {/* Page content — padded below the fixed topbar */}
          <main className="flex-1 overflow-auto pt-topbar">
            <div className="px-6 py-8">{children}</div>
          </main>
        </div>
      </div>
    </RoleProvider>
  );
}
