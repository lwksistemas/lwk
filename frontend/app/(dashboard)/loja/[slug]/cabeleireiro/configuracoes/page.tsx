'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  ChevronRight,
  CreditCard,
  Database,
  Download,
  FileText,
  History,
  LogIn,
  MessageCircle,
  Palette,
  Users,
} from 'lucide-react';
import { SalaoPageHeader } from '@/components/cabeleireiro/SalaoPageHeader';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';

export default function SalaoConfiguracoesPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const base = `/loja/${slug}/cabeleireiro/configuracoes`;

  const opcoes = [
    {
      titulo: 'Pagar assinatura',
      descricao: 'Baixar boleto e ver histórico de pagamentos',
      href: `/loja/${slug}/assinatura`,
      icon: CreditCard,
      itens: ['Baixar boleto', 'Histórico de pagamento'],
    },
    {
      titulo: 'Identidade visual',
      descricao: 'Cores do menu, fundo e status da agenda',
      href: `${base}/aparencia`,
      icon: Palette,
      itens: ['Cor do menu', 'Fundo das páginas', 'Cores dos status na agenda'],
    },
    {
      titulo: 'Configurar tela de login',
      descricao: 'Logo, fundo e cores da tela de login do salão',
      href: `${base}/login`,
      icon: LogIn,
      itens: ['Logo', 'Imagem de fundo', 'Cores do login'],
    },
    {
      titulo: 'Cadastrar profissionais',
      descricao: 'Equipe do salão e cores na agenda',
      href: `/loja/${slug}/cabeleireiro/profissionais`,
      icon: Users,
      itens: ['Adicionar profissionais', 'Especialidades', 'Cor na agenda'],
    },
    {
      titulo: 'Configurar WhatsApp',
      descricao: 'Confirmações e lembretes de agendamento por WhatsApp',
      href: `/loja/${slug}/configuracoes/whatsapp`,
      icon: MessageCircle,
      itens: ['Integração WhatsApp', 'Lembretes de agenda'],
    },
    {
      titulo: 'Nota Fiscal (NFS-e)',
      descricao: 'Configure como as notas fiscais serão emitidas',
      href: `${base}/nota-fiscal`,
      icon: FileText,
      itens: ['Provedor de NF', 'Certificado digital', 'Emissão automática'],
    },
    {
      titulo: 'Backup',
      descricao: 'Exportar e importar dados do salão',
      href: `${base}/backup`,
      icon: Database,
      itens: ['Exportar backup', 'Importar backup', 'Restaurar dados'],
    },
  ];

  return (
    <div>
      <SalaoPageHeader
        title="Configurações"
        subtitle="Assinatura, identidade visual, login, equipe e integrações"
      />
      <div className="p-4 md:p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        {opcoes.map((op) => {
          const Icon = op.icon;
          return (
            <Link
              key={op.href}
              href={op.href}
              className="block bg-white rounded-xl border border-[#E8D5DC] p-6 hover:shadow-md hover:border-[#4A3042]/40 transition-all group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2.5 rounded-lg text-white" style={{ backgroundColor: SALAO_PRIMARY }}>
                      <Icon size={22} />
                    </div>
                    <h2 className="text-lg font-semibold text-gray-900">{op.titulo}</h2>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{op.descricao}</p>
                  <ul className="space-y-1">
                    {op.itens.map((item) => (
                      <li key={item} className="text-xs text-gray-500 flex items-center gap-2">
                        {op.href.includes('assinatura') && item === 'Baixar boleto' && (
                          <Download size={12} className="shrink-0" />
                        )}
                        {op.href.includes('assinatura') && item === 'Histórico de pagamento' && (
                          <History size={12} className="shrink-0" />
                        )}
                        <span>• {item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <ChevronRight
                  size={20}
                  className="text-gray-400 group-hover:text-[#4A3042] shrink-0 transition-colors"
                />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
