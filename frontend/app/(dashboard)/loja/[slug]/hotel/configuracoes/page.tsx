'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { CreditCard, LogIn, Users, ChevronRight, Database, Download, History, Settings, ArrowLeft } from 'lucide-react';
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
      color: 'from-emerald-500 to-teal-600',
      iconBg: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
      itens: ['Baixar boleto', 'Histórico de pagamento'],
    },
    {
      titulo: 'Cadastrar Funcionários',
      descricao: 'Gerencie a equipe do hotel',
      href: `${base}/funcionarios`,
      icon: Users,
      color: 'from-blue-500 to-indigo-600',
      iconBg: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
      itens: ['Adicionar funcionários', 'Permissões'],
    },
    {
      titulo: 'Configurar Tela de Login',
      descricao: 'Personalize a aparência da tela de login',
      href: `${base}/login`,
      icon: LogIn,
      color: 'from-purple-500 to-violet-600',
      iconBg: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
      itens: ['Logo', 'Cores e identidade visual'],
    },
    {
      titulo: 'Backup de Dados',
      descricao: 'Exportar e importar dados do hotel',
      href: `${base}/backup`,
      icon: Database,
      color: 'from-amber-500 to-orange-600',
      iconBg: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
      itens: ['Exportar backup', 'Importar backup', 'Restaurar dados'],
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      {/* Header */}
      <div className="bg-gradient-to-r from-sky-600 to-cyan-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/15 rounded-lg">
                <Settings className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Configurações</h1>
                <p className="text-white/80 text-sm">Gerencie assinatura, funcionários, login e backup</p>
              </div>
            </div>
            <Link href={`/loja/${slug}/hotel`} className="px-3 py-2 bg-white/15 hover:bg-white/25 rounded-md transition-colors text-sm flex items-center gap-1">
              <ArrowLeft className="w-4 h-4" /> Voltar
            </Link>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {opcoes.map((op) => {
            const Icon = op.icon;
            return (
              <Link
                key={op.href}
                href={op.href}
                className="group block bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden hover:shadow-lg transition-all duration-200"
              >
                {/* Color bar top */}
                <div className={`h-1.5 bg-gradient-to-r ${op.color}`} />
                <div className="p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-3">
                        <div className={`p-2.5 rounded-xl ${op.iconBg}`}>
                          <Icon size={22} />
                        </div>
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{op.titulo}</h2>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{op.descricao}</p>
                      <ul className="space-y-1.5">
                        {op.itens.map((item) => (
                          <li key={item} className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
                            <span className="w-1 h-1 rounded-full bg-gray-400 dark:bg-gray-500 shrink-0" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <ChevronRight size={20} className="text-gray-300 group-hover:text-sky-500 shrink-0 transition-colors mt-1" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
