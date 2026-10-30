"use client";

import {
  Alert,
  Anchor,
  Badge,
  Card,
  Center,
  Group,
  Loader,
  Pagination,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { useDebouncedValue } from "@mantine/hooks";
import { IconArrowLeft, IconSearch } from "@tabler/icons-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { money } from "@/lib/money";
import { monthName } from "@/lib/months";
import { usePayrollRun, usePayslips } from "@/lib/queries";

const SIZE = 50;

export function PayrollRunView() {
  const { id } = useParams<{ id: string }>();
  const run = usePayrollRun(id);
  const [country, setCountry] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [debounced] = useDebouncedValue(search, 300);
  const [page, setPage] = useState(1);
  const slips = usePayslips(id, { country: country ?? undefined, search: debounced, page, size: SIZE });

  if (run.isError) return <Alert color="red" title="Could not open this run">{run.error.message}</Alert>;
  if (!run.data) return <Center p="xl"><Loader /></Center>;
  const r = run.data;

  return (
    <Stack gap="lg">
      <Anchor component={Link} href="/payroll" size="sm">
        <Group gap={4}><IconArrowLeft size={14} /> Payroll</Group>
      </Anchor>
      <div>
        <Title order={2}>Payroll for {monthName(r.year, r.month)}</Title>
        <Text c="dimmed" size="sm">Fixed when it was run. Amounts are for the month, in each person&apos;s pay currency.</Text>
      </div>

      <SimpleGrid cols={{ base: 1, sm: 3 }} maw={760}>
        <Stat label="People paid" value={r.headcount.toLocaleString("en-US")} />
        <Stat label="Total in USD" value={money(r.total_usd_cents, "USD")} />
        <Stat label="Countries" value={String(r.countries.length)} />
      </SimpleGrid>

      <Card withBorder>
        <Text fw={600} mb="sm">By country</Text>
        <Table>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Country</Table.Th>
              <Table.Th ta="right">People</Table.Th>
              <Table.Th ta="right">Local total</Table.Th>
              <Table.Th ta="right">USD total</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {r.countries.map((c) => (
              <Table.Tr key={c.country}>
                <Table.Td>{c.country_name}</Table.Td>
                <Table.Td ta="right" className="tabular">{c.headcount.toLocaleString("en-US")}</Table.Td>
                <Table.Td ta="right" className="tabular">{money(c.gross_minor, c.currency)}</Table.Td>
                <Table.Td ta="right" className="tabular">{money(c.gross_usd_cents, "USD")}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Card>

      <Card withBorder>
        <Group justify="space-between" mb="sm">
          <Text fw={600}>Payslips</Text>
          <Group gap="sm">
            <TextInput aria-label="Search payslips" placeholder="Name or staff ID" w={220}
              leftSection={<IconSearch size={16} />} value={search}
              onChange={(e) => { setSearch(e.currentTarget.value); setPage(1); }} />
            <Select aria-label="Country" placeholder="All countries" clearable w={180}
              data={r.countries.map((c) => ({ value: c.country, label: c.country_name }))}
              value={country} onChange={(v) => { setCountry(v); setPage(1); }} />
          </Group>
        </Group>
        {!slips.data ? <Center p="md"><Loader size="sm" /></Center> : (
          <div style={{ opacity: slips.isPlaceholderData ? 0.6 : 1 }}>
            <Table.ScrollContainer minWidth={760}>
              <Table>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Person</Table.Th>
                    <Table.Th ta="right">Annual salary</Table.Th>
                    <Table.Th ta="right">Days paid</Table.Th>
                    <Table.Th ta="right">This month</Table.Th>
                    <Table.Th ta="right">In USD</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {slips.data.items.map((s) => (
                    <Table.Tr key={s.employee_id}>
                      <Table.Td>
                        <Anchor component={Link} href={`/people/${s.employee_id}`} size="sm">{s.full_name}</Anchor>
                        <Text span size="xs" c="dimmed" ff="monospace" ml="xs">{s.staff_id}</Text>
                      </Table.Td>
                      <Table.Td ta="right" className="tabular">{money(s.annual_salary_minor, s.currency)}</Table.Td>
                      <Table.Td ta="right" className="tabular">
                        {s.days_paid < s.days_in_month ? (
                          <Badge variant="light" color="orange">{s.days_paid} of {s.days_in_month}</Badge>
                        ) : `${s.days_paid}`}
                      </Table.Td>
                      <Table.Td ta="right" className="tabular">{money(s.gross_minor, s.currency, true)}</Table.Td>
                      <Table.Td ta="right" className="tabular">{money(s.gross_usd_cents, "USD", true)}</Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
            <Group justify="space-between" mt="md">
              <Text size="sm" c="dimmed">{slips.data.total.toLocaleString("en-US")} payslips</Text>
              <Pagination total={Math.max(1, Math.ceil(slips.data.total / SIZE))} value={page}
                onChange={setPage} />
            </Group>
          </div>
        )}
      </Card>
    </Stack>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Paper withBorder p="md">
      <Text size="xs" tt="uppercase" fw={600} c="dimmed">{label}</Text>
      <Text fz={22} fw={700} className="tabular">{value}</Text>
    </Paper>
  );
}
