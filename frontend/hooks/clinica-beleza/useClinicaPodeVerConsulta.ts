"use client";

import { useEffect, useState } from "react";
import { usuarioPodeVerConsulta } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";

export function useClinicaPodeVerConsulta() {
  const [podeVerConsulta, setPodeVerConsulta] = useState(true);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let ativo = true;
    ClinicaBelezaAPI.me
      .get()
      .then((me) => {
        if (!ativo) return;
        setPodeVerConsulta(usuarioPodeVerConsulta(me ?? {}));
        setLoaded(true);
      })
      .catch(() => {
        if (!ativo) return;
        setPodeVerConsulta(false);
        setLoaded(true);
      });
    return () => {
      ativo = false;
    };
  }, []);

  return { podeVerConsulta, loaded };
}
