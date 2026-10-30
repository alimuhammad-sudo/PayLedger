import { Center, Loader } from "@mantine/core";
import type { Metadata } from "next";
import { Suspense } from "react";

import { Overview } from "@/components/overview";

export const metadata: Metadata = { title: "Overview" };

export default function OverviewPage() {
  return (
    <Suspense fallback={<Center p="xl"><Loader /></Center>}>
      <Overview />
    </Suspense>
  );
}
