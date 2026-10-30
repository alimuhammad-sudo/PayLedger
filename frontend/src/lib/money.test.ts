import { describe, expect, it } from "vitest";

import { change, compact, minorDigits, money, toMajor, usdShort } from "@/lib/money";

describe("money", () => {
  it("knows yen has no minor unit", () => {
    expect(minorDigits("JPY")).toBe(0);
    expect(minorDigits("GBP")).toBe(2);
    expect(toMajor(9_000_000, "JPY")).toBe(9_000_000);
    expect(toMajor(8_500_050, "GBP")).toBe(85_000.5);
  });

  it("shows whole units unless cents are asked for", () => {
    expect(money(8_500_050, "GBP")).toBe("£85,001");
    expect(money(8_500_050, "GBP", true)).toBe("£85,000.50");
    expect(money(9_000_000, "JPY", true)).toBe("¥9,000,000");
    expect(money(null, "USD")).toBe("-");
  });

  it("shortens USD cents for tiles and axes", () => {
    expect(usdShort(67_047_695_500)).toBe("$670.5M");
    expect(usdShort(undefined)).toBe("-");
    expect(compact(31_600_000, "CAD")).toBe("CA$316K");
  });

  it("describes a change as a signed percentage", () => {
    expect(change(100, 108)).toBe("+8.0%");
    expect(change(100, 95)).toBe("-5.0%");
    expect(change(null, 100)).toBe("");
  });
});
