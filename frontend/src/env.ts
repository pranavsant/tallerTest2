/**
 * Typed environment variable validation using Zod.
 *
 * - Server-side vars (non-NEXT_PUBLIC_*): validated at runtime on the server.
 * - Client-side vars (NEXT_PUBLIC_*): baked into the bundle at build time;
 *   validated on both server and client.
 *
 * Import this module instead of accessing `process.env` directly.
 */

import { z } from "zod";

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const clientSchema = z.object({
  /** Base URL of the FastAPI backend reachable by the browser. */
  NEXT_PUBLIC_API_BASE_URL: z.string().url().default("http://localhost:8000"),
  /** Supabase project URL. */
  NEXT_PUBLIC_SUPABASE_URL: z.string().url(),
  /** Supabase anonymous (public) key. */
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(1),
});

const serverSchema = clientSchema.extend({
  /** Application environment. */
  APP_ENV: z.enum(["development", "production", "test"]).default("development"),
  /** Node.js runtime environment (set automatically by Next.js). */
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
});

// ---------------------------------------------------------------------------
// Validation helper
// ---------------------------------------------------------------------------

function parseEnv<T extends z.ZodTypeAny>(schema: T): z.infer<T> {
  const parsed = schema.safeParse(process.env);
  if (!parsed.success) {
    const formatted = parsed.error.format();
    console.error("❌  Invalid environment variables:", JSON.stringify(formatted, null, 2));
    throw new Error("Invalid environment configuration. Check the server logs.");
  }
  return parsed.data as z.infer<T>;
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

/**
 * Validated client-side environment variables.
 * Safe to import in both Server and Client Components.
 */
export const clientEnv = parseEnv(clientSchema);

/**
 * Validated server-side environment variables (superset of clientEnv).
 * Only import this in server-only modules (Server Components, API routes, etc.)
 * — it will throw if accidentally bundled into the client because NEXT_PUBLIC
 * vars are the only ones present in the browser bundle.
 */
export const serverEnv = parseEnv(serverSchema);

// Re-export individual vars for convenience
export const {
  NEXT_PUBLIC_API_BASE_URL,
  NEXT_PUBLIC_SUPABASE_URL,
  NEXT_PUBLIC_SUPABASE_ANON_KEY,
} = clientEnv;
