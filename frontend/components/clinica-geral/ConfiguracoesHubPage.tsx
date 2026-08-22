'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  CalendarClock,
  ChevronRight,
  CreditCard,
  FileSpreadsheet,
  Headphones,
  LogIn,
  MessageCircle,
  Settings,
  Wallet,
} from 'lucide-react';

const NAVY = '#2F2E5B';
const TEAL = '#0D9B9B';

export function ConfiguracoesHubPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const base = `/loja/${slug}/clinica-geral/configuracoes`;

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
      titulo: 'Faturamento',
      descricao: 'Valor das consultas e fechamento de caixa do dia',
      href: `/loja/${slug}/clinica-geral/faturamento`,
      icon: Wallet,
      color: 'from-sky-500 to-blue-600',
      iconBg: 'bg-sky-100 text-sky-700',
      itens: ['Caixa do dia', 'Particular e convênio'],
    },
    {
      titulo: 'Lotes TISS',
      descricao: 'Guias de consulta no padrão ANS para impressão',
      href: `/loja/${slug}/clinica-geral/tiss`,
      icon: FileSpreadsheet,
      color: 'from-slate-500 to-slate-700',
      iconBg: 'bg-slate-100 text-slate-700',
      itens: ['Novo lote', 'Impressão da guia'],
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
    <div className="min-h-full bg-[#F7F8FB]">
      <div className="text-white shadow-sm" style={{ backgroundColor: NAVY }}>
        <div className="mx-auto max-w-6xl px-4 py-5 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-white/15 p-2">
              <Settings className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Configurações</h1>
              <p className="text-sm text-white/80">Agenda, WhatsApp, assinatura e tela de login</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
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
        <p className="mt-6 text-center text-xs text-slate-400" style={{ color: TEAL }}>
          Clínica Geral · LWK Sistemas
        </p>
      </div>
    </div>
  );
}
