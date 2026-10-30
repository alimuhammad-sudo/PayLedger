"use client";

import { AppShell, Badge, Button, Center, Group, Loader, NavLink, Text } from "@mantine/core";
import { IconChartBar, IconCash, IconLogout, IconUsers } from "@tabler/icons-react";
import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Suspense, useEffect } from "react";

import { api } from "@/lib/api";
import { useMe } from "@/lib/queries";

const NAV = [
  { href: "/", label: "Overview", icon: IconChartBar, exact: true },
  { href: "/people", label: "People", icon: IconUsers },
  { href: "/payroll", label: "Payroll", icon: IconCash },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const me = useMe();
  const router = useRouter();
  const qc = useQueryClient();

  useEffect(() => {
    if (me.isError) router.replace("/login");
  }, [me.isError, router]);

  if (!me.data) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    );
  }

  async function signOut() {
    await api("/auth/logout", { method: "POST" });
    qc.clear();
    router.replace("/login");
  }

  return (
    <AppShell header={{ height: 56 }} navbar={{ width: 210, breakpoint: "sm" }} padding="lg">
      <AppShell.Header px="md">
        <Group h="100%" justify="space-between">
          <Text fw={700}>
            Pay<Text span c="teal" inherit>Ledger</Text>
          </Text>
          <Group gap="sm">
            <Text size="sm" visibleFrom="sm">{me.data.full_name}</Text>
            <Badge variant="light" color={me.data.role === "admin" ? "teal" : "gray"}>
              {me.data.role === "admin" ? "HR admin" : "Viewer"}
            </Badge>
            <Button variant="subtle" size="xs" leftSection={<IconLogout size={16} />}
              onClick={signOut}>
              Sign out
            </Button>
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="xs" aria-label="Main">
        <Suspense fallback={<Links active={null} />}>
          <ActiveLinks />
        </Suspense>
      </AppShell.Navbar>
      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}

// Reading the URL streams in under Suspense, so it never blocks prerendering.
function ActiveLinks() {
  return <Links active={usePathname()} />;
}

function Links({ active }: { active: string | null }) {
  return NAV.map(({ href, label, icon: Icon, exact }) => {
    const on = active !== null && (exact ? active === href : active.startsWith(href));
    return (
      <NavLink key={href} component={Link} href={href} label={label} active={on}
        leftSection={<Icon size={18} />} aria-current={on ? "page" : undefined} />
    );
  });
}
