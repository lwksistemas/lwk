'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { CreditCard, MessageCircle, Settings } from 'lucide-react';

export default function ClinicaGeralRecursosPage() {
  const params = useParams();
  const slug = params.slug as string;

  const itens = [
    {
      href: `/loja/${slug}/clinica-geral/configuracoes/agenda`,
      titulo: 'Configurações da agenda',
      texto: 'Expediente, duração dos slots, endereço e telefone',
      icon: Settings,
    },
    {
      href: `/loja/${slug}/configuracoes/whatsapp`,
      titulo: 'WhatsApp',
      texto: 'Confirmações e lembretes de consulta',
      icon: MessageCircle,
    },
    {
      href: `/loja/${slug}/assinatura`,
      titulo: 'Assinatura',
      texto: 'Boleto e histórico do plano',
      icon: CreditCard,
    },
  ];

  return (
    <div className="mx-auto max-w-2xl space-y-4 p-8">
      <h1 className="text-xl font-semibold text-slate-800">Recursos</h1>
      <p className="text-sm text-slate-500">Atalhos do consultório. Sem lote TISS neste módulo.</p>
      <div className="space-y-3">
        {itens.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-5 hover:border-teal-500"
            >
              <Icon className="mt-0.5 h-5 w-5 text-teal-700" />
              <div>
                <h2 className="text-sm font-semibold text-slate-800">{item.titulo}</h2>
                <p className="text-sm text-slate-500">{item.texto}</p>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
