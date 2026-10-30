import { Center, Loader } from "@mantine/core";
import type { Metadata } from "next";
import { Suspense } from "react";

import { Person } from "@/components/person";

export const metadata: Metadata = { title: "Person" };

export default function PersonPage() {
  return (
    <Suspense fallback={<Center p="xl"><Loader /></Center>}>
      <Person />
    </Suspense>
  );
}
