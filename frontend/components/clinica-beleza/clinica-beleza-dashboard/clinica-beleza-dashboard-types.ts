export interface DashboardStats {
  appointments_today: number;
  appointments_yesterday?: number;
  patients_total: number;
  procedures_total: number;
  revenue_month: number;
  revenue_today?: number;
  sessions_month?: number;
}

export interface DashboardFilter {
  mes: number;
  ano: number;
  label: string;
  is_current_month: boolean;
}

export interface DashboardAppointment {
  id: number;
  date: string;
  time?: string;
  patient_name: string;
  procedure_name: string;
  professional_name: string;
  status: string;
}

export interface RevenueDay {
  day: string;
  value: number;
}

export interface TopProcedure {
  name: string;
  count: number;
}

export interface FinancialSummary {
  faturamento: number;
  despesas: number;
  lucro: number;
}

export interface DashboardData {
  filter?: DashboardFilter;
  statistics: DashboardStats;
  next_appointments: DashboardAppointment[];
  revenue_last_7_days?: RevenueDay[];
  top_procedures?: TopProcedure[];
  top_procedures_volume?: TopProcedure[];
}
