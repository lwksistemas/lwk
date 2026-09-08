import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";

export const DASHBOARD_STATUS_COLORS: Record<string, string> = {
  SCHEDULED: "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200",
  CONFIRMED: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
  PENDING: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
  COMPLETED: "bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300",
  CANCELLED: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
};

/** Paleta dos gráficos — 1ª cor = primária da loja. */
export function getDashboardChartColors(primary: string = CLINICA_BELEZA_PRIMARY): string[] {
  return [primary, "#A64D63", "#C4727E", "#E8A0B0", "#D4A574"];
}

export function currentDashboardMesAno(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function parseDashboardMesAno(value: string): { mes: number; ano: number } {
  const [anoStr, mesStr] = value.split("-");
  return { ano: Number(anoStr), mes: Number(mesStr) };
}

export function pctChangeDashboard(current: number, previous: number): string | null {
  if (!previous) return null;
  const pct = Math.round(((current - previous) / previous) * 100);
  return `${pct >= 0 ? "+" : ""}${pct}%`;
}
