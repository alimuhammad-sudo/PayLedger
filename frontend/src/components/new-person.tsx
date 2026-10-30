"use client";

import { Alert, Button, Card, Group, Select, SimpleGrid, Stack, Text, TextInput, Title } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { todayIso } from "@/components/person-modals";
import { api, ApiError } from "@/lib/api";
import { useEmployeeMutation, useMe, useReference } from "@/lib/queries";
import type { EmployeeDetail } from "@/lib/types";

const EMPTY = {
  full_name: "", email: "", job_title: "", department: "", level: "",
  country: "", start_date: "", salary: "",
};

export function NewPerson() {
  const me = useMe().data;
  const ref = useReference().data;
  const router = useRouter();
  const [form, setForm] = useState(EMPTY);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const create = useEmployeeMutation((body: typeof EMPTY) =>
    api<EmployeeDetail>("/employees", { method: "POST", body }));

  if (me && me.role !== "admin") {
    return <Alert title="View only">Only HR admins can add people.</Alert>;
  }

  const currency = ref?.countries.find((c) => c.code === form.country)?.currency;
  const set = (k: keyof typeof EMPTY) => (v: string | null) => setForm((f) => ({ ...f, [k]: v ?? "" }));
  const text = (k: keyof typeof EMPTY, label: string, extra: object = {}) => (
    <TextInput label={label} value={form[k]} onChange={(e) => set(k)(e.currentTarget.value)}
      error={fields[k]} {...extra} />
  );

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setFields({});
    setMessage(null);
    try {
      const created = await create.mutateAsync(form);
      notifications.show({ color: "teal", message: `${created.full_name} added` });
      router.push(`/people/${created.id}`);
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fields).length) setFields(err.fields);
      else setMessage(err instanceof Error ? err.message : "Something went wrong.");
    }
  }

  return (
    <Stack maw={760}>
      <div>
        <Title order={2}>Add person</Title>
        <Text c="dimmed" size="sm">Their starting salary becomes the first entry in their history.</Text>
      </div>
      <Card withBorder component="form" onSubmit={submit} noValidate>
        <Stack>
          {message && <Alert color="red">{message}</Alert>}
          <SimpleGrid cols={{ base: 1, sm: 2 }}>
            {text("full_name", "Full name")}
            {text("email", "Work email", { type: "email" })}
            {text("job_title", "Job title")}
            <Select label="Department" data={ref?.departments ?? []} value={form.department || null}
              onChange={set("department")} error={fields.department} />
            <Select label="Level" data={ref?.levels ?? []} value={form.level || null}
              onChange={set("level")} error={fields.level} />
            <Select label="Country" searchable value={form.country || null} onChange={set("country")}
              data={ref?.countries.map((c) => ({ value: c.code, label: c.name })) ?? []}
              error={fields.country} />
            {text("start_date", "Start date", { type: "date", max: todayIso() })}
            {text("salary", `Annual salary${currency ? ` (${currency})` : ""}`, {
              inputMode: "decimal", description: "Paid in the country's currency",
            })}
          </SimpleGrid>
          <Group justify="flex-end">
            <Button variant="default" onClick={() => router.back()}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Add person</Button>
          </Group>
        </Stack>
      </Card>
    </Stack>
  );
}
