'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import BotaoSuporte from '@/components/suporte/BotaoSuporte';

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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-purple-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold">Super Admin</h1>
              <span className="text-purple-200">Painel de Controle</span>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-md transition-colors"
            >
              Sair
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
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
              title="Relatórios"
              description="Relatórios e análises do sistema"
              icon="📊"
              href="/superadmin/relatorios"
              color="pink"
            />
          </div>
        </div>
      </main>
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

{/* Botão Flutuante de Suporte */}
<BotaoSuporte />
