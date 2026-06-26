/**
 * Jest global setup.
 *
 * Provides the environment variables required by `@/env` so that modules which
 * import it transitively (e.g. `@/lib/api`) don't throw during tests. Tests
 * that exercise the transport layer directly should target `@/lib/http`, which
 * has no env dependency and accepts an injected `fetch`.
 */
process.env.NEXT_PUBLIC_API_BASE_URL ||= "http://localhost:8000";
process.env.NEXT_PUBLIC_SUPABASE_URL ||= "http://localhost:54321";
process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||= "test-anon-key";
