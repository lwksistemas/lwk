"use client";

import type { LojaInfo } from "@/types/dashboard";
import { ClinicaBelezaDashboardContent } from "@/components/clinica-beleza/clinica-beleza-dashboard/ClinicaBelezaDashboardContent";

export default function DashboardClinicaBeleza({
  loja,
  onLogout,
}: {
  loja: LojaInfo;
  onLogout?: () => void;
}) {
  return <ClinicaBelezaDashboardContent loja={loja} onLogout={onLogout} />;
}
