"use client";

import { Alert, Button, Group, Modal, Select, Stack, Text, TextInput, Textarea } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useState } from "react";

import { api, ApiError } from "@/lib/api";
import { change, minorDigits } from "@/lib/money";
import { useEmployeeMutation, useReference } from "@/lib/queries";
import type { EmployeeDetail } from "@/lib/types";

export const todayIso = () => new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD, local

type Props = { person: EmployeeDetail; onClose: () => void };

/** Shared form state: fields, per-field errors from the API, and a general message. */
function useFormErrors() {
  const [fields, setFields] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string | null>(null);
  const capture = (err: unknown) => {
    if (err instanceof ApiError) {
      setFields(err.fields);
      setMessage(Object.keys(err.fields).length ? null : err.message);
    } else {
      setMessage("Something went wrong.");
    }
  };
  const reset = () => { setFields({}); setMessage(null); };
  return { fields, message, capture, reset };
}

export function SalaryChangeModal({ person, onClose }: Props) {
  const reasons = useReference().data?.change_reasons ?? [];
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(todayIso());
  const [reason, setReason] = useState<string | null>("Annual review");
  const [note, setNote] = useState("");
  const errors = useFormErrors();
  const save = useEmployeeMutation((body: object) =>
    api<EmployeeDetail>(`/employees/${person.id}/salary-changes`, { method: "POST", body }));

  const parsed = Number(amount.replace(/,/g, ""));
  const preview = amount && Number.isFinite(parsed)
    ? change(person.salary_minor, Math.round(parsed * 10 ** minorDigits(person.currency)))
    : "";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    errors.reset();
    try {
      await save.mutateAsync({ new_salary: amount, effective_on: date, reason, note: note || null });
      notifications.show({ color: "teal", message: `Salary updated for ${person.full_name}` });
      onClose();
    } catch (err) {
      errors.capture(err);
    }
  }

  return (
    <Modal opened onClose={onClose} title="Change salary">
      <form onSubmit={submit}>
        <Stack>
          {errors.message && <Alert color="red">{errors.message}</Alert>}
          <TextInput label={`New annual salary (${person.currency})`} inputMode="decimal" data-autofocus
            value={amount} onChange={(e) => setAmount(e.currentTarget.value)}
            description={preview ? `${preview} on today's salary` : undefined}
            error={errors.fields.new_salary} />
          <TextInput label="Takes effect on" type="date" value={date} max={todayIso()}
            onChange={(e) => setDate(e.currentTarget.value)} error={errors.fields.effective_on} />
          <Select label="Reason" data={reasons} value={reason} onChange={setReason}
            error={errors.fields.reason} allowDeselect={false} />
          <Textarea label="Note" description={reason === "Other" ? "Required for Other" : "Optional"}
            value={note} onChange={(e) => setNote(e.currentTarget.value)} error={errors.fields.note} />
          <Group justify="flex-end">
            <Button variant="default" onClick={onClose}>Cancel</Button>
            <Button type="submit" loading={save.isPending}>Save change</Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

export function EditDetailsModal({ person, onClose }: Props) {
  const ref = useReference().data;
  const [form, setForm] = useState({
    full_name: person.full_name, email: person.email, job_title: person.job_title,
    department: person.department, level: person.level,
  });
  const errors = useFormErrors();
  const save = useEmployeeMutation((body: object) =>
    api<EmployeeDetail>(`/employees/${person.id}`, { method: "PATCH", body }));
  const set = (k: keyof typeof form) => (v: string | null) => setForm((f) => ({ ...f, [k]: v ?? "" }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    errors.reset();
    try {
      await save.mutateAsync(form);
      notifications.show({ color: "teal", message: "Details saved" });
      onClose();
    } catch (err) {
      errors.capture(err);
    }
  }

  return (
    <Modal opened onClose={onClose} title="Edit details">
      <form onSubmit={submit}>
        <Stack>
          {errors.message && <Alert color="red">{errors.message}</Alert>}
          <TextInput label="Full name" value={form.full_name}
            onChange={(e) => set("full_name")(e.currentTarget.value)} error={errors.fields.full_name} />
          <TextInput label="Work email" value={form.email}
            onChange={(e) => set("email")(e.currentTarget.value)} error={errors.fields.email} />
          <TextInput label="Job title" value={form.job_title}
            onChange={(e) => set("job_title")(e.currentTarget.value)} error={errors.fields.job_title} />
          <Select label="Department" data={ref?.departments ?? []} value={form.department}
            onChange={set("department")} allowDeselect={false} />
          <Select label="Level" data={ref?.levels ?? []} value={form.level}
            onChange={set("level")} allowDeselect={false} />
          <Text size="xs" c="dimmed">
            Country and pay currency are fixed after hiring. Pay changes go through Change salary,
            so they are kept in the history.
          </Text>
          <Group justify="flex-end">
            <Button variant="default" onClick={onClose}>Cancel</Button>
            <Button type="submit" loading={save.isPending}>Save</Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

export function LeavingDateModal({ person, onClose }: Props) {
  const [date, setDate] = useState(person.end_date ?? todayIso());
  const errors = useFormErrors();
  const setIt = useEmployeeMutation((end_date: string) =>
    api<EmployeeDetail>(`/employees/${person.id}/leaving-date`, { method: "PUT", body: { end_date } }));
  const clear = useEmployeeMutation<void>(() =>
    api<EmployeeDetail>(`/employees/${person.id}/leaving-date`, { method: "DELETE" }));

  async function run(action: () => Promise<unknown>, message: string) {
    errors.reset();
    try {
      await action();
      notifications.show({ color: "teal", message });
      onClose();
    } catch (err) {
      errors.capture(err);
    }
  }

  return (
    <Modal opened onClose={onClose} title={`Leaving date for ${person.full_name}`}>
      <Stack>
        {errors.message && <Alert color="red">{errors.message}</Alert>}
        <Text size="sm" c="dimmed">
          They stop counting towards headcount and payroll after this day. Their record and
          history are kept.
        </Text>
        <TextInput label="Last day" type="date" value={date}
          onChange={(e) => setDate(e.currentTarget.value)} error={errors.fields.end_date} />
        <Group justify="space-between">
          {person.end_date ? (
            <Button variant="subtle" color="gray" loading={clear.isPending}
              onClick={() => run(() => clear.mutateAsync(), "Leaving date removed")}>
              Remove leaving date
            </Button>
          ) : <span />}
          <Group>
            <Button variant="default" onClick={onClose}>Cancel</Button>
            <Button color="orange" loading={setIt.isPending}
              onClick={() => run(() => setIt.mutateAsync(date), "Leaving date saved")}>
              Save leaving date
            </Button>
          </Group>
        </Group>
      </Stack>
    </Modal>
  );
}
