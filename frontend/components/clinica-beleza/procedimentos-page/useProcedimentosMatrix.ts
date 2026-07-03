import { useCallback, useEffect, useMemo, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { isBrowserOffline } from "@/lib/clinica-beleza-offline";
import { logger } from "@/lib/logger";
import {
  buildPrecosMapFromMatrix,
  formatPrecoCelula,
} from "./procedimentos-page-utils";
import type { ConvenioItem } from "@/lib/clinica-beleza-api";

export function useProcedimentosMatrix(listLength: number) {
  const [convenios, setConvenios] = useState<ConvenioItem[]>([]);
  const [precosMap, setPrecosMap] = useState<Record<string, string>>({});
  const [matrixLoading, setMatrixLoading] = useState(false);

  const carregarMatrix = useCallback(async () => {
    if (isBrowserOffline()) return;
    setMatrixLoading(true);
    try {
      const data = await ClinicaBelezaAPI.procedures.convenioPrecosMatrix();
      setConvenios(data.convenios || []);
      setPrecosMap(buildPrecosMapFromMatrix(data.precos || []));
    } catch (e) {
      logger.warn("Erro ao carregar matriz de preços:", e);
    } finally {
      setMatrixLoading(false);
    }
  }, []);

  useEffect(() => {
    void carregarMatrix();
  }, [carregarMatrix, listLength]);

  const precoCelula = useMemo(
    () => (procId: number, convId: number) => formatPrecoCelula(precosMap, procId, convId),
    [precosMap],
  );

  return { convenios, precosMap, matrixLoading, carregarMatrix, precoCelula };
}
