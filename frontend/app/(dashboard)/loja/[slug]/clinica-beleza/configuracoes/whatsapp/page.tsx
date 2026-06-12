'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

/** Redireciona para a tela central de WhatsApp (todos os apps). */
export default function ClinicaBelezaWhatsappRedirectPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';

  useEffect(() => {
    router.replace(`/loja/${slug}/configuracoes/whatsapp`);
  }, [router, slug]);

  return null;
}
