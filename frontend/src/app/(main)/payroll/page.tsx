import type { Metadata } from "next";

import { PayrollRuns } from "@/components/payroll-runs";

export const metadata: Metadata = { title: "Payroll" };

export default function PayrollPage() {
  return <PayrollRuns />;
}
