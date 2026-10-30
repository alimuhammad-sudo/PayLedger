export type Role = "admin" | "viewer";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
}

export interface Reference {
  countries: { code: string; name: string; currency: string }[];
  departments: string[];
  levels: string[];
  change_reasons: string[];
}

export interface EmployeeRow {
  id: number;
  staff_id: string;
  full_name: string;
  email: string;
  job_title: string;
  department: string;
  level: string;
  country: string;
  currency: string;
  start_date: string;
  end_date: string | null;
  active: boolean;
  salary_minor: number;
  salary_usd_cents: number;
}

export interface SalaryChange {
  id: number;
  old_salary_minor: number | null;
  new_salary_minor: number;
  effective_on: string;
  reason: string;
  note: string | null;
  changed_by: string | null;
  changed_at: string;
}

export interface EmployeeDetail extends EmployeeRow {
  history: SalaryChange[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface Stats {
  headcount: number;
  total: number | null;
  mean: number | null;
  p25: number | null;
  median: number | null;
  p75: number | null;
  min: number | null;
  max: number | null;
}

export interface Summary extends Stats {
  as_of: string;
  rates: { currency: string; usd_per_unit: string; valid_from: string }[];
}

export interface Group extends Stats {
  key: string;
  label: string;
  currency: string | null;
  local_median: number | null;
}

export interface Band {
  from: number;
  to: number;
  count: number;
}

export interface PayrollRun {
  id: number;
  year: number;
  month: number;
  headcount: number;
  total_usd_cents: number;
  created_at: string;
}

export interface PayrollRunDetail extends PayrollRun {
  countries: {
    country: string;
    country_name: string;
    currency: string;
    headcount: number;
    gross_minor: number;
    gross_usd_cents: number;
  }[];
}

export interface Payslip {
  employee_id: number;
  staff_id: string;
  full_name: string;
  country: string;
  currency: string;
  annual_salary_minor: number;
  days_paid: number;
  days_in_month: number;
  gross_minor: number;
  gross_usd_cents: number;
}
