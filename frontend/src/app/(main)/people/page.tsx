import { Center, Loader } from "@mantine/core";
import type { Metadata } from "next";
import { Suspense } from "react";

import { PeopleDirectory } from "@/components/people-directory";

export const metadata: Metadata = { title: "People" };

export default function PeoplePage() {
  return (
    <Suspense fallback={<Center p="xl"><Loader /></Center>}>
      <PeopleDirectory />
    </Suspense>
  );
}
