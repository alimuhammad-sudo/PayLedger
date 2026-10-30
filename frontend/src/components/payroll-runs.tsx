"use client";

import { Alert, Anchor, Button, Card, Group, Select, Skeleton, Stack, Table, Text, Title } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { IconPlayerPlay } from "@tabler/icons-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, ApiError } from "@/lib/api";
import { money } from "@/lib/money";
import { monthName, runnableMonths } from "@/lib/months";
import { useMe, usePayrollRuns } from "@/lib/queries";
import type { PayrollRunDetail } from "@/lib/types";

export function PayrollRuns() {
  const isAdmin = useMe().data?.role === "admin";
  const runs = usePayrollRuns();
  const router = useRouter();
  const qc = useQueryClient();
  const [months] = useState(() => runnableMonths(new Date()));
  const [pick, setPick] = useState(`${months[0].year}-${months[0].month}`);
  const done = new Set((runs.data ?? []).map((r) => `${r.year}-${r.month}`));
  const [year, month] = pick.split("-").map(Number);

  const create = useMutation({
    mutationFn: () => api<PayrollRunDetail>("/payroll/runs", { method: "POST", body: { year, month } }),
    onSuccess: (run) => {
      qc.invalidateQueries({ queryKey: ["payroll"] });
      notifications.show({ color: "teal", message: `Payroll for ${monthName(year, month)} is ready` });
      router.push(`/payroll/${run.id}`);
    },
    onError: (err) => notifications.show({
      color: "red",
      message: err instanceof ApiError ? Object.values(err.fields)[0] ?? err.message : "Failed",
    }),
  });

  return (
    <Stack gap="lg">
      <div>
        <Title order={2}>Payroll</Title>
        <Text c="dimmed" size="sm">
          A payroll run works out what everyone is owed for a month and keeps it as a record.
          It does not send any payments.
        </Text>
      </div>

      {isAdmin && (
        <Card withBorder maw={640}>
          <Text fw={600}>Run payroll</Text>
          <Text size="sm" c="dimmed" mb="sm">
            Everyone employed during the month is included. People who joined or left part-way
            are paid for the days they worked. Later salary changes never alter a finished run.
          </Text>
          <Group>
            <Select aria-label="Month" w={200} value={pick} allowDeselect={false}
              onChange={(v) => v && setPick(v)}
              data={months.map((m) => ({
                value: `${m.year}-${m.month}`,
                label: m.label + (done.has(`${m.year}-${m.month}`) ? " (done)" : ""),
              }))} />
            <Button leftSection={<IconPlayerPlay size={16} />} loading={create.isPending}
              disabled={done.has(pick)} onClick={() => create.mutate()}>
              Run {monthName(year, month)}
            </Button>
          </Group>
        </Card>
      )}

      {runs.isError ? (
        <Alert color="red">Could not load payroll runs. {runs.error.message}</Alert>
      ) : !runs.data ? (
        <Skeleton h={200} />
      ) : runs.data.length === 0 ? (
        <Text c="dimmed">No payroll has been run yet.</Text>
      ) : (
        <Table highlightOnHover maw={760}>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Month</Table.Th>
              <Table.Th ta="right">People paid</Table.Th>
              <Table.Th ta="right">Total (USD)</Table.Th>
              <Table.Th>Run on</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {runs.data.map((r) => (
              <Table.Tr key={r.id}>
                <Table.Td>
                  <Anchor component={Link} href={`/payroll/${r.id}`}>{monthName(r.year, r.month)}</Anchor>
                </Table.Td>
                <Table.Td ta="right" className="tabular">{r.headcount.toLocaleString("en-US")}</Table.Td>
                <Table.Td ta="right" className="tabular">{money(r.total_usd_cents, "USD")}</Table.Td>
                <Table.Td>{new Date(r.created_at).toLocaleDateString("en-GB")}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Stack>
  );
}
