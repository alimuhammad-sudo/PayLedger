const NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export const monthName = (year: number, month: number) => `${NAMES[month - 1]} ${year}`;

/** Months payroll can be run for: this month back to `back` months ago (API rule: no
 * month that has not started). */
export function runnableMonths(today: Date, back = 18) {
  const out: { year: number; month: number; label: string }[] = [];
  let y = today.getFullYear();
  let m = today.getMonth() + 1;
  for (let i = 0; i <= back; i++) {
    out.push({ year: y, month: m, label: monthName(y, m) });
    m -= 1;
    if (m === 0) {
      m = 12;
      y -= 1;
    }
  }
  return out;
}
