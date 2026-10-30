import { Center, Loader } from "@mantine/core";
import type { Metadata } from "next";
import { Suspense } from "react";

import { PayrollRunView } from "@/components/payroll-run";

export const metadata: Metadata = { title: "Payroll run" };

export default function PayrollRunPage() {
  return (
    <Suspense fallback={<Center p="xl"><Loader /></Center>}>
      <PayrollRunView />
    </Suspense>
  );
}
