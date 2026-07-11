"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { searchClinicaPatients } from "@/lib/clinica-beleza-cadastros-api";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";

export type LocalizarClienteMode = "edit" | "historico";

export function useLocalizarClienteModal(open: boolean) {
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [resultados, setResultados] = useState<PatientQuickOption[]>([]);
  const debounceRef = useRef<number | null>(null);
  const requestIdRef = useRef(0);

  const reset = useCallback(() => {
    setQuery("");
    setSearching(false);
    setResultados([]);
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

  return {
    query,
    setQuery,
    searching,
    resultados,
    reset,
  };
}
