'use client';

import { useState, useEffect, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';
import { ThemeToggle } from '@/components/ui/ThemeProvider';
import { DashboardSkeleton, AgendamentosListSkeleton } from '@/components/ui/Skeleton';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
  logo?: string;
}

interface EstatisticasRestaurante {
  pedidos_hoje: number;
  mesas_ocupadas: string;
  cardapio: number;
  faturamento: number;
}

interface Categoria {
  id: number;
  nome: string;
  ordem?: number;
}

interface ItemCardapio {
  id: number;
  nome: string;
  descricao: string;
  categoria: number | null;
  preco: string;
  tempo_preparo: number;
  is_disponivel: boolean;
  is_destaque?: boolean;
}

interface Mesa {
  id: number;
  numero: string;
  capacidade: number;
  localizacao?: string;
  status: string;
  is_active: boolean;
}

interface Cliente {
  id: number;
  nome: string;
  email?: string;
  telefone?: string;
}

interface Pedido {
  id: number;
  tipo: string;
  status: string;
  total: string;
  mesa?: number | null;
  cliente?: number | null;
  endereco_entrega?: string | null;
  taxa_entrega?: string;
  created_at: string;
  itens?: { item_cardapio: { nome: string }; quantidade: number; preco_unitario: string }[];
}

interface Funcionario {
  id: number;
  nome: string;
  email?: string;
  telefone?: string;
  cargo: string;
  is_admin?: boolean;
}

const STATUS_MESA = [
  { value: 'livre', label: 'Livre' },
  { value: 'ocupada', label: 'Ocupada' },
  { value: 'reservada', label: 'Reservada' },
  { value: 'manutencao', label: 'Manutenção' }
];

const CARGO_FUNCIONARIO = [
  { value: 'garcom', label: 'Garçom' },
  { value: 'cozinheiro', label: 'Cozinheiro' },
  { value: 'gerente', label: 'Gerente' },
  { value: 'caixa', label: 'Caixa' },
  { value: 'outro', label: 'Outro' }
];

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
    </div>
  );
}

function ActionButton({ onClick, color, icon, label }: { onClick: () => void; color: string; icon: string; label: string }) {
  return (
    <button
      onClick={onClick}
      className="group p-2 sm:p-3 md:p-4 rounded-lg sm:rounded-xl text-white font-semibold transition-all duration-200 transform hover:scale-105 active:scale-95 shadow-md sm:shadow-lg hover:shadow-xl btn-press relative overflow-hidden min-h-[70px] sm:min-h-[80px] md:min-h-[100px]"
      style={{ backgroundColor: color }}
    >
      <div className="absolute inset-0 bg-white/0 group-hover:bg-white/10 transition-colors duration-200" />
      <div className="relative flex flex-col items-center justify-center h-full">
        <div className="text-xl sm:text-2xl md:text-3xl mb-1 sm:mb-2">{icon}</div>
        <div className="text-[10px] sm:text-xs md:text-sm leading-tight text-center">{label}</div>
      </div>
    </button>
  );
}

function StatCard({ title, value, icon, cor }: { title: string; value: string | number; icon: string; cor: string }) {
  return (
    <div className="bg-white dark:bg-gray-800 p-3 sm:p-4 md:p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 card-hover group">
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="text-gray-500 dark:text-gray-400 text-xs sm:text-sm font-medium truncate">{title}</h3>
          <p className="text-xl sm:text-2xl md:text-3xl font-bold mt-1 sm:mt-2 text-gray-900 dark:text-white truncate" style={{ color: cor }}>
            {value}
          </p>
        </div>
        <div className="w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-lg sm:rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${cor}20` }}>
          <span className="text-xl sm:text-2xl md:text-3xl">{icon}</span>
        </div>
      </div>
    </div>
  );
}

function PedidoCard({ pedido, cor }: { pedido: Pedido; cor: string }) {
  const tipoLabel = pedido.tipo === 'delivery' ? '🛵 Delivery' : pedido.tipo === 'retirada' ? '📦 Retirada' : '🪑 Local';
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3 sm:p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-all gap-3 sm:gap-4 card-hover">
      <div className="flex items-center space-x-3 sm:space-x-4">
        <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl flex items-center justify-center text-white font-bold flex-shrink-0 shadow-md" style={{ backgroundColor: cor }}>
          #{pedido.id}
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-gray-900 dark:text-white text-sm sm:text-base">Pedido #{pedido.id}</p>
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">{tipoLabel} • {pedido.status}</p>
        </div>
      </div>
      <p className="font-bold text-base sm:text-lg" style={{ color: cor }}>
        R$ {Number(pedido.total).toLocaleString('pt-BR')}
      </p>
    </div>
  );
}

function EmptyState({ message, subMessage, actionLabel, onAction, cor, icon = '📋' }: {
  message: string;
  subMessage: string;
  actionLabel: string;
  onAction: () => void;
  cor: string;
  icon?: string;
}) {
  return (
    <div className="text-center py-8 sm:py-12 px-4">
      <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
        <span className="text-2xl sm:text-3xl">{icon}</span>
      </div>
      <p className="text-base sm:text-lg mb-1 sm:mb-2 text-gray-700 dark:text-gray-300">{message}</p>
      <p className="text-xs sm:text-sm mb-4 text-gray-500 dark:text-gray-500">{subMessage}</p>
      <button
        onClick={onAction}
        className="px-4 sm:px-6 py-2.5 sm:py-3 min-h-[44px] rounded-xl text-white hover:opacity-90 transition-all btn-press shadow-lg text-sm sm:text-base active:scale-95"
        style={{ backgroundColor: cor }}
      >
        {actionLabel}
      </button>
    </div>
  );
}

// ——— Modal Cardápio (Categorias + Itens) ———
function ModalCardapio({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const toast = useToast();
  const [aba, setAba] = useState<'categorias' | 'itens'>('categorias');
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [itens, setItens] = useState<ItemCardapio[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFormCat, setShowFormCat] = useState(false);
  const [showFormItem, setShowFormItem] = useState(false);
  const [editCatId, setEditCatId] = useState<number | null>(null);
  const [editItemId, setEditItemId] = useState<number | null>(null);
  const [formCat, setFormCat] = useState({ nome: '', ordem: '0' });
  const [formItem, setFormItem] = useState({
    nome: '', descricao: '', categoria: '', preco: '', tempo_preparo: '15',
    is_disponivel: true
  });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [catRes, itensRes] = await Promise.all([
        clinicaApiClient.get<Categoria[] | { results?: Categoria[] }>('/restaurante/categorias/'),
        clinicaApiClient.get<ItemCardapio[] | { results?: ItemCardapio[] }>('/restaurante/cardapio/')
      ]);
      setCategorias(Array.isArray(catRes.data) ? catRes.data : (catRes.data as { results?: Categoria[] })?.results ?? []);
      setItens(Array.isArray(itensRes.data) ? itensRes.data : (itensRes.data as { results?: ItemCardapio[] })?.results ?? []);
    } catch (e) {
      console.error(e);
      toast.error('Erro ao carregar cardápio');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const handleSaveCategoria = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = { nome: formCat.nome, ordem: parseInt(formCat.ordem, 10) || 0 };
      if (editCatId) {
        await clinicaApiClient.put(`/restaurante/categorias/${editCatId}/`, payload);
        toast.success('Categoria atualizada');
      } else {
        await clinicaApiClient.post('/restaurante/categorias/', payload);
        toast.success('Categoria criada');
      }
      setShowFormCat(false);
      setEditCatId(null);
      setFormCat({ nome: '', ordem: '0' });
      load();
      onSuccess?.();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveItem = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        nome: formItem.nome,
        descricao: formItem.descricao,
        categoria: formItem.categoria ? parseInt(formItem.categoria, 10) : null,
        preco: formItem.preco,
        tempo_preparo: parseInt(formItem.tempo_preparo, 10) || 15,
        is_disponivel: formItem.is_disponivel
      };
      if (editItemId) {
        await clinicaApiClient.put(`/restaurante/cardapio/${editItemId}/`, payload);
        toast.success('Item atualizado');
      } else {
        await clinicaApiClient.post('/restaurante/cardapio/', payload);
        toast.success('Item criado');
      }
      setShowFormItem(false);
      setEditItemId(null);
      setFormItem({ nome: '', descricao: '', categoria: '', preco: '', tempo_preparo: '15', is_disponivel: true });
      load();
      onSuccess?.();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCategoria = async (id: number, nome: string) => {
    if (!confirm(`Excluir categoria "${nome}"?`)) return;
    try {
      await clinicaApiClient.delete(`/restaurante/categorias/${id}/`);
      toast.success('Categoria excluída');
      load();
      onSuccess?.();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Erro ao excluir');
    }
  };

  const handleDeleteItem = async (id: number, nome: string) => {
    if (!confirm(`Excluir item "${nome}"?`)) return;
    try {
      await clinicaApiClient.delete(`/restaurante/cardapio/${id}/`);
      toast.success('Item excluído');
      load();
      onSuccess?.();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Erro ao excluir');
    }
  };

  if (showFormCat) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full shadow-xl">
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
            {editCatId ? 'Editar' : 'Nova'} Categoria
          </h3>
          <form onSubmit={handleSaveCategoria} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
              <input type="text" value={formCat.nome} onChange={e => setFormCat(f => ({ ...f, nome: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Ex: Bebidas" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Ordem</label>
              <input type="number" value={formCat.ordem} onChange={e => setFormCat(f => ({ ...f, ordem: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div className="flex gap-2 justify-end">
              <button type="button" onClick={() => { setShowFormCat(false); setEditCatId(null); }} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300">Cancelar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Salvar'}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  if (showFormItem) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-xl">
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
            {editItemId ? 'Editar' : 'Novo'} Item do Cardápio
          </h3>
          <form onSubmit={handleSaveItem} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
              <input type="text" value={formItem.nome} onChange={e => setFormItem(f => ({ ...f, nome: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Ex: Refrigerante" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descrição</label>
              <textarea value={formItem.descricao} onChange={e => setFormItem(f => ({ ...f, descricao: e.target.value }))} rows={2} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Categoria</label>
              <select value={formItem.categoria} onChange={e => setFormItem(f => ({ ...f, categoria: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                <option value="">Nenhuma</option>
                {categorias.map(c => <option key={c.id} value={c.id}>{c.nome}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Preço (R$) *</label>
                <input type="text" value={formItem.preco} onChange={e => setFormItem(f => ({ ...f, preco: e.target.value }))} required placeholder="0.00" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tempo preparo (min)</label>
                <input type="number" value={formItem.tempo_preparo} onChange={e => setFormItem(f => ({ ...f, tempo_preparo: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="disp" checked={formItem.is_disponivel} onChange={e => setFormItem(f => ({ ...f, is_disponivel: e.target.checked }))} />
              <label htmlFor="disp" className="text-sm text-gray-700 dark:text-gray-300">Disponível</label>
            </div>
            <div className="flex gap-2 justify-end">
              <button type="button" onClick={() => { setShowFormItem(false); setEditItemId(null); }} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300">Cancelar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Salvar'}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-4xl w-full max-h-[85vh] overflow-y-auto shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>📋 Cardápio</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400">✕</button>
        </div>
        <div className="flex gap-2 mb-4">
          <button onClick={() => setAba('categorias')} className={`px-4 py-2 rounded-lg font-medium ${aba === 'categorias' ? 'text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`} style={aba === 'categorias' ? { backgroundColor: loja.cor_primaria } : {}}>Categorias</button>
          <button onClick={() => setAba('itens')} className={`px-4 py-2 rounded-lg font-medium ${aba === 'itens' ? 'text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`} style={aba === 'itens' ? { backgroundColor: loja.cor_primaria } : {}}>Itens</button>
        </div>
        {loading ? (
          <p className="text-center text-gray-500 dark:text-gray-400 py-8">Carregando...</p>
        ) : aba === 'categorias' ? (
          <div className="space-y-2">
            {categorias.length === 0 ? <p className="text-gray-500 dark:text-gray-400 py-4">Nenhuma categoria. Clique em Nova Categoria.</p> : categorias.map(c => (
              <div key={c.id} className="flex items-center justify-between p-3 border dark:border-gray-600 rounded-lg">
                <span className="font-medium text-gray-900 dark:text-white">{c.nome}</span>
                <div className="flex gap-2">
                  <button onClick={() => { setEditCatId(c.id); setFormCat({ nome: c.nome, ordem: String(c.ordem ?? 0) }); setShowFormCat(true); }} className="px-3 py-1 text-sm rounded-lg text-white" style={{ backgroundColor: loja.cor_primaria }}>Editar</button>
                  <button onClick={() => handleDeleteCategoria(c.id, c.nome)} className="px-3 py-1 text-sm bg-red-600 text-white rounded-lg">Excluir</button>
                </div>
              </div>
            ))}
            <button onClick={() => { setFormCat({ nome: '', ordem: '0' }); setShowFormCat(true); }} className="w-full py-2 border border-dashed border-gray-400 dark:border-gray-500 rounded-lg text-gray-600 dark:text-gray-400">+ Nova Categoria</button>
          </div>
        ) : (
          <div className="space-y-2">
            {itens.length === 0 ? <p className="text-gray-500 dark:text-gray-400 py-4">Nenhum item. Clique em Novo Item.</p> : itens.map(i => (
              <div key={i.id} className="flex items-center justify-between p-3 border dark:border-gray-600 rounded-lg">
                <div>
                  <span className="font-medium text-gray-900 dark:text-white">{i.nome}</span>
                  <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">R$ {Number(i.preco).toLocaleString('pt-BR')}</span>
                  {!i.is_disponivel && <span className="ml-2 text-xs text-red-600">(indisponível)</span>}
                </div>
                <div className="flex gap-2">
                  <button onClick={() => { setEditItemId(i.id); setFormItem({ nome: i.nome, descricao: i.descricao || '', categoria: i.categoria ? String(i.categoria) : '', preco: i.preco, tempo_preparo: String(i.tempo_preparo), is_disponivel: i.is_disponivel }); setShowFormItem(true); }} className="px-3 py-1 text-sm rounded-lg text-white" style={{ backgroundColor: loja.cor_primaria }}>Editar</button>
                  <button onClick={() => handleDeleteItem(i.id, i.nome)} className="px-3 py-1 text-sm bg-red-600 text-white rounded-lg">Excluir</button>
                </div>
              </div>
            ))}
            <button onClick={() => { setFormItem({ nome: '', descricao: '', categoria: '', preco: '', tempo_preparo: '15', is_disponivel: true }); setShowFormItem(true); }} className="w-full py-2 border border-dashed border-gray-400 dark:border-gray-500 rounded-lg text-gray-600 dark:text-gray-400">+ Novo Item</button>
          </div>
        )}
      </div>
    </div>
  );
}

// ——— Modal Mesas ———
function ModalMesas({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const toast = useToast();
  const [mesas, setMesas] = useState<Mesa[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState({ numero: '', capacidade: '4', localizacao: '', status: 'livre' });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await clinicaApiClient.get<Mesa[] | { results?: Mesa[] }>('/restaurante/mesas/');
      setMesas(Array.isArray(res.data) ? res.data : (res.data as { results?: Mesa[] })?.results ?? []);
    } catch (e) {
      toast.error('Erro ao carregar mesas');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = { numero: form.numero, capacidade: parseInt(form.capacidade, 10) || 4, localizacao: form.localizacao || null, status: form.status };
      if (editId) {
        await clinicaApiClient.put(`/restaurante/mesas/${editId}/`, payload);
        toast.success('Mesa atualizada');
      } else {
        await clinicaApiClient.post('/restaurante/mesas/', payload);
        toast.success('Mesa criada');
      }
      setShowForm(false);
      setEditId(null);
      setForm({ numero: '', capacidade: '4', localizacao: '', status: 'livre' });
      load();
      onSuccess?.();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number, numero: string) => {
    if (!confirm(`Excluir mesa ${numero}?`)) return;
    try {
      await clinicaApiClient.delete(`/restaurante/mesas/${id}/`);
      toast.success('Mesa excluída');
      load();
      onSuccess?.();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Erro ao excluir');
    }
  };

  if (showForm) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full shadow-xl">
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>{editId ? 'Editar' : 'Nova'} Mesa</h3>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Número *</label>
              <input type="text" value={form.numero} onChange={e => setForm(f => ({ ...f, numero: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Ex: 1" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Capacidade *</label>
              <input type="number" value={form.capacidade} onChange={e => setForm(f => ({ ...f, capacidade: e.target.value }))} min={1} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Localização</label>
              <input type="text" value={form.localizacao} onChange={e => setForm(f => ({ ...f, localizacao: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Salão, Varanda" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
              <select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                {STATUS_MESA.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            </div>
            <div className="flex gap-2 justify-end">
              <button type="button" onClick={() => { setShowForm(false); setEditId(null); }} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg">Cancelar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Salvar'}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-3xl w-full max-h-[85vh] overflow-y-auto shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>🪑 Mesas</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        {loading ? <p className="text-center text-gray-500 py-8">Carregando...</p> : (
          <div className="space-y-2">
            {mesas.length === 0 ? <p className="text-gray-500 py-4">Nenhuma mesa. Clique em Nova Mesa.</p> : mesas.map(m => (
              <div key={m.id} className="flex items-center justify-between p-3 border dark:border-gray-600 rounded-lg">
                <div>
                  <span className="font-medium text-gray-900 dark:text-white">Mesa {m.numero}</span>
                  <span className="ml-2 text-sm text-gray-500">({m.capacidade} pessoas)</span>
                  <span className="ml-2 px-2 py-0.5 rounded text-xs font-medium bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300">{STATUS_MESA.find(s => s.value === m.status)?.label ?? m.status}</span>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => { setEditId(m.id); setForm({ numero: m.numero, capacidade: String(m.capacidade), localizacao: m.localizacao || '', status: m.status }); setShowForm(true); }} className="px-3 py-1 text-sm rounded-lg text-white" style={{ backgroundColor: loja.cor_primaria }}>Editar</button>
                  <button onClick={() => handleDelete(m.id, m.numero)} className="px-3 py-1 text-sm bg-red-600 text-white rounded-lg">Excluir</button>
                </div>
              </div>
            ))}
            <button onClick={() => { setForm({ numero: '', capacidade: '4', localizacao: '', status: 'livre' }); setShowForm(true); }} className="w-full py-2 border border-dashed border-gray-400 rounded-lg text-gray-600">+ Nova Mesa</button>
          </div>
        )}
      </div>
    </div>
  );
}

// ——— Modal Pedidos (listar + novo) ———
function ModalPedidos({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const toast = useToast();
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [mesas, setMesas] = useState<Mesa[]>([]);
  const [itens, setItens] = useState<ItemCardapio[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNovo, setShowNovo] = useState(false);
  const [form, setForm] = useState({ tipo: 'local' as 'local' | 'delivery' | 'retirada', cliente: '', mesa: '', endereco_entrega: '', taxa_entrega: '0' });
  const [itensPedido, setItensPedido] = useState<{ item_id: number; quantidade: number; preco: string }[]>([]);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [pRes, cRes, mRes, iRes] = await Promise.all([
        clinicaApiClient.get<Pedido[] | { results?: Pedido[] }>('/restaurante/pedidos/'),
        clinicaApiClient.get<Cliente[] | { results?: Cliente[] }>('/restaurante/clientes/'),
        clinicaApiClient.get<Mesa[] | { results?: Mesa[] }>('/restaurante/mesas/'),
        clinicaApiClient.get<ItemCardapio[] | { results?: ItemCardapio[] }>('/restaurante/cardapio/')
      ]);
      setPedidos(Array.isArray(pRes.data) ? pRes.data : (pRes.data as { results?: Pedido[] })?.results ?? []);
      setClientes(Array.isArray(cRes.data) ? cRes.data : (cRes.data as { results?: Cliente[] })?.results ?? []);
      setMesas(Array.isArray(mRes.data) ? mRes.data : (mRes.data as { results?: Mesa[] })?.results ?? []);
      setItens(Array.isArray(iRes.data) ? iRes.data : (iRes.data as { results?: ItemCardapio[] })?.results ?? []);
    } catch (e) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const addItem = (item: ItemCardapio) => {
    const exist = itensPedido.find(x => x.item_id === item.id);
    if (exist) setItensPedido(prev => prev.map(x => x.item_id === item.id ? { ...x, quantidade: x.quantidade + 1 } : x));
    else setItensPedido(prev => [...prev, { item_id: item.id, quantidade: 1, preco: item.preco }]);
  };

  const removeItem = (itemId: number) => setItensPedido(prev => prev.filter(x => x.item_id !== itemId));

  const totalPedido = itensPedido.reduce((s, x) => s + Number(x.preco) * x.quantidade, 0) + (form.tipo === 'delivery' ? Number(form.taxa_entrega || 0) : 0);

  const handleCriarPedido = async (e: React.FormEvent) => {
    e.preventDefault();
    if (itensPedido.length === 0) { toast.error('Adicione pelo menos um item'); return; }
    setSaving(true);
    try {
      const subtotal = itensPedido.reduce((s, x) => s + Number(x.preco) * x.quantidade, 0);
      const taxa = form.tipo === 'delivery' ? Number(form.taxa_entrega || 0) : 0;
      const total = subtotal + taxa;
      const numeroPedido = `PED-${Date.now()}`;
      const payloadPedido = {
        numero_pedido: numeroPedido,
        status: 'pendente',
        subtotal: String(subtotal.toFixed(2)),
        desconto: '0.00',
        total: String(total.toFixed(2)),
        tipo: form.tipo,
        cliente: form.cliente ? parseInt(form.cliente, 10) : null,
        mesa: form.tipo === 'local' && form.mesa ? parseInt(form.mesa, 10) : null,
        endereco_entrega: form.tipo === 'delivery' ? form.endereco_entrega : null,
        taxa_entrega: form.tipo === 'delivery' ? (form.taxa_entrega || '0') : '0',
        taxa_servico: '0.00'
      };
      const res = await clinicaApiClient.post<{ id: number }>('/restaurante/pedidos/', payloadPedido);
      const pedidoId = res.data.id;
      for (const x of itensPedido) {
        const sub = Number(x.preco) * x.quantidade;
        await clinicaApiClient.post('/restaurante/itens-pedido/', {
          pedido: pedidoId,
          item_cardapio: x.item_id,
          quantidade: x.quantidade,
          preco_unitario: x.preco,
          subtotal: String(sub.toFixed(2))
        });
      }
      toast.success('Pedido criado');
      setShowNovo(false);
      setForm({ tipo: 'local', cliente: '', mesa: '', endereco_entrega: '', taxa_entrega: '0' });
      setItensPedido([]);
      load();
      onSuccess?.();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Erro ao criar pedido');
    } finally {
      setSaving(false);
    }
  };

  if (showNovo) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>📦 Novo Pedido</h3>
          <form onSubmit={handleCriarPedido} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tipo</label>
              <select value={form.tipo} onChange={e => setForm(f => ({ ...f, tipo: e.target.value as 'local' | 'delivery' | 'retirada' }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                <option value="local">Local (mesa)</option>
                <option value="delivery">Delivery</option>
                <option value="retirada">Retirada</option>
              </select>
            </div>
            {form.tipo === 'local' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mesa</label>
                <select value={form.mesa} onChange={e => setForm(f => ({ ...f, mesa: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                  <option value="">—</option>
                  {mesas.map(m => <option key={m.id} value={m.id}>Mesa {m.numero}</option>)}
                </select>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cliente (opcional)</label>
              <select value={form.cliente} onChange={e => setForm(f => ({ ...f, cliente: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                <option value="">—</option>
                {clientes.map(c => <option key={c.id} value={c.id}>{c.nome}</option>)}
              </select>
            </div>
            {form.tipo === 'delivery' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Endereço de entrega</label>
                  <textarea value={form.endereco_entrega} onChange={e => setForm(f => ({ ...f, endereco_entrega: e.target.value }))} rows={2} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Taxa entrega (R$)</label>
                  <input type="text" value={form.taxa_entrega} onChange={e => setForm(f => ({ ...f, taxa_entrega: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="0.00" />
                </div>
              </>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Itens do pedido</label>
              <div className="flex flex-wrap gap-2 mb-2">
                {itens.filter(i => i.is_disponivel).map(i => (
                  <button type="button" key={i.id} onClick={() => addItem(i)} className="px-3 py-2 rounded-lg border dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 text-sm">
                    {i.nome} — R$ {Number(i.preco).toLocaleString('pt-BR')}
                  </button>
                ))}
              </div>
              <ul className="space-y-1">
                {itensPedido.map(x => {
                  const item = itens.find(i => i.id === x.item_id);
                  return item ? (
                    <li key={x.item_id} className="flex justify-between items-center">
                      <span>{item.nome} x{x.quantidade}</span>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">R$ {(Number(x.preco) * x.quantidade).toLocaleString('pt-BR')}</span>
                        <button type="button" onClick={() => removeItem(x.item_id)} className="text-red-600 text-sm">Remover</button>
                      </div>
                    </li>
                  ) : null;
                })}
              </ul>
            </div>
            <p className="font-bold text-lg">Total: R$ {totalPedido.toLocaleString('pt-BR')}</p>
            <div className="flex gap-2 justify-end">
              <button type="button" onClick={() => setShowNovo(false)} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg">Cancelar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Criar Pedido'}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-4xl w-full max-h-[85vh] overflow-y-auto shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>📦 Pedidos</h3>
          <div className="flex gap-2">
            <button onClick={() => setShowNovo(true)} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo</button>
            <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
          </div>
        </div>
        {loading ? <p className="text-center text-gray-500 py-8">Carregando...</p> : (
          <div className="space-y-2">
            {pedidos.length === 0 ? <p className="text-gray-500 py-4">Nenhum pedido.</p> : pedidos.map(p => (
              <div key={p.id} className="flex items-center justify-between p-3 border dark:border-gray-600 rounded-lg">
                <div>
                  <span className="font-medium text-gray-900 dark:text-white">#{p.id}</span>
                  <span className="ml-2 text-sm text-gray-500">{p.tipo} • {p.status}</span>
                </div>
                <span className="font-bold" style={{ color: loja.cor_primaria }}>R$ {Number(p.total).toLocaleString('pt-BR')}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ——— Modal Delivery (pedidos tipo delivery) ———
function ModalDelivery({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const toast = useToast();
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await clinicaApiClient.get<Pedido[] | { results?: Pedido[] }>('/restaurante/pedidos/', { params: { tipo: 'delivery' } });
      const list = Array.isArray(res.data) ? res.data : (res.data as { results?: Pedido[] })?.results ?? [];
      setPedidos(list);
    } catch (e) {
      toast.error('Erro ao carregar pedidos de delivery');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-3xl w-full max-h-[85vh] overflow-y-auto shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>🛵 Controle de Delivery</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        {loading ? <p className="text-center text-gray-500 py-8">Carregando...</p> : (
          <div className="space-y-3">
            {pedidos.length === 0 ? <p className="text-gray-500 py-4">Nenhum pedido de delivery no momento.</p> : pedidos.map(p => (
              <div key={p.id} className="p-4 border dark:border-gray-600 rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-bold text-gray-900 dark:text-white">Pedido #{p.id}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Status: {p.status}</p>
                    {p.endereco_entrega && <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">📍 {p.endereco_entrega}</p>}
                    <p className="text-sm font-semibold mt-1">R$ {Number(p.total).toLocaleString('pt-BR')}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ——— Modal PDV (vendas rápidas) ———
function ModalPDV({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const toast = useToast();
  const [itens, setItens] = useState<ItemCardapio[]>([]);
  const [carrinho, setCarrinho] = useState<{ item: ItemCardapio; qtd: number }[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await clinicaApiClient.get<ItemCardapio[] | { results?: ItemCardapio[] }>('/restaurante/cardapio/');
      setItens(Array.isArray(res.data) ? res.data : (res.data as { results?: ItemCardapio[] })?.results ?? []);
    } catch (e) {
      toast.error('Erro ao carregar cardápio');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const add = (item: ItemCardapio) => {
    const exist = carrinho.find(x => x.item.id === item.id);
    if (exist) setCarrinho(prev => prev.map(x => x.item.id === item.id ? { ...x, qtd: x.qtd + 1 } : x));
    else setCarrinho(prev => [...prev, { item, qtd: 1 }]);
  };

  const remove = (itemId: number) => setCarrinho(prev => prev.filter(x => x.item.id !== itemId));

  const total = carrinho.reduce((s, x) => s + Number(x.item.preco) * x.qtd, 0);

  const finalizar = async () => {
    if (carrinho.length === 0) { toast.error('Adicione itens ao carrinho'); return; }
    try {
      const subtotal = carrinho.reduce((s, x) => s + Number(x.item.preco) * x.qtd, 0);
      const payloadPedido = {
        numero_pedido: `PDV-${Date.now()}`,
        status: 'pendente',
        subtotal: String(subtotal.toFixed(2)),
        desconto: '0.00',
        total: String(subtotal.toFixed(2)),
        tipo: 'local',
        taxa_servico: '0.00',
        taxa_entrega: '0.00'
      };
      const res = await clinicaApiClient.post<{ id: number }>('/restaurante/pedidos/', payloadPedido);
      const pedidoId = res.data.id;
      for (const x of carrinho) {
        const sub = Number(x.item.preco) * x.qtd;
        await clinicaApiClient.post('/restaurante/itens-pedido/', {
          pedido: pedidoId,
          item_cardapio: x.item.id,
          quantidade: x.qtd,
          preco_unitario: x.item.preco,
          subtotal: String(sub.toFixed(2))
        });
      }
      toast.success('Venda registrada');
      setCarrinho([]);
      onSuccess?.();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Erro ao registrar venda');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>💳 PDV - Vendas</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Cardápio — clique para adicionar</p>
            {loading ? <p className="text-gray-500">Carregando...</p> : (
              <div className="flex flex-wrap gap-2 max-h-[300px] overflow-y-auto">
                {itens.filter(i => i.is_disponivel).map(i => (
                  <button type="button" key={i.id} onClick={() => add(i)} className="px-3 py-2 rounded-lg border dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 text-left text-sm">
                    {i.nome} — R$ {Number(i.preco).toLocaleString('pt-BR')}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Carrinho</p>
            <ul className="space-y-2 mb-4">
              {carrinho.map(x => (
                <li key={x.item.id} className="flex justify-between items-center">
                  <span>{x.item.nome} x{x.qtd}</span>
                  <div className="flex items-center gap-2">
                    <span>R$ {(Number(x.item.preco) * x.qtd).toLocaleString('pt-BR')}</span>
                    <button type="button" onClick={() => remove(x.item.id)} className="text-red-600 text-sm">Remover</button>
                  </div>
                </li>
              ))}
            </ul>
            <p className="font-bold text-lg mb-2">Total: R$ {total.toLocaleString('pt-BR')}</p>
            <button onClick={finalizar} disabled={carrinho.length === 0} className="w-full py-3 rounded-lg text-white font-bold min-h-[44px] disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>Finalizar venda</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ——— Modal Nota Fiscal (entrada — placeholder) ———
function ModalNotaFiscal({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-lg w-full shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>📄 Entrada de Nota Fiscal</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        <p className="text-gray-600 dark:text-gray-400 mb-4">Registro de entrada de notas fiscais de compras. Em breve: upload de XML, vinculação a fornecedores e estoque.</p>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Número da NF</label>
            <input type="text" placeholder="Ex: 000.000.000" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" readOnly />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fornecedor</label>
            <input type="text" placeholder="Nome do fornecedor" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" readOnly />
          </div>
          <p className="text-xs text-amber-600 dark:text-amber-400">Módulo em desenvolvimento. Backend será integrado em breve.</p>
        </div>
        <div className="flex justify-end mt-4">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>Fechar</button>
        </div>
      </div>
    </div>
  );
}

// ——— Modal Estoque (placeholder) ———
function ModalEstoque({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-lg w-full shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>📦 Controle de Estoque</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        <p className="text-gray-600 dark:text-gray-400 mb-4">Controle de ingredientes e produtos. Em breve: cadastro de itens, entradas/saídas e alertas de mínimo.</p>
        <p className="text-xs text-amber-600 dark:text-amber-400">Módulo em desenvolvimento. Backend será integrado em breve.</p>
        <div className="flex justify-end mt-4">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>Fechar</button>
        </div>
      </div>
    </div>
  );
}

// ——— Modal Balança (placeholder) ———
function ModalBalanca({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-lg w-full shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>⚖️ Balança</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        <p className="text-gray-600 dark:text-gray-400 mb-4">Integração com balança para pesar comida (por kg). Em breve: configuração de dispositivos e registro de peso por item.</p>
        <p className="text-xs text-amber-600 dark:text-amber-400">Módulo em desenvolvimento. Backend será integrado em breve.</p>
        <div className="flex justify-end mt-4">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>Fechar</button>
        </div>
      </div>
    </div>
  );
}

// ——— Modal Funcionários ———
function ModalFuncionarios({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [lista, setLista] = useState<Funcionario[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState({ nome: '', email: '', telefone: '', cargo: 'garcom' });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await clinicaApiClient.get<Funcionario[] | { results?: Funcionario[] }>('/restaurante/funcionarios/');
      setLista(Array.isArray(res.data) ? res.data : (res.data as { results?: Funcionario[] })?.results ?? []);
    } catch (e) {
      toast.error('Erro ao carregar funcionários');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { load(); }, [load]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editId) {
        await clinicaApiClient.put(`/restaurante/funcionarios/${editId}/`, form);
        toast.success('Funcionário atualizado');
      } else {
        await clinicaApiClient.post('/restaurante/funcionarios/', form);
        toast.success('Funcionário cadastrado');
      }
      setShowForm(false);
      setEditId(null);
      setForm({ nome: '', email: '', telefone: '', cargo: 'garcom' });
      load();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number, nome: string) => {
    if (!confirm(`Excluir funcionário "${nome}"?`)) return;
    try {
      await clinicaApiClient.delete(`/restaurante/funcionarios/${id}/`);
      toast.success('Funcionário excluído');
      load();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Erro ao excluir');
    }
  };

  if (showForm) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full shadow-xl">
          <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>{editId ? 'Editar' : 'Novo'} Funcionário</h3>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
              <input type="text" value={form.nome} onChange={e => setForm(f => ({ ...f, nome: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
              <input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label>
              <input type="tel" value={form.telefone} onChange={e => setForm(f => ({ ...f, telefone: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cargo</label>
              <select value={form.cargo} onChange={e => setForm(f => ({ ...f, cargo: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                {CARGO_FUNCIONARIO.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            <div className="flex gap-2 justify-end">
              <button type="button" onClick={() => { setShowForm(false); setEditId(null); }} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg">Cancelar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Salvar'}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-3xl w-full max-h-[85vh] overflow-y-auto shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>👥 Funcionários</h3>
          <div className="flex gap-2">
            <button onClick={() => { setForm({ nome: '', email: '', telefone: '', cargo: 'garcom' }); setShowForm(true); }} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo</button>
            <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
          </div>
        </div>
        {loading ? <p className="text-center text-gray-500 py-8">Carregando...</p> : (
          <div className="space-y-2">
            {lista.length === 0 ? <p className="text-gray-500 py-4">Nenhum funcionário.</p> : lista.map(f => (
              <div key={f.id} className="flex items-center justify-between p-3 border dark:border-gray-600 rounded-lg">
                <div>
                  <span className="font-medium text-gray-900 dark:text-white">{f.nome}</span>
                  <span className="ml-2 px-2 py-0.5 rounded text-xs bg-gray-200 dark:bg-gray-700">{CARGO_FUNCIONARIO.find(c => c.value === f.cargo)?.label ?? f.cargo}</span>
                  {f.email && <p className="text-sm text-gray-500">{f.email}</p>}
                </div>
                <div className="flex gap-2">
                  <button onClick={() => { setEditId(f.id); setForm({ nome: f.nome, email: f.email || '', telefone: f.telefone || '', cargo: f.cargo }); setShowForm(true); }} className="px-3 py-1 text-sm rounded-lg text-white" style={{ backgroundColor: loja.cor_primaria }}>Editar</button>
                  {!f.is_admin && <button onClick={() => handleDelete(f.id, f.nome)} className="px-3 py-1 text-sm bg-red-600 text-white rounded-lg">Excluir</button>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
