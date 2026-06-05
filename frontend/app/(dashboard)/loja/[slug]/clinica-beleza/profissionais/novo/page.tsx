"use client";

import { useEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";

/** Redireciona rota legada para ?novo=1 ou ?id= na lista de profissionais. */
export default function NovoProfissionalRedirectPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const id = searchParams.get("id");

  useEffect(() => {
    const base = `/loja/${slug}/clinica-beleza/profissionais`;
    router.replace(id ? `${base}?id=${id}` : `${base}?novo=1`);
  }, [slug, id, router]);

  return null;
}
