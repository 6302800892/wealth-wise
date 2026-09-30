// NFR-01 on the client: amounts arrive as decimal strings and are formatted without floating point.
import { describe, expect, it } from "vitest";
import { bpToPct, capPct, formatInr, formatPct, pctToBp, sumPct } from "../../src/lib/format.js";

describe("formatInr", () => {
  it("uses Indian digit grouping", () => {
    expect(formatInr("1000000.00")).toBe("₹10,00,000.00");
    expect(formatInr("600000.00")).toBe("₹6,00,000.00");
    expect(formatInr("999.50")).toBe("₹999.50");
  });

  it("handles negatives, zero and missing values", () => {
    expect(formatInr("-12345.60")).toBe("-₹12,345.60");
    expect(formatInr("0.00")).toBe("₹0.00");
    expect(formatInr(null)).toBe("—");
  });
});

describe("fixed-point percentage helpers (AC-02 live row sums)", () => {
  it("converts percentage strings to integer basis points and back", () => {
    expect(pctToBp("50.00")).toBe(5000);
    expect(pctToBp("5.5")).toBe(550);
    expect(pctToBp("0.07")).toBe(7);
    expect(bpToPct(10000)).toBe("100.00");
    expect(bpToPct(7)).toBe("0.07");
  });

  it("sums a template row exactly (no 0.1 + 0.2 drift)", () => {
    expect(sumPct(["60.00", "27.00", "10.00", "3.00"])).toBe("100.00");
    expect(sumPct(["33.33", "33.33", "33.34"])).toBe("100.00");
    expect(sumPct(["0.10", "0.20"])).toBe("0.30");
  });

  it("rejects malformed input", () => {
    expect(pctToBp("abc")).toBeNull();
    expect(pctToBp("1.234")).toBeNull();
    expect(sumPct(["50.00", "x"])).toBeNull();
  });

  it("formats percentages for display", () => {
    expect(formatPct("10.00")).toBe("10.00%");
    expect(formatPct(null)).toBe("—");
  });
});

describe("capPct", () => {
  it("clamps progress widths without floating point", () => {
    expect(capPct("25.30")).toBe("25.30");
    expect(capPct("150.00")).toBe("100.00");
    expect(capPct("-1.00")).toBe("0.00");
    expect(capPct(null)).toBe("0.00");
  });
});
