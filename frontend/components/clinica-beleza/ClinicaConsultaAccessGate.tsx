"use client";

import { useEffect, type ReactNode } from "react";
import { useParams, useRouter } from "next/navigation";
import { useClinicaPodeVerConsulta } from "@/hooks/clinica-beleza/useClinicaPodeVerConsulta";

/** Bloqueia tela de consulta/prontuário para recepção e manda para a agenda. */
export function ClinicaConsultaAccessGate({ children }: { children: ReactNode }) {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const { podeVerConsulta, loaded } = useClinicaPodeVerConsulta();

  useEffect(() => {
    if (loaded && !podeVerConsulta) {
      router.replace(`/loja/${slug}/agenda`);
    }
  }, [loaded, podeVerConsulta, router, slug]);

  if (!loaded || !podeVerConsulta) {
    return <div className="text-center py-16 text-gray-500">Redirecionando...</div>;
  }
  return <>{children}</>;
}
