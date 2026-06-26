import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { LoginForm } from "./LoginForm";

export const metadata: Metadata = {
  title: "Sign in",
};

/**
 * Login page (Server Component).
 *
 * If the visitor already has a valid session, skip the form and send them
 * straight to the dashboard. Otherwise render the email/password form, passing
 * through the optional `?redirect=` target so they land where they intended
 * after signing in.
 */
export default async function LoginPage({
  searchParams,
}: {
  searchParams?: { redirect?: string };
}) {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (user) {
    redirect("/dashboard");
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
            Overseer{" "}
            <span className="bg-gradient-to-r from-brand-600 to-purple-600 bg-clip-text text-transparent">
              AI
            </span>
          </h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Sign in to your account to continue.
          </p>
        </div>

        <div className="rounded-card border border-gray-200 bg-surface p-6 shadow-card dark:border-gray-800 dark:bg-surface-dark-muted">
          <LoginForm redirectTo={searchParams?.redirect} />
        </div>
      </div>
    </main>
  );
}
