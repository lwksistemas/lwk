'use client';

import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import apiClient from '@/lib/api-client';
import { extractArrayData, formatApiError } from '@/lib/api-helpers';
import { ResumoCard } from '@/components/financeiro/ResumoCard';
import { TransacaoItem } from '@/components/financeiro/TransacaoItem';
import { FORMAS_PAGAMENTO, STATUS_OPTIONS } from '@/lib/financeiro-helpers';
import type { Categoria, Transacao, ResumoFinanceiro, TransacaoFormData, TabFinanceiro } from '@/types/financeiro';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

interface ModalFinanceiroProps {
  loja: LojaInfo;
  onClose: () => void;
}

const INITIAL_FORM_DATA: TransacaoFormData = {
  tipo: 'receita',
  descricao: '',
  categoria: '',
  valor: '',
  data_vencimento: new Date().toISOString().split('T')[0],
  status: 'pendente',
  forma_pagamento: '',
  observacoes: ''
};

export function ModalFinanceiro({ loja, onClose }: ModalFinanceiroProps) {
  // Estados
  const [activeTab, setActiveTab] = useState<TabFinanceiro>('resumo');
  const [loading, setLoading] = useState(true);
  const [resumo, setResumo] = useState<ResumoFinanceiro | null>(null);
  const [transacoes, setTransacoes] = useState<Transacao[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<Transacao | null>(null);
  const [formData, setFormData] = useState<TransacaoFormData>(INITIAL_FORM_DATA);

  // Carregar dados ao montar e ao trocar de tab
  useEffect(() => {
    carregarDados();
  }, [activeTab]);

  /**
   * Carrega dados da API (DRY - função centralizada)
   */
  const carregarDados = async () => {
    try {
      setLoading(true);
      
      // Carregar resumo
      const resumoResponse = await apiClient.get('/clinica/transacoes/resumo/');
      setResumo(resumoResponse.data);
      
      // Carregar categorias
      const categoriasResponse = await apiClient.get('/clinica/categorias-financeiras/');
      setCategorias(extractArrayData<Categoria>(categoriasResponse));
      
      // Carregar transações se necessário
      if (activeTab === 'receitas' || activeTab === 'despesas') {
        const tipo = activeTab === 'receitas' ? 'receita' : 'despesa';
        const transacoesResponse = await apiClient.get(`/clinica/transacoes/?tipo=${tipo}`);
        setTransacoes(extractArrayData<Transacao>(transacoesResponse));
      }
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      alert(formatApiError(error));
    } finally {
      setLoading(false);
    }
  };

  /**
   * Submete formulário (criar ou editar)
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const payload = {
        ...formData,
        valor: parseFloat(formData.valor),
        categoria: parseInt(formData.categoria)
      };

      if (editando) {
        await apiClient.put(`/clinica/transacoes/${editando.id}/`, payload);
      } else {
        await apiClient.post('/clinica/transacoes/', payload);
      }
      
      await carregarDados();
      handleCloseForm();
    } catch (error) {
      console.error('Erro ao salvar transação:', error);
      alert(formatApiError(error));
    }
  };

  /**
   * Marca transação como paga
   */
  const handleMarcarComoPago = async (id: number) => {
    const forma_pagamento = prompt('Forma de pagamento:\n\n' + 
      FORMAS_PAGAMENTO.map(f => `- ${f.label}`).join('\n') + 
      '\n\nDigite o valor (ex: pix):');
    
    if (!forma_pagamento) return;
    
    try {
      await apiClient.post(`/clinica/transacoes/${id}/marcar_como_pago/`, {
        forma_pagamento: forma_pagamento.toLowerCase().replace(/\s/g, '_')
      });
      await carregarDados();
    } catch (error) {
      console.error('Erro ao marcar como pago:', error);
      alert(formatApiError(error));
    }
  };

  /**
   * Exclui transação
   */
  const handleExcluir = async (id: number, descricao: string) => {
    if (!confirm(`Deseja excluir a transação "${descricao}"?`)) return;
    
    try {
      await apiClient.delete(`/clinica/transacoes/${id}/`);
      await carregarDados();
    } catch (error) {
      console.error('Erro ao excluir transação:', error);
      alert(formatApiError(error));
    }
  };

  /**
   * Fecha formulário e reseta estado
   */
  const handleCloseForm = () => {
    setShowForm(false);
    setEditando(null);
    setFormData(INITIAL_FORM_DATA);
  };

  /**
   * Filtra categorias por tipo
   */
  const categoriasDisponiveis = categorias.filter(
    c => c.tipo === formData.tipo && c.is_active
  );

  // Renderizar formulário
  if (showForm) {
    return (
      <Modal isOpen={true} onClose={handleCloseForm} maxWidth="3xl">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
            {editando ? '✏️ Editar Transação' : '➕ Nova Transação'}
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Tipo */}
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Tipo *</label>
                <select
                  value={formData.tipo}
                  onChange={(e) => setFormData({ ...formData, tipo: e.target.value as 'receita' | 'despesa', categoria: '' })}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  required
                >
                  <option value="receita">💰 Receita</option>
                  <option value="despesa">💸 Despesa</option>
                </select>
              </div>

              {/* Categoria */}
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Categoria *</label>
                <select
                  value={formData.categoria}
                  onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  required
                >
                  <option value="">Selecione...</option>
                  {categoriasDisponiveis.map(c => (
                    <option key={c.id} value={c.id}>{c.nome}</option>
                  ))}
                </select>
              </div>

              {/* Descrição */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Descrição *</label>
                <input
                  type="text"
                  value={formData.descricao}
                  onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  placeholder="Ex: Pagamento de consulta"
                  required
                />
              </div>

              {/* Valor */}
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Valor *</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.valor}
                  onChange={(e) => setFormData({ ...formData, valor: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  placeholder="0.00"
                  required
                />
              </div>

              {/* Data de Vencimento */}
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Data de Vencimento *</label>
                <input
                  type="date"
                  value={formData.data_vencimento}
                  onChange={(e) => setFormData({ ...formData, data_vencimento: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  required
                />
              </div>

              {/* Status */}
              <div>
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Status *</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as 'pendente' | 'pago' })}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  required
                >
                  {STATUS_OPTIONS.map(s => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </div>

              {/* Forma de Pagamento (se pago) */}
              {formData.status === 'pago' && (
                <div>
                  <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Forma de Pagamento *</label>
                  <select
                    value={formData.forma_pagamento}
                    onChange={(e) => setFormData({ ...formData, forma_pagamento: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    required
                  >
                    <option value="">Selecione...</option>
                    {FORMAS_PAGAMENTO.map(f => (
                      <option key={f.value} value={f.value}>{f.label}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Observações */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">Observações</label>
                <textarea
                  value={formData.observacoes}
                  onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  rows={3}
                  placeholder="Informações adicionais..."
                />
              </div>
            </div>

            {/* Botões */}
            <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
              <button
                type="button"
                onClick={handleCloseForm}
                className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-6 py-2 text-white rounded-lg hover:opacity-90 transition-opacity"
                style={{ backgroundColor: loja.cor_primaria }}
              >
                {editando ? 'Atualizar' : 'Criar'}
              </button>
            </div>
          </form>
        </div>
      </Modal>
    );
  }

  // Renderizar modal principal
  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="5xl">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: loja.cor_primaria }}>
            💰 Financeiro
          </h2>
          {(activeTab === 'receitas' || activeTab === 'despesas') && (
            <button
              onClick={() => setShowForm(true)}
              className="px-6 py-2 text-white rounded-lg hover:opacity-90 transition-opacity"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Nova Transação
            </button>
          )}
        </div>

        {/* Tabs */}
        <div className="flex border-b dark:border-gray-600 mb-6 overflow-x-auto">
          {[
            { key: 'resumo', label: '📊 Resumo' },
            { key: 'receitas', label: '💰 Receitas' },
            { key: 'despesas', label: '💸 Despesas' },
            { key: 'categorias', label: '📁 Categorias' }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as TabFinanceiro)}
              className={`px-6 py-3 font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.key
                  ? 'border-b-2'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
              style={activeTab === tab.key ? { borderColor: loja.cor_primaria, color: loja.cor_primaria } : {}}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Conteúdo */}
        {loading ? (
          <div className="text-center py-12">
            <div className="w-12 h-12 border-4 border-gray-200 dark:border-gray-700 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">Carregando...</p>
          </div>
        ) : (
          <>
            {/* Tab Resumo */}
            {activeTab === 'resumo' && resumo && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <ResumoCard
                    titulo="Receitas"
                    valor={resumo.receitas_pagas}
                    valorSecundario={resumo.receitas_pendentes}
                    labelSecundario="Pendente"
                    cor="#10B981"
                    icone="💰"
                  />
                  <ResumoCard
                    titulo="Despesas"
                    valor={resumo.despesas_pagas}
                    valorSecundario={resumo.despesas_pendentes}
                    labelSecundario="Pendente"
                    cor="#EF4444"
                    icone="💸"
                  />
                  <ResumoCard
                    titulo="Saldo"
                    valor={resumo.saldo}
                    cor={resumo.saldo >= 0 ? '#3B82F6' : '#EF4444'}
                    icone="💵"
                  />
                </div>

                {resumo.transacoes_atrasadas > 0 && (
                  <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <p className="text-red-800 dark:text-red-300 font-medium">
                      ⚠️ {resumo.transacoes_atrasadas} transação(ões) atrasada(s) - Total: R$ {resumo.valor_atrasado.toFixed(2)}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Tab Receitas/Despesas */}
            {(activeTab === 'receitas' || activeTab === 'despesas') && (
              <div className="space-y-3">
                {transacoes.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                      <span className="text-3xl">{activeTab === 'receitas' ? '💰' : '💸'}</span>
                    </div>
                    <p className="text-lg mb-2 text-gray-700 dark:text-gray-300">
                      Nenhuma {activeTab === 'receitas' ? 'receita' : 'despesa'} encontrada
                    </p>
                    <button
                      onClick={() => setShowForm(true)}
                      className="mt-4 px-6 py-3 text-white rounded-lg hover:opacity-90 transition-opacity"
                      style={{ backgroundColor: loja.cor_primaria }}
                    >
                      + Adicionar Primeira {activeTab === 'receitas' ? 'Receita' : 'Despesa'}
                    </button>
                  </div>
                ) : (
                  transacoes.map((transacao) => (
                    <TransacaoItem
                      key={transacao.id}
                      transacao={transacao}
                      corPrimaria={loja.cor_primaria}
                      onMarcarPago={handleMarcarComoPago}
                      onExcluir={handleExcluir}
                    />
                  ))
                )}
              </div>
            )}

            {/* Tab Categorias */}
            {activeTab === 'categorias' && (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                  <span className="text-3xl">📁</span>
                </div>
                <p className="text-lg mb-2 text-gray-700 dark:text-gray-300">
                  Gerenciamento de Categorias
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Funcionalidade em desenvolvimento
                </p>
              </div>
            )}
          </>
        )}

        {/* Footer */}
        <div className="flex justify-end gap-3 pt-6 border-t dark:border-gray-600 mt-6">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white transition-colors"
          >
            Fechar
          </button>
        </div>
      </div>
    </Modal>
  );
}

export default ModalFinanceiro;
