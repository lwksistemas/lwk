"use client";

import { useCallback, useEffect, useState } from "react";
import apiClient from "@/lib/api-client";
import { logger } from "@/lib/logger";
import {
  DEFAULT_COLUNAS_PACIENTES,
  resolveColunasPacientes,
  type PacientesColunaDef,
} from "@/lib/clinica-pacientes-colunas-config";

/** Carrega colunas visíveis da listagem de Clientes (login-config). */
export function usePacientesColunas() {
  const [keys, setKeys] = useState<string[]>(DEFAULT_COLUNAS_PACIENTES);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<{ colunas_pacientes?: string[] | null }>(
        "/crm-vendas/login-config/",
      );
      const resolved = resolveColunasPacientes(data.colunas_pacientes);
      setKeys(resolved.map((c) => c.key));
    } catch (err) {
      logger.warn("Erro ao carregar colunas de clientes:", err);
      setKeys([...DEFAULT_COLUNAS_PACIENTES]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const colunasVisiveis: PacientesColunaDef[] = resolveColunasPacientes(keys);

  return {
    colunasKeys: keys,
    colunasVisiveis,
    loading,
    reload: load,
  };
}
