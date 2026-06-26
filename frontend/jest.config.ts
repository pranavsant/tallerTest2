import type { Config } from "jest";

/**
 * Jest configuration for the Overseer AI frontend.
 *
 * Uses ts-jest to run TypeScript tests directly and maps the `@/*` path alias
 * (mirroring tsconfig.json) so test files can import application modules the
 * same way components do.
 */
const config: Config = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  roots: ["<rootDir>/src"],
  testMatch: ["**/*.test.ts", "**/*.test.tsx"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  // Keep env-dependent modules happy when imported transitively in tests.
  setupFiles: ["<rootDir>/jest.setup.ts"],
  clearMocks: true,
};

export default config;
