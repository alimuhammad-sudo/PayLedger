import { MantineProvider, Table } from "@mantine/core";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { nextSort, SortHeader } from "@/components/people-directory";
import { monthName, runnableMonths } from "@/lib/months";

function renderHeader(props: Partial<React.ComponentProps<typeof SortHeader>> = {}) {
  const onClick = vi.fn();
  render(
    <MantineProvider>
      <Table>
        <Table.Thead>
          <Table.Tr>
            <SortHeader label="Salary" active={false} order="asc" onClick={onClick} {...props} />
          </Table.Tr>
        </Table.Thead>
      </Table>
    </MantineProvider>,
  );
  return onClick;
}

describe("SortHeader", () => {
  it("tells screen readers the current sort", () => {
    renderHeader({ active: true, order: "desc" });
    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "descending");
  });

  it("is a button that reports clicks", async () => {
    const onClick = renderHeader();
    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "none");
    await userEvent.click(screen.getByRole("button", { name: /salary/i }));
    expect(onClick).toHaveBeenCalledOnce();
  });
});

describe("nextSort", () => {
  it("flips direction on the same column", () => {
    expect(nextSort({ sort: "name", order: "asc" }, "name")).toEqual({ sort: "name", order: "desc" });
  });

  it("starts a new column ascending, but salary with the highest paid", () => {
    expect(nextSort({ sort: "name", order: "desc" }, "level")).toEqual({ sort: "level", order: "asc" });
    expect(nextSort({ sort: "name", order: "asc" }, "salary")).toEqual({ sort: "salary", order: "desc" });
  });
});

describe("payroll months", () => {
  it("offers this month first and goes back across the new year", () => {
    const months = runnableMonths(new Date(2026, 0, 20), 2);
    expect(months.map((m) => m.label)).toEqual(["January 2026", "December 2025", "November 2025"]);
  });

  it("names a month", () => {
    expect(monthName(2026, 9)).toBe("September 2026");
  });
});
