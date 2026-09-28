"use client";

import { useEffect, useState } from "react";
import { usuarioPodeAbrirConsultas, usuarioPodeVerConsulta } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";

export function useClinicaPodeVerConsulta() {
  const [podeVerConsulta, setPodeVerConsulta] = useState(true);
  const [podeAbrirConsultas, setPodeAbrirConsultas] = useState(true);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let ativo = true;
    ClinicaBelezaAPI.me
      .get()
      .then((me) => {
        if (!ativo) return;
        const dados = me ?? {};
        setPodeVerConsulta(usuarioPodeVerConsulta(dados));
        setPodeAbrirConsultas(usuarioPodeAbrirConsultas(dados));
        setLoaded(true);
      })
      .catch(() => {
        if (!ativo) return;
        setPodeVerConsulta(false);
        setPodeAbrirConsultas(false);
        setLoaded(true);
      });
    return () => {
      ativo = false;
    };
  }, []);

  return { podeVerConsulta, podeAbrirConsultas, loaded };
}
