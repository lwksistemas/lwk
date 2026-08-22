'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';

export default function ClinicaGeralRecursosPage() {
  const params = useParams();
  const slug = params.slug as string;

  return (
    <div className="space-y-4 p-8">
      <h1 className="text-xl font-semibold text-slate-800">Recursos</h1>
      <p className="text-sm text-slate-500">
        Configurações do consultório. WhatsApp e assinatura usam as telas compartilhadas da loja.
      </p>
      <div className="flex flex-col gap-2 text-sm">
        <Link href={`/loja/${slug}/configuracoes/whatsapp`} className="text-teal-700 hover:underline">
          WhatsApp
        </Link>
        <Link href={`/loja/${slug}/assinatura`} className="text-teal-700 hover:underline">
          Assinatura
        </Link>
        <Link href={`/loja/${slug}/suporte`} className="text-teal-700 hover:underline">
          Suporte
        </Link>
      </div>
    </div>
  );
}
