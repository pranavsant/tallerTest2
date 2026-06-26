import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { canManageUsers } from "@/lib/auth/roles";
import { UserRoleManager } from "@/components/admin/UserRoleManager";

export const metadata: Metadata = {
  title: "Admin",
};

/**
 * Admin panel — user & role management (acceptance criterion 4).
 *
 * Server-guarded: non-admins are redirected away. This is defence in depth on
 * top of the sidebar hiding the link and the backend `/admin/*` routes
 * enforcing the admin role; the API is the real boundary.
 */
export default async function AdminPage() {
  const user = await getCurrentUser();

  if (!canManageUsers(user?.role ?? null)) {
    redirect("/dashboard");
  }

  return (
    <>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">User Management</h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Assign roles to control who can configure feeds, trigger calls, and acknowledge incidents,
          and deactivate accounts to revoke access.
        </p>
      </div>

      <UserRoleManager />
    </>
  );
}
