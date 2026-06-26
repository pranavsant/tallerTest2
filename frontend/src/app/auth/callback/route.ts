/**
 * OAuth / email-confirmation callback handler.
 *
 * Supabase Auth redirects here with a one-time `code` after the user completes
 * an email-link or OAuth flow. We exchange that code for a session (which sets
 * the auth cookies via the server client) and then redirect into the app.
 *
 * This is required for any non-password flow (magic link, email confirmation,
 * OAuth) to land the user with a valid SSR session.
 */

import { NextResponse, type NextRequest } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { safeRedirect } from "@/lib/supabase/paths";

export async function GET(request: NextRequest) {
  const { searchParams, origin } = request.nextUrl;
  const code = searchParams.get("code");
  const next = safeRedirect(searchParams.get("next"));

  if (code) {
    const supabase = createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  // No code, or the exchange failed → back to login with an error flag.
  return NextResponse.redirect(`${origin}/login?error=auth`);
}
