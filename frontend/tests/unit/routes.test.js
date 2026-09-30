// Hash routing and role-based navigation (NFR-04 separation mirrored in the UI).
import { describe, expect, it } from "vitest";
import { homeFor, navFor, parseHash } from "../../src/config/routes.js";

describe("parseHash", () => {
  it("matches static routes", () => {
    expect(parseHash("#/holdings")).toEqual({ name: "holdings", params: {} });
    expect(parseHash("#/admin/templates")).toEqual({ name: "admin-templates", params: {} });
  });

  it("extracts route parameters", () => {
    expect(parseHash("#/advisor/customers/abc-123")).toEqual({
      name: "advisor-customer",
      params: { id: "abc-123" },
    });
  });

  it("falls back to login for unknown or empty hashes", () => {
    expect(parseHash("")).toEqual({ name: "login", params: {} });
    expect(parseHash("#/nope")).toEqual({ name: "login", params: {} });
  });
});

describe("role navigation", () => {
  it("gives each role its own home and menu", () => {
    expect(homeFor("CUSTOMER")).toBe("#/dashboard");
    expect(homeFor("ADVISOR")).toBe("#/advisor/customers");
    expect(homeFor("ADMIN")).toBe("#/admin/templates");
    expect(navFor("CUSTOMER").map((item) => item.name)).toContain("rebalancing");
    expect(navFor("ADVISOR").every((item) => item.role === "ADVISOR")).toBe(true);
  });
});
