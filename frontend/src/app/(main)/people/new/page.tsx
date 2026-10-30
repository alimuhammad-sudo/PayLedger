import type { Metadata } from "next";

import { NewPerson } from "@/components/new-person";

export const metadata: Metadata = { title: "Add person" };

export default function NewPersonPage() {
  return <NewPerson />;
}
