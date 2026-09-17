"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ClinicaConsultaAccessGate } from "@/components/clinica-beleza/ClinicaConsultaAccessGate";

/** Redireciona rota legada para ?novo=1 na lista de consultas. */
function NovaConsultaRedirect() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  useEffect(() => {
    router.replace(`/loja/${slug}/clinica-beleza/consultas?novo=1`);
  }, [slug, router]);

  return null;
}

export default function NovaConsultaRedirectPage() {
  return (
    <ClinicaConsultaAccessGate>
      <NovaConsultaRedirect />
    </ClinicaConsultaAccessGate>
  );
}
