"use client";

import { useCallback, useEffect, useState } from "react";
import apiClient from "@/lib/api-client";
import { logger } from "@/lib/logger";
import {
  DEFAULT_COLUNAS_CONSULTAS,
  resolveColunasConsultas,
  type ConsultasColunaDef,
} from "@/lib/clinica-consultas-colunas-config";

/**
 * Carrega colunas visíveis da listagem de Consultas (login-config).
 * Fallback: padrão sem AGENDA.
 */
export function useConsultasColunas() {
  const [keys, setKeys] = useState<string[]>(DEFAULT_COLUNAS_CONSULTAS);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<{ colunas_consultas?: string[] | null }>(
        "/crm-vendas/login-config/",
      );
      const resolved = resolveColunasConsultas(data.colunas_consultas);
      setKeys(resolved.map((c) => c.key));
    } catch (err) {
      logger.warn("Erro ao carregar colunas de consultas:", err);
      setKeys([...DEFAULT_COLUNAS_CONSULTAS]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const colunasVisiveis: ConsultasColunaDef[] = resolveColunasConsultas(keys);

  return {
    colunasKeys: keys,
    colunasVisiveis,
    loading,
    reload: load,
  };
}
