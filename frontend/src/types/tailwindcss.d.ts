/**
 * Minimal type shim for the `tailwindcss` package.
 *
 * This shim exists because tailwindcss ships its own types in `tailwindcss/types/config.d.ts`
 * but the package may not be installed in the current environment. The shim provides
 * just enough typing for `tailwind.config.ts` to type-check cleanly.
 *
 * Remove this file if/when `tailwindcss` is fully installed in node_modules.
 */

declare module "tailwindcss" {
  // Re-export the Config type used in tailwind.config.ts
  export type { Config } from "tailwindcss/types/config";
}

declare module "tailwindcss/types/config" {
  // Minimal Config interface — mirrors the real tailwindcss Config type.
  export interface Config {
    content: string[] | { files: string[]; transform?: Record<string, (content: string) => string> };
    darkMode?: "class" | "media" | false;
    theme?: {
      extend?: Record<string, unknown>;
      [key: string]: unknown;
    };
    plugins?: unknown[];
    [key: string]: unknown;
  }
}
