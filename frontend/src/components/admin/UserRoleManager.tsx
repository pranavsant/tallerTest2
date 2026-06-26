"use client";

import { useEffect, useState } from "react";
import { adminApi, type AdminUser, type UserRole } from "@/lib/api";
import { ROLES } from "@/lib/auth/roles";
import { formatDate } from "@/lib/utils";

/**
 * Admin UI for listing users and assigning roles (acceptance criterion 4).
 *
 * Calls the admin API (`/admin/users`, `/admin/users/{id}/role`), which the
 * backend gates on the admin role. The browser API client attaches the
 * Supabase access token automatically, so these requests are authenticated.
 */
export function UserRoleManager() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // user_id currently being saved → disables its control and shows progress.
  const [savingId, setSavingId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    adminApi
      .listUsers()
      .then((res) => setUsers(res.users))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function handleRoleChange(user: AdminUser, role: UserRole) {
    const previous = user.role;
    setSavingId(user.user_id);
    setError(null);
    setNotice(null);
    // Optimistic update; rolled back on failure.
    setUsers((prev) =>
      prev.map((u) => (u.user_id === user.user_id ? { ...u, role } : u)),
    );
    try {
      const updated = await adminApi.assignRole(user.user_id, { role });
      setUsers((prev) =>
        prev.map((u) => (u.user_id === user.user_id ? updated : u)),
      );
      setNotice(`Updated ${user.email ?? user.user_id} to ${role}.`);
    } catch (err) {
      setUsers((prev) =>
        prev.map((u) =>
          u.user_id === user.user_id ? { ...u, role: previous } : u,
        ),
      );
      setError(err instanceof Error ? err.message : "Failed to update role.");
    } finally {
      setSavingId(null);
    }
  }

  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-14 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-800"
          />
        ))}
      </div>
    );
  }

  if (error && users.length === 0) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
        Failed to load users: {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {notice && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700 dark:border-green-800 dark:bg-green-900/20 dark:text-green-400">
          {notice}
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      )}

      <div className="overflow-x-auto rounded-card border border-gray-200 dark:border-gray-800">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase tracking-wide text-gray-500 dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-400">
            <tr>
              <th className="px-4 py-3 font-medium">User</th>
              <th className="px-4 py-3 font-medium">Last sign-in</th>
              <th className="px-4 py-3 font-medium">Role</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {users.map((user) => (
              <tr key={user.user_id}>
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900 dark:text-white">
                    {user.email ?? "—"}
                  </div>
                  <div className="text-xs text-gray-400">{user.user_id}</div>
                </td>
                <td className="px-4 py-3 text-gray-500 dark:text-gray-400">
                  {user.last_sign_in_at ? formatDate(user.last_sign_in_at) : "Never"}
                </td>
                <td className="px-4 py-3">
                  <label className="sr-only" htmlFor={`role-${user.user_id}`}>
                    Role for {user.email ?? user.user_id}
                  </label>
                  <select
                    id={`role-${user.user_id}`}
                    value={user.role ?? ""}
                    disabled={savingId === user.user_id}
                    onChange={(e) =>
                      handleRoleChange(user, e.target.value as UserRole)
                    }
                    className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm capitalize text-gray-900 disabled:opacity-50 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
                  >
                    {user.role === null && (
                      <option value="" disabled>
                        — none —
                      </option>
                    )}
                    {ROLES.map((r) => (
                      <option key={r} value={r} className="capitalize">
                        {r}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
