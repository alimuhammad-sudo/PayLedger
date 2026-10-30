"use client";

import { LineChart } from "@mantine/charts";
import {
  Alert,
  Anchor,
  Badge,
  Button,
  Card,
  Center,
  Grid,
  Group,
  Loader,
  Stack,
  Text,
  Timeline,
  Title,
} from "@mantine/core";
import { IconArrowLeft, IconCalendarOff, IconEdit, IconTrendingUp } from "@tabler/icons-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { EditDetailsModal, LeavingDateModal, SalaryChangeModal } from "@/components/person-modals";
import { change, compact, money } from "@/lib/money";
import { useEmployee, useMe } from "@/lib/queries";

type Dialog = "salary" | "edit" | "leaving" | null;

export function Person() {
  const { id } = useParams<{ id: string }>();
  const isAdmin = useMe().data?.role === "admin";
  const { data: p, isError, error } = useEmployee(id);
  const [dialog, setDialog] = useState<Dialog>(null);

  if (isError) {
    return <Alert color="red" title="Could not open this person">{error.message}</Alert>;
  }
  if (!p) return <Center p="xl"><Loader /></Center>;

  const oldestFirst = [...p.history].reverse();

  return (
    <Stack gap="lg">
      <Anchor component={Link} href="/people" size="sm">
        <Group gap={4}><IconArrowLeft size={14} /> People</Group>
      </Anchor>

      <Group justify="space-between" align="flex-start">
        <div>
          <Group gap="xs">
            <Title order={2}>{p.full_name}</Title>
            {p.active ? (
              p.end_date ? <Badge color="orange">Leaving {p.end_date}</Badge> : <Badge>Active</Badge>
            ) : (
              <Badge color="gray">Left {p.end_date}</Badge>
            )}
          </Group>
          <Text c="dimmed">{p.job_title} · {p.level} · {p.department} · {p.country}</Text>
        </div>
        {isAdmin && (
          <Group gap="xs">
            <Button leftSection={<IconTrendingUp size={16} />} onClick={() => setDialog("salary")}
              disabled={!p.active}>
              Change salary
            </Button>
            <Button variant="default" leftSection={<IconEdit size={16} />}
              onClick={() => setDialog("edit")}>Edit details</Button>
            <Button variant="default" leftSection={<IconCalendarOff size={16} />}
              onClick={() => setDialog("leaving")}>
              {p.end_date ? "Leaving date" : "Set leaving date"}
            </Button>
          </Group>
        )}
      </Group>

      <Grid>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card withBorder>
            <Text size="sm" c="dimmed">Annual salary today</Text>
            <Text fz={30} fw={700} className="tabular">{money(p.salary_minor, p.currency, true)}</Text>
            <Text size="sm" c="dimmed">about {money(p.salary_usd_cents, "USD")} at planning rates</Text>
            <Stack gap={4} mt="md">
              <Row label="Staff ID" value={p.staff_id} />
              <Row label="Email" value={p.email} />
              <Row label="Started" value={p.start_date} />
              <Row label="Pay currency" value={p.currency} />
            </Stack>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Card withBorder>
            <Text fw={600}>Salary history</Text>
            <Text size="sm" c="dimmed" mb="md">
              Every change is kept, with the date it took effect and who made it.
            </Text>
            {oldestFirst.length > 1 && (
              <LineChart h={180} mb="lg" dataKey="date" curveType="stepAfter" withDots
                data={oldestFirst.map((h) => ({ date: h.effective_on, Salary: h.new_salary_minor }))}
                series={[{ name: "Salary", color: "teal.6" }]}
                valueFormatter={(v) => money(v, p.currency)}
                yAxisProps={{ width: 80, domain: ["auto", "auto"],
                  tickFormatter: (v: number) => compact(v, p.currency) }} />
            )}
            <Timeline active={0} bulletSize={14} lineWidth={2}>
              {p.history.map((h) => (
                <Timeline.Item key={h.id} title={
                  <Group gap="xs">
                    <Text fw={600} className="tabular">{money(h.new_salary_minor, p.currency, true)}</Text>
                    {h.old_salary_minor !== null && (
                      <Badge variant="light" color={h.new_salary_minor > h.old_salary_minor ? "teal" : "red"}>
                        {change(h.old_salary_minor, h.new_salary_minor)}
                      </Badge>
                    )}
                  </Group>
                }>
                  <Text size="sm">{h.reason}{h.note ? ` - ${h.note}` : ""}</Text>
                  <Text size="xs" c="dimmed">
                    From {h.effective_on} · {h.changed_by ? `by ${h.changed_by}` : "imported"}
                  </Text>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </Grid.Col>
      </Grid>

      {dialog === "salary" && <SalaryChangeModal person={p} onClose={() => setDialog(null)} />}
      {dialog === "edit" && <EditDetailsModal person={p} onClose={() => setDialog(null)} />}
      {dialog === "leaving" && <LeavingDateModal person={p} onClose={() => setDialog(null)} />}
    </Stack>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <Group justify="space-between" gap="xs" wrap="nowrap">
      <Text size="sm" c="dimmed">{label}</Text>
      <Text size="sm" truncate title={value}>{value}</Text>
    </Group>
  );
}
