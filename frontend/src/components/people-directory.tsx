"use client";

import {
  Alert,
  Badge,
  Button,
  Group,
  Pagination,
  SegmentedControl,
  Skeleton,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
  UnstyledButton,
} from "@mantine/core";
import { useDebouncedValue } from "@mantine/hooks";
import { IconArrowDown, IconArrowUp, IconPlus, IconSearch, IconSelector } from "@tabler/icons-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { OrgFilters } from "@/components/filters";
import { money } from "@/lib/money";
import { useEmployees, useMe } from "@/lib/queries";
import { useUrlState } from "@/lib/url-state";

const DEFAULTS = {
  search: "", country: "", department: "", level: "",
  status: "active", sort: "name", order: "asc", page: "1",
};
const PAGE_SIZE = 25;

export const COLUMNS = [
  { key: "name", label: "Name" },
  { key: "staff_id", label: "Staff ID" },
  { key: "department", label: "Department" },
  { key: "level", label: "Level" },
  { key: "country", label: "Country" },
  { key: "start_date", label: "Started" },
  { key: "salary", label: "Salary", right: true },
] as const;

/** Clicking the current column flips direction; a new column starts ascending, except
 * salary, which starts with the highest paid. */
export function nextSort(current: { sort: string; order: string }, column: string) {
  if (current.sort === column) {
    return { sort: column, order: current.order === "asc" ? "desc" : "asc" };
  }
  return { sort: column, order: column === "salary" ? "desc" : "asc" };
}

export function PeopleDirectory() {
  const isAdmin = useMe().data?.role === "admin";
  const [state, set] = useUrlState(DEFAULTS);
  const [typed, setTyped] = useState(state.search);
  const [debounced] = useDebouncedValue(typed, 300);

  useEffect(() => {
    if (debounced !== state.search) set({ search: debounced });
    // only the debounced text should trigger this
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debounced]);

  const page = Number(state.page) || 1;
  const { data, isError, error, isPlaceholderData } = useEmployees({
    ...state, page, size: PAGE_SIZE,
  });

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <div>
          <Title order={2}>People</Title>
          <Text c="dimmed" size="sm">
            {data ? `${data.total.toLocaleString("en-US")} people` : "Loading..."}
          </Text>
        </div>
        {isAdmin && (
          <Button component={Link} href="/people/new" leftSection={<IconPlus size={16} />}>
            Add person
          </Button>
        )}
      </Group>

      <Group gap="sm">
        <TextInput aria-label="Search by name, email or staff ID" placeholder="Name, email or staff ID"
          leftSection={<IconSearch size={16} />} w={260} value={typed}
          onChange={(e) => setTyped(e.currentTarget.value)} />
        <OrgFilters value={state} onChange={set} />
        <SegmentedControl ml="auto" value={state.status} onChange={(status) => set({ status })}
          aria-label="Status"
          data={[{ value: "active", label: "Active" }, { value: "left", label: "Left" },
                 { value: "all", label: "All" }]} />
      </Group>

      {isError ? (
        <Alert color="red">Could not load people. {error.message}</Alert>
      ) : !data ? (
        <Skeleton h={400} />
      ) : data.items.length === 0 ? (
        <Text c="dimmed" ta="center" py="xl">Nobody matches. Try clearing a filter.</Text>
      ) : (
        <div style={{ opacity: isPlaceholderData ? 0.6 : 1 }}>
          <Table.ScrollContainer minWidth={900}>
            <Table highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  {COLUMNS.map((c) => (
                    <SortHeader key={c.key} label={c.label} right={"right" in c}
                      active={state.sort === c.key} order={state.order}
                      onClick={() => set(nextSort(state, c.key))} />
                  ))}
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {data.items.map((e) => (
                  <Table.Tr key={e.id}>
                    <Table.Td>
                      <Text component={Link} href={`/people/${e.id}`} fw={500} size="sm"
                        td="underline">{e.full_name}</Text>
                      <Text size="xs" c="dimmed">{e.job_title}</Text>
                    </Table.Td>
                    <Table.Td><Text size="sm" ff="monospace">{e.staff_id}</Text></Table.Td>
                    <Table.Td>{e.department}</Table.Td>
                    <Table.Td>{e.level}</Table.Td>
                    <Table.Td>{e.country}</Table.Td>
                    <Table.Td>
                      {e.start_date}
                      {!e.active && <Badge ml="xs" color="gray" size="sm">Left</Badge>}
                    </Table.Td>
                    <Table.Td ta="right" className="tabular">{money(e.salary_minor, e.currency)}</Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
          <Group justify="space-between" mt="md">
            <Text size="sm" c="dimmed">
              {(page - 1) * PAGE_SIZE + 1}-{Math.min(page * PAGE_SIZE, data.total)} of{" "}
              {data.total.toLocaleString("en-US")}
            </Text>
            <Pagination total={Math.max(1, Math.ceil(data.total / PAGE_SIZE))} value={page}
              onChange={(p) => set({ page: String(p) })} />
          </Group>
        </div>
      )}
    </Stack>
  );
}

export function SortHeader({ label, active, order, right, onClick }: {
  label: string; active: boolean; order: string; right?: boolean; onClick: () => void;
}) {
  const Icon = !active ? IconSelector : order === "asc" ? IconArrowUp : IconArrowDown;
  return (
    <Table.Th ta={right ? "right" : undefined}
      aria-sort={active ? (order === "asc" ? "ascending" : "descending") : "none"}>
      <UnstyledButton onClick={onClick} fw={600} fz="sm">
        <Group gap={4} wrap="nowrap" justify={right ? "flex-end" : undefined}>
          {label}
          <Icon size={14} opacity={active ? 1 : 0.4} />
        </Group>
      </UnstyledButton>
    </Table.Th>
  );
}
