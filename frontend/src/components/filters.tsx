"use client";

import { Select } from "@mantine/core";

import { useReference } from "@/lib/queries";

type Value = { country: string; department: string; level: string };

export function OrgFilters({ value, onChange }: {
  value: Value;
  onChange: (v: Partial<Value>) => void;
}) {
  const ref = useReference().data;
  return (
    <>
      <Select aria-label="Country" placeholder="All countries" clearable w={180}
        data={ref?.countries.map((c) => ({ value: c.code, label: c.name })) ?? []}
        value={value.country || null} onChange={(v) => onChange({ country: v ?? "" })} />
      <Select aria-label="Department" placeholder="All departments" clearable w={190}
        data={ref?.departments ?? []}
        value={value.department || null} onChange={(v) => onChange({ department: v ?? "" })} />
      <Select aria-label="Level" placeholder="All levels" clearable w={150}
        data={ref?.levels ?? []}
        value={value.level || null} onChange={(v) => onChange({ level: v ?? "" })} />
    </>
  );
}
