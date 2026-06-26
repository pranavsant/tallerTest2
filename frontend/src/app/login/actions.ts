"use server";

/**
 * Server Actions for the auth flows.
 *
 * These run on the server, use the cookie-bound Supabase server client, and
 * return a serializable result the form can render. On success they redirect;
 * on failure they return a `{ error }` shape so the login page can show inline
 * error states (acceptance criterion 3).
 */

import { redirect } from "next/navigation";
import { z } from "zod";
import { createClient } from "@/lib/supabase/server";
import { safeRedirect } from "@/lib/supabase/paths";

/** Shape returned to the client form on validation/auth failure. */
export interface AuthActionState {
  error: string | null;
}

const credentialsSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(1, "Password is required."),
  // Optional safe-internal redirect target supplied by the login page.
  redirectTo: z.string().optional(),
});

/**
 * Sign in with email + password. On success the Supabase client sets the
 * session cookies; we then redirect to the originally-requested page.
 */
export async function login(
  _prevState: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const parsed = credentialsSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
    redirectTo: formData.get("redirectTo") ?? undefined,
  });

  if (!parsed.success) {
    return { error: parsed.error.issues[0]?.message ?? "Invalid input." };
  }

  const supabase = createClient();
  const { error } = await supabase.auth.signInWithPassword({
    email: parsed.data.email,
    password: parsed.data.password,
  });

  if (error) {
    return { error: error.message };
  }

  redirect(safeRedirect(parsed.data.redirectTo));
}

/**
 * Sign out the current user, clearing the session cookies, then send them to
 * the login page (acceptance criterion 5).
 */
export async function logout(): Promise<void> {
  const supabase = createClient();
  await supabase.auth.signOut();
  redirect("/login");
}
