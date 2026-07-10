"use client";

import { useCallback, useEffect, useState } from "react";
import apiClient from "@/lib/api-client";
import { logger } from "@/lib/logger";
import {
  DEFAULT_COLUNAS_ESTOQUE,
  resolveColunasEstoque,
  type EstoqueColunaDef,
} from "@/lib/clinica-estoque-colunas-config";

/** Carrega colunas visíveis da listagem de Estoque (login-config). */
export function useEstoqueColunas() {
  const [keys, setKeys] = useState<string[]>(DEFAULT_COLUNAS_ESTOQUE);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<{ colunas_estoque?: string[] | null }>(
        "/crm-vendas/login-config/",
      );
      const resolved = resolveColunasEstoque(data.colunas_estoque);
      setKeys(resolved.map((c) => c.key));
    } catch (err) {
      logger.warn("Erro ao carregar colunas de estoque:", err);
      setKeys([...DEFAULT_COLUNAS_ESTOQUE]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const colunasVisiveis: EstoqueColunaDef[] = resolveColunasEstoque(keys);

  return {
    colunasKeys: keys,
    colunasVisiveis,
    loading,
    reload: load,
  };
}
