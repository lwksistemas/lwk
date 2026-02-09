'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import BotaoSuporte from '@/components/suporte/BotaoSuporte';
import NotificacoesSeguranca from '@/components/NotificacoesSeguranca';
import { ToastContainer, useToast } from '@/components/ToastNotificacao';

interface Estatisticas {
  total_lojas: number;
  lojas_ativas: number;
  lojas_trial: number;
  lojas_inativas: number;
  receita_mensal_estimada: number;
}

export default function SuperAdminDashboard() {
  const router = useRouter();
  const [stats, setStats] = useState<Estatisticas | null>(null);
  const [loading, setLoading] = useState(true);
  const { toasts, addToast, removeToast } = useToast();

  useEffect(() => {
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
      console.error('Erro ao carregar estatísticas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    authService.logout();
    router.push('/superadmin/login');
  };

  const handleNovaViolacao = (violacao: any) => {
    // Mostrar toast para violações críticas
    if (violacao.criticidade === 'critica') {
      addToast({
        tipo: 'critico',
        titulo: '🚨 Violação Crítica Detectada',
        mensagem: `${violacao.tipo_display}: ${violacao.usuario_nome}`,
        duracao: 10000, // 10 segundos para críticas
      });
    } else if (violacao.criticidade === 'alta') {
      addToast({
        tipo: 'aviso',
        titulo: '⚠️ Alerta de Segurança',
        mensagem: `${violacao.tipo_display}: ${violacao.usuario_nome}`,
        duracao: 7000,
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
    <div className="min-h-screen bg-gray-50">
      {/* Toast Container */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      
      {/* Header */}
      <nav className="bg-purple-900 text-white shadow-lg">
        <div className="w-full max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold">Super Admin</h1>
              <span className="text-purple-200">Painel de Controle</span>
            </div>
            <div className="flex items-center space-x-4">
              {/* Notificações de Segurança */}
              <NotificacoesSeguranca onNovaViolacao={handleNovaViolacao} />
              
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
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Total de Lojas</h3>
              <p className="text-3xl font-bold text-purple-600 mt-2">{stats?.total_lojas || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Lojas Ativas</h3>
              <p className="text-3xl font-bold text-green-600 mt-2">{stats?.lojas_ativas || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Em Trial</h3>
              <p className="text-3xl font-bold text-yellow-600 mt-2">{stats?.lojas_trial || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Receita Mensal</h3>
              <p className="text-3xl font-bold text-blue-600 mt-2">
                R$ {stats?.receita_mensal_estimada?.toFixed(2) || '0.00'}
              </p>
            </div>
          </div>

          {/* Menu de Ações */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <MenuCard
              title="Gerenciar Lojas"
              description="Criar, editar e gerenciar todas as lojas do sistema"
              icon="🏪"
              href="/superadmin/lojas"
              color="purple"
            />
            <MenuCard
              title="Busca de Logs"
              description="Busca avançada e análise detalhada de logs"
              icon="🔍"
              href="/superadmin/dashboard/logs"
              color="indigo"
            />
            <MenuCard
              title="Dashboard de Auditoria"
              description="Análise de ações, estatísticas e padrões de uso"
              icon="📈"
              href="/superadmin/dashboard/auditoria"
              color="teal"
            />
            <MenuCard
              title="Tipos de Loja"
              description="Configurar tipos de loja e dashboards personalizados"
              icon="🎨"
              href="/superadmin/tipos-loja"
              color="indigo"
            />
            <MenuCard
              title="Planos"
              description="Gerenciar planos de assinatura e preços"
              icon="💎"
              href="/superadmin/planos"
              color="blue"
            />
            <MenuCard
              title="Financeiro"
              description="Controle financeiro e pagamentos das lojas"
              icon="💰"
              href="/superadmin/financeiro"
              color="green"
            />
            <MenuCard
              title="Usuários"
              description="Gerenciar super admins e equipe de suporte"
              icon="👥"
              href="/superadmin/usuarios"
              color="cyan"
            />
            <MenuCard
              title="Busca de Logs"
              description="Histórico de acessos e análises avançadas do sistema"
              icon="📊"
              href="/superadmin/dashboard/logs"
              color="pink"
            />
            <MenuCard
              title="Alertas de Segurança"
              description="Monitoramento de violações e atividades suspeitas"
              icon="�"
              href="/superadmin/dashboard/alertas"
              color="red"
            />
            <MenuCard
              title="Configuração Asaas"
              description="Configurar e monitorar integração com API Asaas"
              icon="🔧"
              href="/superadmin/asaas"
              color="orange"
            />
          </div>
        </div>
      </main>
      
      {/* Botão Flutuante de Suporte */}
      <BotaoSuporte />
    </div>
  );
}

interface MenuCardProps {
  title: string;
  description: string;
  icon: string;
  href: string;
  color: string;
}

function MenuCard({ title, description, icon, href, color }: MenuCardProps) {
  const colorClasses = {
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

  return (
    <a
      href={href}
      className={`block p-6 rounded-lg border-2 transition-all ${colorClasses[color as keyof typeof colorClasses]}`}
    >
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </a>
  );
}
