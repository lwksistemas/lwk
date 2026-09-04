'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  CalendarClock,
  ChevronRight,
  CreditCard,
  Headphones,
  LogIn,
  MessageCircle,
} from 'lucide-react';
import { ConfiguracoesLayout } from '@/components/clinica-geral/ConfiguracoesLayout';
import { TEAL } from '@/lib/clinica-geral-theme';


export function ConfiguracoesHubPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const base = `/loja/${slug}/clinica/configuracoes`;

  const opcoes = [
    {
      titulo: 'Agenda',
      descricao: 'Horário de atendimento, duração dos slots, endereço e telefone',
      href: `${base}/agenda`,
      icon: CalendarClock,
      color: 'from-[#0D9B9B] to-teal-600',
      iconBg: 'bg-teal-100 text-teal-700',
      itens: ['Início e fim do expediente', 'Duração de 15 minutos', 'Endereço e telefone'],
    },
    {
      titulo: 'WhatsApp',
      descricao: 'Confirmações e lembretes de consulta',
      href: `/loja/${slug}/configuracoes/whatsapp`,
      icon: MessageCircle,
      color: 'from-emerald-500 to-green-600',
      iconBg: 'bg-emerald-100 text-emerald-700',
      itens: ['WhatsApp Web (QR)', 'Mensagens automáticas'],
    },
    {
      titulo: 'Assinatura',
      descricao: 'Boleto e histórico de pagamentos do plano',
      href: `/loja/${slug}/assinatura`,
      icon: CreditCard,
      color: 'from-violet-500 to-indigo-600',
      iconBg: 'bg-violet-100 text-violet-700',
      itens: ['Baixar boleto', 'Histórico de pagamento'],
    },
    {
      titulo: 'Tela de login',
      descricao: 'Logo, fundo e cores da tela de entrada do consultório',
      href: `${base}/login`,
      icon: LogIn,
      color: 'from-[#2F2E5B] to-indigo-700',
      iconBg: 'bg-indigo-100 text-indigo-700',
      itens: ['Logo', 'Imagem de fundo', 'Cores'],
    },
    {
      titulo: 'Suporte',
      descricao: 'Abrir chamado e acompanhar atendimento',
      href: `/loja/${slug}/suporte`,
      icon: Headphones,
      color: 'from-amber-500 to-orange-600',
      iconBg: 'bg-amber-100 text-amber-700',
      itens: ['Novo chamado', 'Histórico de tickets'],
    },
  ];

  return (
    <ConfiguracoesLayout>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {opcoes.map((op) => {
            const Icon = op.icon;
            return (
              <Link
                key={op.href}
                href={op.href}
                className="group block overflow-hidden rounded-xl border border-slate-200 bg-white hover:shadow-lg"
              >
                <div className={`h-1.5 bg-gradient-to-r ${op.color}`} />
                <div className="p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="mb-3 flex items-center gap-3">
                        <div className={`rounded-xl p-2.5 ${op.iconBg}`}>
                          <Icon size={22} />
                        </div>
                        <h2 className="text-lg font-semibold text-slate-900">{op.titulo}</h2>
                      </div>
                      <p className="mb-4 text-sm text-slate-600">{op.descricao}</p>
                      <ul className="space-y-1.5">
                        {op.itens.map((item) => (
                          <li key={item} className="flex items-center gap-2 text-xs text-slate-500">
                            <span className="h-1 w-1 shrink-0 rounded-full bg-slate-400" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <ChevronRight
                      size={20}
                      className="mt-1 shrink-0 text-slate-300 transition-colors group-hover:text-teal-600"
                    />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
        <p className="mt-6 text-center text-xs" style={{ color: TEAL }}>
          Clínica · LWK Sistemas
        </p>
    </ConfiguracoesLayout>
  );
}
