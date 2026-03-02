'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { formatCurrency } from '@/lib/financeiro-helpers';
import NotificacoesSeguranca from '@/components/NotificacoesSeguranca';
import { ToastContainer, useToast } from '@/components/ToastNotificacao';
import { ThemeToggle } from '@/components/ui/ThemeProvider';

interface Estatisticas {
  total_lojas: number;
  lojas_ativas: number;
  lojas_trial: number;
  lojas_inativas: number;
  receita_mensal_estimada: number;
}

interface MenuCardProps {
  title: string;
  description: string;
  icon: string;
  href: string;
  color: string;
}

// Configuração dos cards do menu - Single Source of Truth
const MENU_CARDS: MenuCardProps[] = [
  {
    title: 'Gerenciar Lojas',
    description: 'Criar, editar e gerenciar todas as lojas do sistema',
    icon: '🏪',
    href: '/superadmin/lojas',
    color: 'purple',
  },
  {
    title: 'Tipos de App',
    description: 'Configurar tipos de app e dashboards personalizados',
    icon: '🎨',
    href: '/superadmin/tipos-app',
    color: 'indigo',
  },
  {
    title: 'Planos',
    description: 'Gerenciar planos de assinatura e preços',
    icon: '💎',
    href: '/superadmin/planos',
    color: 'blue',
  },
  {
    title: 'Usuários',
    description: 'Gerenciar super admins e equipe de suporte',
    icon: '👥',
    href: '/superadmin/usuarios',
    color: 'cyan',
  },
  {
    title: 'Financeiro',
    description: 'Controle financeiro e pagamentos das lojas',
    icon: '💰',
    href: '/superadmin/financeiro',
    color: 'green',
  },
  {
    title: 'Configuração Asaas',
    description: 'Configurar e monitorar integração com API Asaas',
    icon: '🔧',
    href: '/superadmin/asaas',
    color: 'orange',
  },
  {
    title: 'Configuração Mercado Pago',
    description: 'Configurar boletos via Mercado Pago para as lojas',
    icon: '💳',
    href: '/superadmin/mercadopago',
    color: 'blue',
  },
  {
    title: 'Busca de Logs',
    description: 'Busca avançada e análise detalhada de logs',
    icon: '🔍',
    href: '/superadmin/dashboard/logs',
    color: 'indigo',
  },
  {
    title: 'Dashboard de Auditoria',
    description: 'Análise de ações, estatísticas e padrões de uso',
    icon: '📈',
    href: '/superadmin/dashboard/auditoria',
    color: 'teal',
  },
  {
    title: 'Alertas de Segurança',
    description: 'Monitoramento de violações e atividades suspeitas',
    icon: '🚨',
    href: '/superadmin/dashboard/alertas',
    color: 'red',
  },
  {
    title: 'Monitoramento de Storage',
    description: 'Acompanhar crescimento do banco de todas as lojas em tempo real',
    icon: '💾',
    href: '/superadmin/dashboard/storage',
    color: 'purple',
  },
];

// Configuração das cores - DRY (Don't Repeat Yourself)
const COLOR_CLASSES: Record<string, string> = {
  purple: 'bg-purple-50 hover:bg-purple-100 border-purple-200',
  indigo: 'bg-indigo-50 hover:bg-indigo-100 border-indigo-200',
  blue: 'bg-blue-50 hover:bg-blue-100 border-blue-200',
  green: 'bg-green-50 hover:bg-green-100 border-green-200',
  cyan: 'bg-cyan-50 hover:bg-cyan-100 border-cyan-200',
  pink: 'bg-pink-50 hover:bg-pink-100 border-pink-200',
  red: 'bg-red-50 hover:bg-red-100 border-red-200',
  orange: 'bg-orange-50 hover:bg-orange-100 border-orange-200',
  teal: 'bg-teal-50 hover:bg-teal-100 border-teal-200',
};

export default function SuperAdminDashboard() {
  const router = useRouter();
  const [stats, setStats] = useState<Estatisticas | null>(null);
  const [loading, setLoading] = useState(true);
  const { toasts, addToast, removeToast } = useToast();

  useEffect(() => {
    // Verificação de autenticação
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    loadStats();
  }, [router]);

  const loadStats = async () => {
    try {
      const response = await apiClient.get('/superadmin/lojas/estatisticas/');
      setStats(response.data);
    } catch (error) {
      // Erro já logado pelo interceptor do apiClient
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    authService.logout();
    router.push('/superadmin/login');
  };

  const handleNovaViolacao = (violacao: any) => {
    // Mostrar toast apenas para violações críticas e altas
    const toastConfig = {
      critica: {
        tipo: 'critico' as const,
        titulo: '🚨 Violação Crítica Detectada',
        duracao: 10000,
      },
      alta: {
        tipo: 'aviso' as const,
        titulo: '⚠️ Alerta de Segurança',
        duracao: 7000,
      },
    };

    const config = toastConfig[violacao.criticidade as keyof typeof toastConfig];
    
    if (config) {
      addToast({
        tipo: config.tipo,
        titulo: config.titulo,
        mensagem: `${violacao.tipo_display}: ${violacao.usuario_nome}`,
        duracao: config.duracao,
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      
      {/* Header */}
      <nav className="bg-purple-900 dark:bg-purple-950 text-white shadow-lg">
        <div className="w-full max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold">Super Admin</h1>
              <span className="text-purple-200 dark:text-purple-300">Painel de Controle</span>
            </div>
            <div className="flex items-center space-x-4">
              <NotificacoesSeguranca onNovaViolacao={handleNovaViolacao} />
              {/* Botão de Dark Mode */}
              <ThemeToggle />
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-md transition-colors"
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="w-full max-w-full py-6 px-4 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Estatísticas */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <StatCard
              label="Total de Lojas"
              value={stats?.total_lojas || 0}
              color="text-purple-600"
            />
            <StatCard
              label="Lojas Ativas"
              value={stats?.lojas_ativas || 0}
              color="text-green-600"
            />
            <StatCard
              label="Em Trial"
              value={stats?.lojas_trial || 0}
              color="text-yellow-600"
            />
            <StatCard
              label="Receita Mensal"
              value={formatCurrency(stats?.receita_mensal_estimada ?? 0)}
              color="text-blue-600"
            />
          </div>

          {/* Menu de Ações */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {MENU_CARDS.map((card) => (
              <MenuCard key={card.href} {...card} />
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

// Componente StatCard - Reutilizável e com responsabilidade única
function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-gray-500 text-sm font-medium">{label}</h3>
      <p className={`text-3xl font-bold mt-2 ${color}`}>{value}</p>
    </div>
  );
}

// Componente MenuCard - Reutilizável e com responsabilidade única
function MenuCard({ title, description, icon, href, color }: MenuCardProps) {
  const colorClass = COLOR_CLASSES[color] || COLOR_CLASSES.purple;

  return (
    <a
      href={href}
      className={`block p-6 rounded-lg border-2 transition-all ${colorClass}`}
      aria-label={`Acessar ${title}`}
    >
      <div className="text-4xl mb-3" aria-hidden="true">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </a>
  );
}
