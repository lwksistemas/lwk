"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { searchClinicaPatients } from "@/lib/clinica-beleza-cadastros-api";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import { buildProntuarioPacientePath } from "@/components/clinica-beleza/prontuario/prontuario-paths";

export function useProntuarioHub() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [resultados, setResultados] = useState<PatientQuickOption[]>([]);
  const debounceRef = useRef<number | null>(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
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
  }, [query]);

  const abrirProntuario = useCallback(
    (patientId: number) => {
      router.push(buildProntuarioPacientePath(slug, patientId));
    },
    [router, slug],
  );

  return {
    slug,
    query,
    setQuery,
    searching,
    resultados,
    abrirProntuario,
  };
}
