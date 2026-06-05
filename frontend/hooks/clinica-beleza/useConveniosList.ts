"use client";

import { useEffect, useState } from "react";
import { ClinicaBelezaAPI, type ConvenioItem } from "@/lib/clinica-beleza-api";

export function useConveniosList(enabled = true) {
  const [convenios, setConvenios] = useState<ConvenioItem[]>([]);

  useEffect(() => {
    if (!enabled) return;
    ClinicaBelezaAPI.convenios.list()
      .then((rows) => setConvenios(Array.isArray(rows) ? rows : []))
      .catch(() => setConvenios([]));
  }, [enabled]);

  return convenios;
}
