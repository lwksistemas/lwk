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
  Settings,
  Sliders,
  Database,
} from 'lucide-react';

export default function CrmVendasConfiguracoesPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const base = `/loja/${slug}/crm-vendas/configuracoes`;

  const opcoes = [
    {
      titulo: 'Pagar assinatura',
      descricao: 'Baixar boleto e ver histórico de pagamentos',
      href: `/loja/${slug}/assinatura`,
      icon: CreditCard,
      itens: ['Baixar boleto', 'Histórico de pagamento'],
    },
    {
      titulo: 'Configurar tela de login',
      descricao: 'Personalize a aparência da tela de login da sua loja',
      href: `${base}/login`,
      icon: LogIn,
      itens: ['Logo', 'Cores e identidade visual'],
    },
    {
      titulo: 'Cadastrar funcionários',
      descricao: 'Gerencie vendedores e equipe de vendas',
      href: `${base}/funcionarios`,
      icon: Users,
      itens: ['Adicionar vendedores', 'Permissões'],
    },
    {
      titulo: 'Configurar WhatsApp',
      descricao: 'Enviar lembretes de tarefas do calendário por WhatsApp',
      href: `${base}/whatsapp`,
      icon: MessageCircle,
      itens: ['Integração WhatsApp', 'Lembretes do calendário'],
    },
    {
      titulo: 'Backup',
      descricao: 'Exportar e importar dados da sua loja',
      href: `${base}/backup`,
      icon: Database,
      itens: ['Exportar backup', 'Importar backup', 'Restaurar dados'],
    },
    {
      titulo: 'Personalizar CRM',
      descricao: 'Personalize o sistema do jeito que você quiser trabalhar',
      href: `${base}/personalizar`,
      icon: Sliders,
      itens: ['Origens de leads', 'Etapas do pipeline', 'Colunas visíveis', 'Módulos ativos'],
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Configurações
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Gerencie assinatura, login, funcionários e integrações
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {opcoes.map((op) => {
          const Icon = op.icon;
          return (
            <Link
              key={op.href}
              href={op.href}
              className="block bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6 hover:shadow-md hover:border-[#0176d3]/30 dark:hover:border-[#0176d3]/50 transition-all group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2.5 rounded-lg bg-[#e3f3ff] dark:bg-[#0176d3]/20 text-[#0176d3]">
                      <Icon size={22} />
                    </div>
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {op.titulo}
                    </h2>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {op.descricao}
                  </p>
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
                  className="text-gray-400 group-hover:text-[#0176d3] shrink-0 transition-colors"
                />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
