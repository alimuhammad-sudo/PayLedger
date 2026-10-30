"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  Band,
  EmployeeDetail,
  EmployeeRow,
  Group,
  Page,
  PayrollRun,
  PayrollRunDetail,
  Payslip,
  Reference,
  Summary,
  User,
} from "@/lib/types";

export type Filters = { country?: string; department?: string; level?: string };

export const useMe = () =>
  useQuery({ queryKey: ["me"], queryFn: () => api<User>("/auth/me"), retry: false });

export const useReference = () =>
  useQuery({
    queryKey: ["reference"],
    queryFn: () => api<Reference>("/reference"),
    staleTime: Infinity,
  });

export const useEmployees = (params: Record<string, string | number | undefined>) =>
  useQuery({
    queryKey: ["employees", params],
    queryFn: () => api<Page<EmployeeRow>>("/employees", { query: params }),
    placeholderData: keepPreviousData, // keep the old page on screen while the next loads
  });

export const useEmployee = (id: string) =>
  useQuery({
    queryKey: ["employee", id],
    queryFn: () => api<EmployeeDetail>(`/employees/${id}`),
  });

export const useSummary = (f: Filters) =>
  useQuery({
    queryKey: ["summary", f],
    queryFn: () => api<Summary>("/analytics/summary", { query: f }),
    placeholderData: keepPreviousData,
  });

export const useBreakdown = (by: string, f: Filters) =>
  useQuery({
    queryKey: ["breakdown", by, f],
    queryFn: () => api<{ by: string; groups: Group[] }>("/analytics/breakdown", {
      query: { by, ...f },
    }),
    placeholderData: keepPreviousData,
  });

export const useDistribution = (f: Filters) =>
  useQuery({
    queryKey: ["distribution", f],
    queryFn: () => api<Band[]>("/analytics/distribution", { query: f }),
    placeholderData: keepPreviousData,
  });

export const usePayrollRuns = () =>
  useQuery({ queryKey: ["payroll"], queryFn: () => api<PayrollRun[]>("/payroll/runs") });

export const usePayrollRun = (id: string) =>
  useQuery({
    queryKey: ["payroll", id],
    queryFn: () => api<PayrollRunDetail>(`/payroll/runs/${id}`),
  });

export const usePayslips = (id: string, params: Record<string, string | number | undefined>) =>
  useQuery({
    queryKey: ["payslips", id, params],
    queryFn: () => api<Page<Payslip>>(`/payroll/runs/${id}/payslips`, { query: params }),
    placeholderData: keepPreviousData,
  });

/** Any write that changes employees: refresh lists, the profile and the analytics. */
export function useEmployeeMutation<TBody>(fn: (body: TBody) => Promise<EmployeeDetail>) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: (emp) => {
      qc.setQueryData(["employee", String(emp.id)], emp);
      for (const key of ["employees", "summary", "breakdown", "distribution"]) {
        qc.invalidateQueries({ queryKey: [key] });
      }
    },
  });
}
