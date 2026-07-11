"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchHistoricoPaciente,
  searchClinicaPatients,
} from "@/lib/clinica-beleza-cadastros-api";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";

export type LocalizarClienteMode = "edit" | "historico";

export function useLocalizarClienteModal(open: boolean, mode: LocalizarClienteMode) {
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [resultados, setResultados] = useState<PatientQuickOption[]>([]);
  const [paciente, setPaciente] = useState<PatientQuickOption | null>(null);
  const [historico, setHistorico] = useState<Consulta[]>([]);
  const [loadingHistorico, setLoadingHistorico] = useState(false);
  const [erroHistorico, setErroHistorico] = useState<string | null>(null);
  const debounceRef = useRef<number | null>(null);
  const requestIdRef = useRef(0);

  const reset = useCallback(() => {
    setQuery("");
    setSearching(false);
    setResultados([]);
    setPaciente(null);
    setHistorico([]);
    setLoadingHistorico(false);
    setErroHistorico(null);
    if (debounceRef.current != null) {
      window.clearTimeout(debounceRef.current);
      debounceRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!open) {
      reset();
      return;
    }
  }, [open, reset]);

  useEffect(() => {
    if (!open) return;
    const q = query.trim();
    if (q.length < 1) {
      setResultados([]);
      setSearching(false);
      return;
    }

    if (debounceRef.current != null) {
      window.clearTimeout(debounceRef.current);
    }
    setSearching(true);
    const requestId = ++requestIdRef.current;
    debounceRef.current = window.setTimeout(() => {
      void (async () => {
        try {
          const rows = await searchClinicaPatients(q);
          if (requestId !== requestIdRef.current) return;
          setResultados(rows);
        } catch {
          if (requestId !== requestIdRef.current) return;
          setResultados([]);
        } finally {
          if (requestId === requestIdRef.current) setSearching(false);
        }
      })();
    }, 300);

    return () => {
      if (debounceRef.current != null) {
        window.clearTimeout(debounceRef.current);
        debounceRef.current = null;
      }
    };
  }, [open, query]);

  const selecionarPaciente = useCallback(
    async (p: PatientQuickOption) => {
      if (mode === "edit") {
        setPaciente(p);
        return p;
      }
      setPaciente(p);
      setLoadingHistorico(true);
      setErroHistorico(null);
      setHistorico([]);
      try {
        const rows = await fetchHistoricoPaciente(p.id);
        setHistorico(Array.isArray(rows) ? (rows as Consulta[]) : []);
      } catch {
        setErroHistorico("Não foi possível carregar o histórico de consultas.");
        setHistorico([]);
      } finally {
        setLoadingHistorico(false);
      }
      return p;
    },
    [mode],
  );

  const voltarBusca = useCallback(() => {
    setPaciente(null);
    setHistorico([]);
    setErroHistorico(null);
    setLoadingHistorico(false);
  }, []);

  return {
    query,
    setQuery,
    searching,
    resultados,
    paciente,
    historico,
    loadingHistorico,
    erroHistorico,
    selecionarPaciente,
    voltarBusca,
    reset,
  };
}
