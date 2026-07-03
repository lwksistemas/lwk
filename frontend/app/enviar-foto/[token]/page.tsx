'use client';

import { useParams } from 'next/navigation';
import { EnviarFotoPublicaClient } from '@/components/clinica-beleza/EnviarFotoPublicaClient';

/** Links legados com token no path (`/enviar-foto/{token}`). */
export default function EnviarFotoPathPage() {
  const params = useParams();
  const tokenRaw = params.token as string;
  return <EnviarFotoPublicaClient token={tokenRaw} />;
}
