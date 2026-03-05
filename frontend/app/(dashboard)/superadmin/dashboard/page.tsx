'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { formatCurrency } from '@/lib/financeiro-helpers';
import NotificacoesSeguranca from '@/components/NotificacoesSeguranca';
import SeletorServidorBackend from '@/components/SeletorServidorBackend';
import { ToastContainer, useToast } from '@/components/ToastNotificacao';
import { ThemeToggle } from '@/components/ui/ThemeProvider';

interface Estatisticas {
  total_lojas: number;
  lojas_ativas: number;
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
  purple: 'bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/40 border-purple-200 dark:border-purple-700',
  indigo: 'bg-indigo-50 dark:bg-indigo-900/20 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 border-indigo-200 dark:border-indigo-700',
  blue: 'bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/40 border-blue-200 dark:border-blue-700',
  green: 'bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/40 border-green-200 dark:border-green-700',
  cyan: 'bg-cyan-50 dark:bg-cyan-900/20 hover:bg-cyan-100 dark:hover:bg-cyan-900/40 border-cyan-200 dark:border-cyan-700',
  pink: 'bg-pink-50 dark:bg-pink-900/20 hover:bg-pink-100 dark:hover:bg-pink-900/40 border-pink-200 dark:border-pink-700',
  red: 'bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 border-red-200 dark:border-red-700',
  orange: 'bg-orange-50 dark:bg-orange-900/20 hover:bg-orange-100 dark:hover:bg-orange-900/40 border-orange-200 dark:border-orange-700',
  teal: 'bg-teal-50 dark:bg-teal-900/20 hover:bg-teal-100 dark:hover:bg-teal-900/40 border-teal-200 dark:border-teal-700',
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
      // Erro já logado pelo interceptor do apiClient; deixa stats null (mostra 0)
      setStats(null);
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
              <SeletorServidorBackend />
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
          {/* Aviso: usando Render com 0 lojas = provavelmente outro banco */}
          {typeof window !== 'undefined' &&
            localStorage.getItem('backend_servidor') === 'render' &&
            (stats?.total_lojas ?? 0) === 0 && (
            <div className="mb-4 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg">
              <p className="text-amber-800 dark:text-amber-200 text-sm font-medium">
                Você está no servidor <strong>Render</strong> e não há lojas listadas. Para ver as mesmas lojas do Heroku, o Render precisa usar o <strong>mesmo banco de dados</strong>: no Dashboard do Render → serviço <strong>lwksistemas-backup</strong> → <strong>Environment</strong>, defina <code className="bg-amber-100 dark:bg-amber-800 px-1 rounded">DATABASE_URL</code> com o mesmo valor do Heroku (<code className="text-xs">heroku config:get DATABASE_URL -a lwksistemas</code>). Depois faça um novo deploy.
              </p>
              <p className="text-amber-700 dark:text-amber-300 text-xs mt-2">
                Instruções detalhadas no repositório: <code>docs/RENDER-DATABASE-SYNC.md</code>
              </p>
            </div>
          )}
          {/* Dica: Render (backup) é mais lento — usar Heroku no dia a dia */}
          {typeof window !== 'undefined' &&
            localStorage.getItem('backend_servidor') === 'render' &&
            (stats?.total_lojas ?? 0) > 0 && (
            <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg">
              <p className="text-blue-800 dark:text-blue-200 text-sm">
                Servidor <strong>Render</strong> (backup) pode ser mais lento. Para uso diário, prefira <strong>Heroku</strong> no seletor acima.
              </p>
            </div>
          )}

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
              label="Lojas Inativas"
              value={stats?.lojas_inativas || 0}
              color="text-red-600"
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
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
      <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">{label}</h3>
      <p className={`text-3xl font-bold mt-2 ${color} dark:opacity-90`}>{value}</p>
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
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">{title}</h3>
      <p className="text-sm text-gray-600 dark:text-gray-400">{description}</p>
    </a>
  );
}
