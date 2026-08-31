"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { buildConsultasBasePath } from "@/components/clinica-beleza/consultas-page/consultas-page-utils";

export default function ProntuarioHubRedirectPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  useEffect(() => {
    router.replace(buildConsultasBasePath(slug));
  }, [router, slug]);

  return <div className="text-center py-16 text-gray-500">Redirecionando às consultas...</div>;
}
