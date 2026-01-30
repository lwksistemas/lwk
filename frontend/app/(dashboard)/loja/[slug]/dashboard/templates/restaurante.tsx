'use client';

import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { clinicaApiClient } from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';
import { ThemeToggle } from '@/components/ui/ThemeProvider';
import { DashboardSkeleton, AgendamentosListSkeleton } from '@/components/ui/Skeleton';
import type { LojaInfo, EstatisticasRestaurante, Pedido } from './restaurante/types';
import { ActionButton, StatCard, PedidoCard, EmptyState } from './restaurante/components/restaurante-shared';

// Lazy load dos modais: cada um só é baixado quando o usuário abre (dashboard mais rápido)
const ModalCardapio = dynamic(
  () => import('./restaurante/ModalsAll').then((m) => ({ default: m.ModalCardapio })),
  { ssr: false }
);
const ModalMesas = dynamic(
  () => import('./restaurante/ModalsAll').then((m) => ({ default: m.ModalMesas })),
  { ssr: false }
);
const ModalPedidos = dynamic(
  () => import('./restaurante/ModalsAll').then((m) => ({ default: m.ModalPedidos })),
  { ssr: false }
);
const ModalDelivery = dynamic(
  () => import('./restaurante/ModalsAll').then((m) => ({ default: m.ModalDelivery })),
  { ssr: false }
);
const ModalPDV = dynamic(
  () => import('./restaurante/ModalsAll').then((m) => ({ default: m.ModalPDV })),
  { ssr: false }
);
const ModalNotaFiscal = dynamic(
  () => import('./restaurante/ModalsAll').then((m) => ({ default: m.ModalNotaFiscal })),
  { ssr: false }
);
const ModalEstoque = dynamic(
  () => import('./restaurante/ModalsAll').then((m) => ({ default: m.ModalEstoque })),
  { ssr: false }
);
const ModalBalanca = dynamic(
  () => import('./restaurante/ModalsAll').then((m) => ({ default: m.ModalBalanca })),
  { ssr: false }
);
const ModalFuncionarios = dynamic(
  () => import('./restaurante/ModalsAll').then((m) => ({ default: m.ModalFuncionarios })),
  { ssr: false }
);
const ModalClientes = dynamic(
  () => import('./restaurante/modals').then((m) => ({ default: m.ModalClientes })),
  { ssr: false }
);

export default function DashboardRestaurante({ loja }: { loja: LojaInfo }) {
  const toast = useToast();
  const [estatisticas, setEstatisticas] = useState<EstatisticasRestaurante>({
    pedidos_hoje: 0,
    mesas_ocupadas: '0/0',
    cardapio: 0,
    faturamento: 0
  });
  const [pedidosRecentes, setPedidosRecentes] = useState<Pedido[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingPedidos, setLoadingPedidos] = useState(false);

  const [showModalCardapio, setShowModalCardapio] = useState(false);
  const [showModalMesas, setShowModalMesas] = useState(false);
  const [showModalPedidos, setShowModalPedidos] = useState(false);
  const [showModalDelivery, setShowModalDelivery] = useState(false);
  const [showModalPDV, setShowModalPDV] = useState(false);
  const [showModalNotaFiscal, setShowModalNotaFiscal] = useState(false);
  const [showModalEstoque, setShowModalEstoque] = useState(false);
  const [showModalBalanca, setShowModalBalanca] = useState(false);
  const [showModalFuncionarios, setShowModalFuncionarios] = useState(false);
  const [showModalClientes, setShowModalClientes] = useState(false);

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setLoadingPedidos(true);
      const [statsRes, pedidosRes] = await Promise.all([
        clinicaApiClient.get<EstatisticasRestaurante>('/restaurante/pedidos/estatisticas/'),
        clinicaApiClient.get<Pedido[] | { results?: Pedido[] }>('/restaurante/pedidos/')
      ]);
      const stats = statsRes.data;
      setEstatisticas({
        pedidos_hoje: stats?.pedidos_hoje ?? 0,
        mesas_ocupadas: stats?.mesas_ocupadas ?? '0/0',
        cardapio: stats?.cardapio ?? 0,
        faturamento: stats?.faturamento ?? 0
      });
      const pedidosRaw = pedidosRes.data;
      const pedidosArray = Array.isArray(pedidosRaw)
        ? pedidosRaw.slice(0, 5)
        : (pedidosRaw && typeof pedidosRaw === 'object' && Array.isArray((pedidosRaw as { results?: Pedido[] }).results))
          ? (pedidosRaw as { results: Pedido[] }).results.slice(0, 5)
          : [];
      setPedidosRecentes(pedidosArray);
    } catch (error) {
      console.error('Erro ao carregar dashboard Restaurante:', error);
      toast.error('Erro ao carregar dashboard');
      setPedidosRecentes([]);
    } finally {
      setLoading(false);
      setLoadingPedidos(false);
    }
  }, [toast]);

  useEffect(() => {
    if (typeof window !== 'undefined' && loja?.id) {
      const current = sessionStorage.getItem('current_loja_id');
      if (current !== String(loja.id)) sessionStorage.setItem('current_loja_id', String(loja.id));
      if (loja.slug) sessionStorage.setItem('loja_slug', loja.slug);
    }
    loadDashboard();
  }, [loadDashboard, loja?.id, loja?.slug]);

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="space-y-6 sm:space-y-8 px-2 sm:px-4 lg:px-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
          Dashboard - {loja.nome}
        </h1>
        <ThemeToggle />
      </div>

      {/* Ações Rápidas */}
      <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg card-hover">
        <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
          🚀 Ações Rápidas
        </h3>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2 sm:gap-3 md:gap-4">
          <ActionButton onClick={() => setShowModalCardapio(true)} color="#3B82F6" icon="📋" label="Cardápio" />
          <ActionButton onClick={() => setShowModalMesas(true)} color="#F59E0B" icon="🪑" label="Mesas" />
          <ActionButton onClick={() => setShowModalPedidos(true)} color="#10B981" icon="📦" label="Pedidos" />
          <ActionButton onClick={() => setShowModalDelivery(true)} color="#EC4899" icon="🛵" label="Delivery" />
          <ActionButton onClick={() => setShowModalPDV(true)} color="#8B5CF6" icon="💳" label="PDV" />
          <ActionButton onClick={() => setShowModalNotaFiscal(true)} color="#06B6D4" icon="📄" label="Nota Fiscal" />
          <ActionButton onClick={() => setShowModalEstoque(true)} color="#059669" icon="📦" label="Estoque" />
          <ActionButton onClick={() => setShowModalBalanca(true)} color="#D97706" icon="⚖️" label="Balança" />
          <ActionButton onClick={() => setShowModalFuncionarios(true)} color="#6366F1" icon="👥" label="Funcionários" />
          <ActionButton onClick={() => setShowModalClientes(true)} color="#0EA5E9" icon="👤" label="Clientes" />
        </div>
        <div className="mt-3 sm:mt-4 p-2 sm:p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <p className="text-[10px] sm:text-xs text-gray-600 dark:text-gray-400 text-center">
            💡 Dashboard Restaurante — Cardápio, Mesas, Pedidos, Delivery, PDV, NF, Estoque, Balança e Funcionários
          </p>
        </div>
      </div>

      {/* Estatísticas */}
      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
        <StatCard title="Pedidos Hoje" value={estatisticas.pedidos_hoje} icon="📦" cor={loja.cor_primaria} />
        <StatCard title="Mesas" value={estatisticas.mesas_ocupadas} icon="🪑" cor={loja.cor_primaria} />
        <StatCard title="Itens no Cardápio" value={estatisticas.cardapio} icon="📋" cor={loja.cor_primaria} />
        <StatCard title="Faturamento Hoje" value={`R$ ${Number(estatisticas.faturamento).toLocaleString('pt-BR')}`} icon="💰" cor={loja.cor_primaria} />
      </div>

      {/* Pedidos Recentes */}
      <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg">
        <div className="flex items-center justify-between mb-3 sm:mb-4">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Pedidos Recentes</h3>
          <button
            onClick={() => setShowModalPedidos(true)}
            className="text-xs sm:text-sm px-3 sm:px-4 py-2 min-h-[40px] rounded-lg text-white hover:opacity-90 transition-all btn-press shadow-md"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            Ver todos
          </button>
        </div>
        {loadingPedidos ? (
          <AgendamentosListSkeleton count={3} />
        ) : !Array.isArray(pedidosRecentes) || pedidosRecentes.length === 0 ? (
          <EmptyState
            message="Nenhum pedido ainda"
            subMessage="Os pedidos aparecerão aqui"
            actionLabel="Novo Pedido"
            onAction={() => setShowModalPedidos(true)}
            cor={loja.cor_primaria}
            icon="📦"
          />
        ) : (
          <div className="space-y-4">
            {pedidosRecentes.map((pedido) => (
              <PedidoCard key={pedido.id} pedido={pedido} cor={loja.cor_primaria} />
            ))}
          </div>
        )}
      </div>

      {/* Modais */}
      {showModalCardapio && <ModalCardapio loja={loja} onClose={() => setShowModalCardapio(false)} onSuccess={loadDashboard} />}
      {showModalMesas && <ModalMesas loja={loja} onClose={() => setShowModalMesas(false)} onSuccess={loadDashboard} />}
      {showModalPedidos && <ModalPedidos loja={loja} onClose={() => setShowModalPedidos(false)} onSuccess={loadDashboard} />}
      {showModalDelivery && <ModalDelivery loja={loja} onClose={() => setShowModalDelivery(false)} onSuccess={loadDashboard} />}
      {showModalPDV && <ModalPDV loja={loja} onClose={() => setShowModalPDV(false)} onSuccess={loadDashboard} />}
      {showModalNotaFiscal && <ModalNotaFiscal loja={loja} onClose={() => setShowModalNotaFiscal(false)} />}
      {showModalEstoque && <ModalEstoque loja={loja} onClose={() => setShowModalEstoque(false)} />}
      {showModalBalanca && <ModalBalanca loja={loja} onClose={() => setShowModalBalanca(false)} />}
      {showModalFuncionarios && <ModalFuncionarios loja={loja} onClose={() => setShowModalFuncionarios(false)} />}
      {showModalClientes && <ModalClientes loja={loja} onClose={() => setShowModalClientes(false)} />}
    </div>
  );
}
