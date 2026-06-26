/**
 * Tests for the pure role helpers: extraction from metadata + capability checks.
 */

import {
  canAcknowledgeIncidents,
  canManageFeeds,
  canManageUsers,
  canTriggerCalls,
  isRole,
  roleFromMetadata,
} from "./roles";

describe("isRole", () => {
  it("accepts the three known roles", () => {
    expect(isRole("admin")).toBe(true);
    expect(isRole("operator")).toBe(true);
    expect(isRole("viewer")).toBe(true);
  });

  it("rejects unknown or non-string values", () => {
    expect(isRole("superuser")).toBe(false);
    expect(isRole("")).toBe(false);
    expect(isRole(null)).toBe(false);
    expect(isRole(42)).toBe(false);
  });
});

describe("roleFromMetadata", () => {
  it("reads the first valid role from the roles array", () => {
    expect(roleFromMetadata({ roles: ["admin"] })).toBe("admin");
    expect(roleFromMetadata({ roles: ["authenticated", "operator"] })).toBe("operator");
  });

  it("falls back to the scalar role", () => {
    expect(roleFromMetadata({ role: "viewer" })).toBe("viewer");
  });

  it("prefers a valid roles[] entry over the scalar role", () => {
    expect(roleFromMetadata({ roles: ["admin"], role: "viewer" })).toBe("admin");
  });

  it("returns null when no application role is present", () => {
    expect(roleFromMetadata({})).toBeNull();
    expect(roleFromMetadata(null)).toBeNull();
    expect(roleFromMetadata({ roles: ["authenticated"] })).toBeNull();
  });
});

describe("capability checks", () => {
  it("only admins manage feeds, trigger calls, and manage users", () => {
    expect(canManageFeeds("admin")).toBe(true);
    expect(canManageFeeds("operator")).toBe(false);
    expect(canTriggerCalls("admin")).toBe(true);
    expect(canTriggerCalls("viewer")).toBe(false);
    expect(canManageUsers("admin")).toBe(true);
    expect(canManageUsers("operator")).toBe(false);
  });

  it("admins and operators acknowledge incidents; viewers cannot", () => {
    expect(canAcknowledgeIncidents("admin")).toBe(true);
    expect(canAcknowledgeIncidents("operator")).toBe(true);
    expect(canAcknowledgeIncidents("viewer")).toBe(false);
    expect(canAcknowledgeIncidents(null)).toBe(false);
  });
});
