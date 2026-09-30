// Display helpers. Amounts arrive from the API as decimal strings (NFR-01); the UI never uses floats on them.
// Percentages are converted to integer basis points for the only client-side arithmetic (template row sums).

const DECIMAL = /^(-?)(\d+)(?:\.(\d{1,2}))?$/;

function groupIndian(digits) {
  if (digits.length <= 3) return digits;
  const last3 = digits.slice(-3);
  const rest = digits.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ",");
  return `${rest},${last3}`;
}

export function formatInr(value) {
  if (value === null || value === undefined || value === "") return "—";
  const [whole, fraction = "00"] = String(value).split(".");
  const negative = whole.startsWith("-");
  const digits = negative ? whole.slice(1) : whole;
  return `${negative ? "-" : ""}₹${groupIndian(digits)}.${fraction.padEnd(2, "0")}`;
}

export function formatPct(value) {
  return value === null || value === undefined ? "—" : `${value}%`;
}

export function formatUnits(value) {
  return value === null || value === undefined ? "—" : String(value);
}

export function pctToBp(text) {
  const match = DECIMAL.exec(String(text).trim());
  if (!match) return null;
  const [, sign, whole, fraction = ""] = match;
  const bp = Number.parseInt(whole, 10) * 100 + Number.parseInt(fraction.padEnd(2, "0"), 10);
  return sign === "-" ? -bp : bp;
}

export function bpToPct(bp) {
  const sign = bp < 0 ? "-" : "";
  const abs = Math.abs(bp);
  return `${sign}${Math.trunc(abs / 100)}.${String(abs % 100).padStart(2, "0")}`;
}

export function sumPct(values) {
  let total = 0;
  for (const value of values) {
    const bp = pctToBp(value);
    if (bp === null) return null;
    total += bp;
  }
  return bpToPct(total);
}

export function titleCase(code) {
  return code ? code.charAt(0) + code.slice(1).toLowerCase().replaceAll("_", " ") : "";
}

// Clamp a percentage string to 100.00 for progress-bar widths (compares integer basis points).
export function capPct(value) {
  const bp = pctToBp(value);
  if (bp === null || bp < 0) return "0.00";
  return bp > 10000 ? "100.00" : bpToPct(bp);
}
