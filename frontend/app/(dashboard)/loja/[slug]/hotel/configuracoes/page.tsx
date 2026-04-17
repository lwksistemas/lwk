'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { CreditCard, LogIn, Users, ChevronRight, Database, Download, History } from 'lucide-react';
import { authService } from '@/lib/auth';
import apiClient from '@/lib/api-client';

export default function HotelConfiguracoesPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const base = `/loja/${slug}/hotel/configuracoes`;

  const [acessoAdmin, setAcessoAdmin] = useState(() => authService.hasAdminAccess());

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        // Tenta sincronizar flags de acesso (endpoint pode não existir para hotel, fallback ok)
        const r = await apiClient.get<{ is_vendedor?: boolean }>('/crm-vendas/me/').catch(() => null);
        if (r?.data) authService.syncCrmMeFlags(r.data);
        if (!cancel) setAcessoAdmin(authService.hasAdminAccess());
      } catch {
        if (!cancel) setAcessoAdmin(authService.hasAdminAccess());
      }
    })();
    return () => { cancel = true; };
  }, []);

  const opcoes = [
    {
      titulo: 'Pagar Assinatura',
      descricao: 'Baixar boleto e ver histórico de pagamentos',
      href: `/loja/${slug}/assinatura`,
      icon: CreditCard,
      itens: ['Baixar boleto', 'Histórico de pagamento'],
    },
    {
      titulo: 'Cadastrar Funcionários',
      descricao: 'Gerencie a equipe do hotel',
      href: `${base}/funcionarios`,
      icon: Users,
      itens: ['Adicionar funcionários', 'Permissões'],
    },
    {
      titulo: 'Configurar Tela de Login',
      descricao: 'Personalize a aparência da tela de login',
      href: `${base}/login`,
      icon: LogIn,
      itens: ['Logo', 'Cores e identidade visual'],
    },
    {
      titulo: 'Backup de Dados',
      descricao: 'Exportar e importar dados do hotel',
      href: `${base}/backup`,
      icon: Database,
      itens: ['Exportar backup', 'Importar backup', 'Restaurar dados'],
    },
  ];

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Configurações</h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Gerencie assinatura, funcionários, login e backup</p>
        <Link href={`/loja/${slug}/hotel`} className="text-sm text-sky-700 hover:underline">← Voltar</Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {opcoes.map((op) => {
          const Icon = op.icon;
          return (
            <Link
              key={op.href}
              href={op.href}
              className="block bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6 hover:shadow-md hover:border-sky-500/30 transition-all group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2.5 rounded-lg bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300">
                      <Icon size={22} />
                    </div>
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{op.titulo}</h2>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{op.descricao}</p>
                  <ul className="space-y-1">
                    {op.itens.map((item) => (
                      <li key={item} className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
                        {op.href.includes('assinatura') && item === 'Baixar boleto' && <Download size={12} className="shrink-0" />}
                        {op.href.includes('assinatura') && item === 'Histórico de pagamento' && <History size={12} className="shrink-0" />}
                        <span>• {item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <ChevronRight size={20} className="text-gray-400 group-hover:text-sky-600 shrink-0 transition-colors" />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
