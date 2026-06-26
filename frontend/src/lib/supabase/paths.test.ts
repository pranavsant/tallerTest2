/**
 * Tests for the pure auth path helpers used by the middleware and login flow.
 */

import { isPublicPath, safeRedirect } from "./paths";

describe("isPublicPath", () => {
  it("treats /login and /auth (and their subpaths) as public", () => {
    expect(isPublicPath("/login")).toBe(true);
    expect(isPublicPath("/auth")).toBe(true);
    expect(isPublicPath("/auth/callback")).toBe(true);
  });

  it("treats app routes as protected", () => {
    expect(isPublicPath("/")).toBe(false);
    expect(isPublicPath("/dashboard")).toBe(false);
    expect(isPublicPath("/dashboard/agents")).toBe(false);
  });

  it("does not match paths that merely share a prefix", () => {
    // "/loginx" should not be considered the public "/login" route.
    expect(isPublicPath("/loginx")).toBe(false);
    expect(isPublicPath("/authority")).toBe(false);
  });
});

describe("safeRedirect", () => {
  it("returns internal absolute paths unchanged", () => {
    expect(safeRedirect("/dashboard/agents")).toBe("/dashboard/agents");
    expect(safeRedirect("/settings")).toBe("/settings");
  });

  it("falls back to the dashboard for missing or empty targets", () => {
    expect(safeRedirect(undefined)).toBe("/dashboard");
    expect(safeRedirect(null)).toBe("/dashboard");
    expect(safeRedirect("")).toBe("/dashboard");
  });

  it("rejects external and protocol-relative URLs (open-redirect guard)", () => {
    expect(safeRedirect("https://evil.example.com")).toBe("/dashboard");
    expect(safeRedirect("//evil.example.com")).toBe("/dashboard");
    expect(safeRedirect("javascript:alert(1)")).toBe("/dashboard");
  });

  it("honors a custom fallback", () => {
    expect(safeRedirect(null, "/login")).toBe("/login");
  });
});
