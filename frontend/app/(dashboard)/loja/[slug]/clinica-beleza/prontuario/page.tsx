"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ClinicaConsultaAccessGate } from "@/components/clinica-beleza/ClinicaConsultaAccessGate";
import { buildConsultasBasePath } from "@/components/clinica-beleza/consultas-page/consultas-page-utils";

function ProntuarioHubRedirect() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  useEffect(() => {
    router.replace(buildConsultasBasePath(slug));
  }, [router, slug]);

  return <div className="text-center py-16 text-gray-500">Redirecionando às consultas...</div>;
}

export default function ProntuarioHubRedirectPage() {
  return (
    <ClinicaConsultaAccessGate>
      <ProntuarioHubRedirect />
    </ClinicaConsultaAccessGate>
  );
}
