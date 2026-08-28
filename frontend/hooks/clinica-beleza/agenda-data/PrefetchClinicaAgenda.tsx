"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { prefetchClinicaAgenda } from "./useAgendaQueries";
import { readLojaInfoPublicaCache } from "@/lib/loja-info-publica-cache";
import { isTipoClinicaBeleza } from "@/lib/loja-tipo";

/** Enquanto a secretária está no dashboard, já baixa os eventos da agenda. */
export function PrefetchClinicaAgenda({ slug }: { slug: string }) {
  const queryClient = useQueryClient();

  useEffect(() => {
    let cancelled = false;
    const tentar = () => {
      if (cancelled) return true;
      const cached = readLojaInfoPublicaCache(slug);
      if (!cached || !isTipoClinicaBeleza(cached.tipo_loja_nome || "")) return false;
      void prefetchClinicaAgenda(queryClient);
      return true;
    };
    if (tentar()) return;
    const poll = window.setInterval(() => {
      if (tentar()) window.clearInterval(poll);
    }, 300);
    const stop = window.setTimeout(() => window.clearInterval(poll), 8000);
    return () => {
      cancelled = true;
      window.clearInterval(poll);
      window.clearTimeout(stop);
    };
  }, [queryClient, slug]);

  return null;
}
