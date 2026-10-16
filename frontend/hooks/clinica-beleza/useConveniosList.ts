"use client";

import { useEffect, useState } from "react";
import { ClinicaBelezaAPI, type ConvenioItem } from "@/lib/clinica-beleza-api";
import { conveniosAtivos } from "@/lib/convenio-precos";

export function useConveniosList(enabled = true) {
  const [convenios, setConvenios] = useState<ConvenioItem[]>([]);

  useEffect(() => {
    if (!enabled) return;
    ClinicaBelezaAPI.convenios.list({ all: 1 })
      .then((rows) => setConvenios(conveniosAtivos(Array.isArray(rows) ? rows : [])))
      .catch(() => setConvenios([]));
  }, [enabled]);

  return convenios;
}
