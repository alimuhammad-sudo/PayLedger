"use client";

import { BarChart } from "@mantine/charts";
import {
  Alert,
  Button,
  Card,
  Group,
  Paper,
  Progress,
  SegmentedControl,
  SimpleGrid,
  Skeleton,
  Stack,
  Table,
  Text,
  Title,
  Tooltip,
} from "@mantine/core";

import { OrgFilters } from "@/components/filters";
import { money, usdShort } from "@/lib/money";
import { useBreakdown, useDistribution, useSummary } from "@/lib/queries";
import type { Group as PayGroup } from "@/lib/types";
import { useUrlState } from "@/lib/url-state";

const DEFAULTS = { country: "", department: "", level: "", by: "country" };

export function Overview() {
  const [state, set] = useUrlState(DEFAULTS);
  const filters = { country: state.country, department: state.department, level: state.level };
  const summary = useSummary(filters);
  const breakdown = useBreakdown(state.by, filters);
  const bands = useDistribution(filters);
  const s = summary.data;
  const filtered = Object.values(filters).some(Boolean);

  return (
    <Stack gap="lg">
      <div>
        <Title order={2}>How ACME pays its people</Title>
        <Text c="dimmed" size="sm">
          Active employees{s ? ` on ${s.as_of}` : ""}. Every amount is an annual salary in US
          dollars at fixed planning rates.
        </Text>
      </div>

      <Group gap="sm">
        <OrgFilters value={state} onChange={set} />
        {filtered && (
          <Button variant="subtle" onClick={() => set({ country: "", department: "", level: "" })}>
            Clear filters
          </Button>
        )}
      </Group>

      {summary.isError ? (
        <Alert color="red">Could not load the figures. {summary.error.message}</Alert>
      ) : (
        <SimpleGrid cols={{ base: 2, md: 4 }}>
          <Tile label="People" value={s ? s.headcount.toLocaleString("en-US") : null} />
          <Tile label="Payroll per year" value={s ? usdShort(s.total) : null}
            hint={s?.total ? money(s.total, "USD") : undefined} />
          <Tile label="Median salary" value={s ? money(s.median, "USD") : null}
            hint={s?.mean ? `Average ${money(s.mean, "USD")}` : undefined} />
          <Tile label="Middle half earns" value={s ? `${usdShort(s.p25)} to ${usdShort(s.p75)}` : null}
            hint="25th to 75th percentile" />
        </SimpleGrid>
      )}

      <SimpleGrid cols={{ base: 1, lg: 2 }}>
        <Card withBorder>
          <Text fw={600}>Salary spread</Text>
          <Text size="sm" c="dimmed" mb="md">How many people earn within each salary band.</Text>
          {bands.data ? (
            bands.data.length ? (
              <BarChart h={260} dataKey="band" withTooltip
                data={bands.data.map((b) => ({ band: usdShort(b.from), People: b.count }))}
                series={[{ name: "People", color: "teal.6" }]} />
            ) : (
              <Text c="dimmed">Nobody matches these filters.</Text>
            )
          ) : (
            <Skeleton h={260} />
          )}
          {s && s.rates.length > 0 && (
            <Tooltip multiline w={260} label={s.rates.filter((r) => r.currency !== "USD")
              .map((r) => `1 ${r.currency} = ${r.usd_per_unit} USD`).join(" · ")}>
              <Text size="xs" c="dimmed" mt="sm" td="underline" style={{ cursor: "help" }}>
                Planning rates from {s.rates[0].valid_from}
              </Text>
            </Tooltip>
          )}
        </Card>

        <Card withBorder>
          <Group justify="space-between" mb="md">
            <div>
              <Text fw={600}>By {state.by}</Text>
              <Text size="sm" c="dimmed">Median salary per group, biggest group first.</Text>
            </div>
            <SegmentedControl size="xs" value={state.by} onChange={(by) => set({ by })}
              data={[{ value: "country", label: "Country" },
                     { value: "department", label: "Department" },
                     { value: "level", label: "Level" }]} />
          </Group>
          {breakdown.data ? <Breakdown groups={breakdown.data.groups} by={state.by} />
            : <Skeleton h={260} />}
        </Card>
      </SimpleGrid>
    </Stack>
  );
}

function Tile({ label, value, hint }: { label: string; value: string | null; hint?: string }) {
  return (
    <Paper withBorder p="md">
      <Text size="xs" tt="uppercase" fw={600} c="dimmed">{label}</Text>
      {value === null ? <Skeleton h={30} mt={6} /> : (
        <Text fz={26} fw={700} className="tabular">{value}</Text>
      )}
      {hint && <Text size="xs" c="dimmed">{hint}</Text>}
    </Paper>
  );
}

export function Breakdown({ groups, by }: { groups: PayGroup[]; by: string }) {
  if (!groups.length) return <Text c="dimmed">Nobody matches these filters.</Text>;
  const top = Math.max(...groups.map((g) => g.median ?? 0));
  return (
    <Table.ScrollContainer minWidth={420}>
      <Table verticalSpacing={6}>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>{by === "country" ? "Country" : by === "level" ? "Level" : "Department"}</Table.Th>
            <Table.Th ta="right">People</Table.Th>
            <Table.Th w="40%">Median (USD)</Table.Th>
            {by === "country" && <Table.Th ta="right">Median (local)</Table.Th>}
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {groups.map((g) => (
            <Table.Tr key={g.key}>
              <Table.Td>{g.label}</Table.Td>
              <Table.Td ta="right" className="tabular">{g.headcount.toLocaleString("en-US")}</Table.Td>
              <Table.Td>
                <Group gap="xs" wrap="nowrap">
                  <Progress value={((g.median ?? 0) / top) * 100} color="teal" w="100%"
                    aria-hidden />
                  <Text size="sm" className="tabular" w={80} ta="right">{money(g.median, "USD")}</Text>
                </Group>
              </Table.Td>
              {by === "country" && (
                <Table.Td ta="right" className="tabular">
                  {g.currency ? money(g.local_median, g.currency) : "-"}
                </Table.Td>
              )}
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Table.ScrollContainer>
  );
}
