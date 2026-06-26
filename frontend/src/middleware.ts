/**
 * Next.js middleware entry point.
 *
 * Runs on every request matched by `config.matcher` and delegates to
 * `updateSession`, which refreshes the Supabase auth cookies and enforces
 * route protection (redirecting unauthenticated users to `/login`).
 *
 * Acceptance criteria covered here:
 *  - Session cookie is refreshed on every request (criterion 4).
 *  - Unauthenticated users are redirected to /login (criterion 2).
 */

import type { NextRequest } from "next/server";
import { updateSession } from "@/lib/supabase/middleware";

export async function middleware(request: NextRequest) {
  return updateSession(request);
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public asset extensions (images, fonts, etc.)
     *
     * This ensures the session is refreshed on every page navigation while
     * skipping static assets that don't need an auth check.
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|woff|woff2|ttf)$).*)",
  ],
};
