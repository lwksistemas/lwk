'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  CreditCard,
  LogIn,
  Users,
  MessageCircle,
  ChevronRight,
  Download,
  History,
  Database,
  FileText,
  Palette,
} from 'lucide-react';
import { ClinicaBelezaPageContent } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { useClinicaBelezaTheme } from '@/components/clinica-beleza/ClinicaBelezaThemeContext';
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';

export default function ClinicaBelezaConfiguracoesPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const base = `/loja/${slug}/clinica-beleza/configuracoes`;
  const { primary } = useClinicaBelezaTheme();

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
      descricao: 'Cores do menu, fundo, status da agenda e colunas de Consultas/Estoque',
      href: `${base}/aparencia`,
      icon: Palette,
      itens: [
        'Cor do menu',
        'Fundo das páginas',
        'Cores dos status na agenda',
        'Colunas de Consultas',
        'Colunas de Estoque',
      ],
    },
    {
      titulo: 'Configurar tela de login',
      descricao: 'Logo, fundo e cores da tela de login da clínica',
      href: `${base}/login`,
      icon: LogIn,
      itens: ['Logo', 'Imagem de fundo', 'Cores do login'],
    },
    {
      titulo: 'Cadastrar profissionais',
      descricao: 'Equipe da clínica e acessos ao sistema',
      href: `/loja/${slug}/clinica-beleza/profissionais`,
      icon: Users,
      itens: ['Adicionar profissionais', 'Perfis de acesso', 'Horários de trabalho'],
    },
    {
      titulo: 'Configurar WhatsApp',
      descricao: 'Confirmações e lembretes de agendamento por WhatsApp',
      href: `/loja/${slug}/configuracoes/whatsapp`,
      icon: MessageCircle,
      itens: ['Integração WhatsApp', 'Lembretes de consultas'],
    },
    {
      titulo: 'Receituário Memed — Timbrado',
      descricao: 'PDF timbrado A4 para receitas e pedidos de exames',
      href: `${base}/memed`,
      icon: FileText,
      itens: ['Upload Timbrado A4.pdf', 'Aplica a todos os prescritores', 'Receita e exames'],
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
      descricao: 'Exportar e importar dados da sua clínica',
      href: `${base}/backup`,
      icon: Database,
      itens: ['Exportar backup', 'Importar backup', 'Restaurar dados'],
    },
  ];

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Configurações"
        subtitle="Gerencie assinatura, identidade visual, login, equipe e integrações"
        showOffline={false}
      />
      <ClinicaBelezaPageContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {opcoes.map((op) => {
            const Icon = op.icon;
            return (
              <Link
                key={op.href}
                href={op.href}
                className="block bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md hover:border-[color:var(--cb-primary)]/40 transition-all group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <div
                        className="p-2.5 rounded-lg text-white"
                        style={{ backgroundColor: primary }}
                      >
                        <Icon size={22} />
                      </div>
                      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {op.titulo}
                      </h2>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{op.descricao}</p>
                    <ul className="space-y-1">
                      {op.itens.map((item) => (
                        <li
                          key={item}
                          className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2"
                        >
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
                    className="text-gray-400 group-hover:text-[color:var(--cb-primary)] shrink-0 transition-colors"
                  />
                </div>
              </Link>
            );
          })}
        </div>
      </ClinicaBelezaPageContent>
    </>
  );
}
