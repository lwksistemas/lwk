import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";
import type { LojaInfo } from "@/types/dashboard";
import type { DashboardData, FinancialSummary } from "./clinica-beleza-dashboard-types";
import { currentDashboardMesAno, parseDashboardMesAno } from "./clinica-beleza-dashboard-utils";

/**
 * Dashboard clínica: dispara dashboard + financeiro em paralelo assim que houver slug.
 * Não espera info_publica terminar (waterfall removido).
 */
export function useClinicaBelezaDashboard(loja: LojaInfo | null | undefined) {
  const params = useParams();
  const slug = (params?.slug as string) || loja?.slug || "";
  const [data, setData] = useState<DashboardData | null>(null);
  const [financial, setFinancial] = useState<FinancialSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [mesAno, setMesAno] = useState(currentDashboardMesAno);
  const mesAnoMax = useMemo(() => currentDashboardMesAno(), []);

  const fetchData = useCallback(
    async (forceRefresh = false) => {
      if (!slug && !loja?.id) return;
      setLoading(true);
      try {
        const { mes, ano } = parseDashboardMesAno(mesAno);
        const lojaCtx = { id: loja?.id, slug: loja?.slug || slug };
        const qs = `period=proximos&mes=${mes}&ano=${ano}${forceRefresh ? "&refresh=1" : ""}`;
        const [dashRes, finRes] = await Promise.all([
          clinicaBelezaFetch(`/dashboard/?${qs}`, {}, lojaCtx),
          clinicaBelezaFetch(`/financeiro/resumo/?mes=${mes}&ano=${ano}`, {}, lojaCtx).catch(() => null),
        ]);
        if (dashRes.ok) setData(await dashRes.json());
        else setData(null);
        if (finRes?.ok) setFinancial(await finRes.json());
      } catch (err) {
        logger.error("Dashboard fetch error:", err);
        setData(null);
      } finally {
        setLoading(false);
      }
    },
    [loja?.id, loja?.slug, slug, mesAno],
  );

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  return {
    slug,
    data,
    financial,
    loading,
    mesAno,
    setMesAno,
    mesAnoMax,
    fetchData,
  };
}
