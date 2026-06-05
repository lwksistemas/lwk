"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

/** Redireciona rota legada para ?novo=1 na lista de consultas. */
export default function NovaConsultaRedirectPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  useEffect(() => {
    router.replace(`/loja/${slug}/clinica-beleza/consultas?novo=1`);
  }, [slug, router]);

  return null;
}
