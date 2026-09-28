"use client";

import { useEffect, type ReactNode } from "react";
import { useParams, useRouter } from "next/navigation";
import { useClinicaPodeVerConsulta } from "@/hooks/clinica-beleza/useClinicaPodeVerConsulta";

/** Lista de consultas: profissional, administrador e recepção. Prontuário fica fora. */
export function ConsultasOperacionalGate({ children }: { children: ReactNode }) {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const { podeAbrirConsultas, loaded } = useClinicaPodeVerConsulta();

  useEffect(() => {
    if (loaded && !podeAbrirConsultas) {
      router.replace(`/loja/${slug}/agenda`);
    }
  }, [loaded, podeAbrirConsultas, router, slug]);

  if (!loaded || !podeAbrirConsultas) {
    return <div className="text-center py-16 text-gray-500">Redirecionando...</div>;
  }
  return <>{children}</>;
}
