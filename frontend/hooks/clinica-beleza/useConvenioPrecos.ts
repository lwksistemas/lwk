"use client";

import { useEffect, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { buildPrecosMap } from "@/lib/convenio-precos";
import { logger } from "@/lib/logger";

export function useConvenioPrecos(convenioId: number | "") {
  const [precosMap, setPrecosMap] = useState<Record<number, number>>({});

  useEffect(() => {
    if (!convenioId) {
      setPrecosMap({});
      return;
    }
    (async () => {
      try {
        const rows = await ClinicaBelezaAPI.convenios.precos(Number(convenioId));
        setPrecosMap(buildPrecosMap(rows));
      } catch (e) {
        logger.warn("Erro ao carregar preços do convênio:", e);
        setPrecosMap({});
      }
    })();
  }, [convenioId]);

  return precosMap;
}
