"use client";

import { useEffect, useState } from "react";
import { adminApi, type AdminUser, type UserRole } from "@/lib/api";
import { ROLES } from "@/lib/auth/roles";
import { cn, formatDate } from "@/lib/utils";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";

/**
 * Admin UI for listing users, assigning roles, and deactivating/reactivating
 * accounts (acceptance criteria 1–4).
 *
 * Calls the admin API (`/admin/users`, `/admin/users/{id}/role`,
 * `/admin/users/{id}/status`), which the backend gates on the admin role. The
 * browser API client attaches the Supabase access token automatically, so
 * these requests are authenticated.
 *
 * Every mutating action is staged as a `PendingAction` and only submitted once
 * the admin confirms it in a modal (acceptance criterion 4).
 */

/** A staged, not-yet-submitted action awaiting confirmation. */
type PendingAction =
  | { kind: "role"; user: AdminUser; role: UserRole }
  | { kind: "status"; user: AdminUser; isActive: boolean };

export function UserRoleManager() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  // The action awaiting confirmation, or null when no dialog is open.
  const [pending, setPending] = useState<PendingAction | null>(null);
  // True while the confirmed action is being submitted.
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    adminApi
      .listUsers()
      .then((res) => setUsers(res.users))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  function replaceUser(updated: AdminUser) {
    setUsers((prev) => prev.map((u) => (u.user_id === updated.user_id ? updated : u)));
  }

  async function confirmPending() {
    if (!pending) return;
    setSubmitting(true);
    setError(null);
    setNotice(null);
    const { user } = pending;
    const label = user.email ?? user.user_id;
    try {
      if (pending.kind === "role") {
        const updated = await adminApi.assignRole(user.user_id, {
          role: pending.role,
        });
        replaceUser(updated);
        setNotice(`Updated ${label} to ${pending.role}.`);
      } else {
        const updated = await adminApi.setActive(user.user_id, {
          is_active: pending.isActive,
        });
        replaceUser(updated);
        setNotice(`${pending.isActive ? "Reactivated" : "Deactivated"} ${label}.`);
      }
      setPending(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-14 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-800" />
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
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Last sign-in</th>
              <th className="px-4 py-3 font-medium">Role</th>
              <th className="px-4 py-3 font-medium">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {users.map((user) => (
              <tr key={user.user_id} className={cn(!user.is_active && "opacity-60")}>
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900 dark:text-white">
                    {user.email ?? "—"}
                  </div>
                  <div className="text-xs text-gray-400">{user.user_id}</div>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge isActive={user.is_active} />
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
                    disabled={submitting || !user.is_active}
                    onChange={(e) => {
                      const role = e.target.value as UserRole;
                      if (role !== user.role) {
                        setPending({ kind: "role", user, role });
                      }
                    }}
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
                <td className="px-4 py-3 text-right">
                  <button
                    type="button"
                    disabled={submitting}
                    onClick={() =>
                      setPending({
                        kind: "status",
                        user,
                        isActive: !user.is_active,
                      })
                    }
                    className={cn(
                      "rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-50",
                      user.is_active
                        ? "text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                        : "text-green-700 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-900/20",
                    )}
                  >
                    {user.is_active ? "Deactivate" : "Reactivate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ConfirmDialog
        open={pending !== null}
        busy={submitting}
        tone={pending?.kind === "status" && !pending.isActive ? "danger" : "default"}
        title={confirmTitle(pending)}
        description={confirmDescription(pending)}
        confirmLabel={confirmActionLabel(pending)}
        onConfirm={confirmPending}
        onCancel={() => {
          if (!submitting) setPending(null);
        }}
      />
    </div>
  );
}

function StatusBadge({ isActive }: { isActive: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-pill px-2.5 py-0.5 text-xs font-medium",
        isActive
          ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
          : "bg-gray-200 text-gray-700 dark:bg-gray-800 dark:text-gray-400",
      )}
    >
      {isActive ? "Active" : "Deactivated"}
    </span>
  );
}

// ── Confirmation copy ─────────────────────────────────────────────────────────

function userLabel(user: AdminUser): string {
  return user.email ?? user.user_id;
}

function confirmTitle(action: PendingAction | null): string {
  if (!action) return "";
  if (action.kind === "role") return "Change role?";
  return action.isActive ? "Reactivate account?" : "Deactivate account?";
}

function confirmDescription(action: PendingAction | null): React.ReactNode {
  if (!action) return null;
  const name = userLabel(action.user);
  if (action.kind === "role") {
    return (
      <>
        Change <strong>{name}</strong>&rsquo;s role from{" "}
        <strong>{action.user.role ?? "none"}</strong> to <strong>{action.role}</strong>? This takes
        effect on their next sign-in.
      </>
    );
  }
  if (action.isActive) {
    return (
      <>
        Reactivate <strong>{name}</strong>? They will be able to sign in again.
      </>
    );
  }
  return (
    <>
      Deactivate <strong>{name}</strong>? They will be signed out and blocked from signing in until
      reactivated.
    </>
  );
}

function confirmActionLabel(action: PendingAction | null): string {
  if (!action) return "Confirm";
  if (action.kind === "role") return "Change role";
  return action.isActive ? "Reactivate" : "Deactivate";
}
