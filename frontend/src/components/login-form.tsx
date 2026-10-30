"use client";

import { Alert, Button, Center, Paper, PasswordInput, Stack, Text, TextInput, Title } from "@mantine/core";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, ApiError } from "@/lib/api";
import type { User } from "@/lib/types";

export function LoginForm() {
  const router = useRouter();
  const qc = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const user = await api<User>("/auth/login", { method: "POST", body: { email, password } });
      qc.setQueryData(["me"], user);
      router.replace("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
      setBusy(false);
    }
  }

  return (
    <Center mih="100vh" bg="gray.0" p="md">
      <Paper withBorder shadow="sm" p="xl" w={380} component="form" onSubmit={submit}>
        <Stack>
          <div>
            <Title order={2}>PayLedger</Title>
            <Text c="dimmed" size="sm">Salary records and pay insight for ACME HR.</Text>
          </div>
          {error && <Alert color="red" role="alert">{error}</Alert>}
          <TextInput label="Email" type="email" autoComplete="username" required
            value={email} onChange={(e) => setEmail(e.currentTarget.value)} />
          <PasswordInput label="Password" autoComplete="current-password" required
            value={password} onChange={(e) => setPassword(e.currentTarget.value)} />
          <Button type="submit" loading={busy} disabled={!email || !password}>Sign in</Button>
          <Text size="xs" c="dimmed">
            Demo: hr.admin@acme-hr.example (admin) or hr.viewer@acme-hr.example (viewer).
            Password in the README.
          </Text>
        </Stack>
      </Paper>
    </Center>
  );
}
