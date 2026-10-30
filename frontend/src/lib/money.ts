// The API sends money as integers of the smallest unit (cents, pence, whole yen).

const ZERO_DECIMAL = new Set(["JPY"]);

export const minorDigits = (currency: string) => (ZERO_DECIMAL.has(currency) ? 0 : 2);

export const toMajor = (minor: number, currency: string) => minor / 10 ** minorDigits(currency);

/** "£85,000" - whole units, which is how salaries are discussed. */
export function money(minor: number | null | undefined, currency: string, withCents = false) {
  if (minor === null || minor === undefined) return "-";
  const digits = withCents ? minorDigits(currency) : 0;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(toMajor(minor, currency));
}

/** "$1.2M" for tiles and chart axes. Input is US cents. */
export function usdShort(cents: number | null | undefined) {
  if (cents === null || cents === undefined) return "-";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(cents / 100);
}

/** Percentage change, e.g. "+8.0%". Empty when there is nothing to compare with. */
export function change(oldMinor: number | null, newMinor: number) {
  if (!oldMinor) return "";
  const pct = ((newMinor - oldMinor) / oldMinor) * 100;
  return `${pct > 0 ? "+" : ""}${pct.toFixed(1)}%`;
}

/** "CA$316K" for chart axes, in any currency. Input is minor units. */
export function compact(minor: number, currency: string) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(toMajor(minor, currency));
}
