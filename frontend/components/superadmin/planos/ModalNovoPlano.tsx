'use client';

import { useState } from 'react';
import apiClient from '@/lib/api-client';
import { formatCurrency } from '@/lib/financeiro-helpers';

interface Plano {
  id: number;
  nome: string;
  slug: string;
  descricao: string;
  preco_mensal: string;
  preco_anual: string;
  max_produtos: number;
  max_usuarios: number;
  max_pedidos_mes: number;
  espaco_storage_gb: number;
  tem_relatorios_avancados: boolean;
  tem_api_acesso: boolean;
  tem_suporte_prioritario: boolean;
  tem_dominio_customizado: boolean;
  tem_whatsapp_integration: boolean;
  is_active: boolean;
  ordem: number;
}

interface ModalNovoPlanoProps {
  onClose: () => void;
  onSuccess: () => void;
  editingPlano?: Plano | null;
  /** ID do tipo de app selecionado (ex.: Clínica de Estética) para vincular o novo plano */
  tipoLojaId?: number | null;
}

export function ModalNovoPlano({ onClose, onSuccess, editingPlano, tipoLojaId = null }: ModalNovoPlanoProps) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    nome: editingPlano?.nome || '',
    slug: editingPlano?.slug || '',
    descricao: editingPlano?.descricao || '',
    preco_mensal: editingPlano?.preco_mensal || '',
    preco_anual: editingPlano?.preco_anual || '',
    max_produtos: editingPlano?.max_produtos || 100,
    max_usuarios: editingPlano?.max_usuarios || 3,
    max_pedidos_mes: editingPlano?.max_pedidos_mes || 100,
    espaco_storage_gb: editingPlano?.espaco_storage_gb || 5,
    tem_relatorios_avancados: editingPlano?.tem_relatorios_avancados || false,
    tem_api_acesso: editingPlano?.tem_api_acesso || false,
    tem_suporte_prioritario: editingPlano?.tem_suporte_prioritario || false,
    tem_dominio_customizado: editingPlano?.tem_dominio_customizado || false,
    tem_whatsapp_integration: editingPlano?.tem_whatsapp_integration || false,
    is_active: editingPlano?.is_active ?? true,
    ordem: editingPlano?.ordem || 1,
  });

  const isEditing = !!editingPlano;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else if (type === 'number') {
      setFormData(prev => ({ ...prev, [name]: parseInt(value) || 0 }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
    
    // Auto-gerar slug a partir do nome
    if (name === 'nome') {
      const slug = value.toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/(^-|-$)/g, '');
      setFormData(prev => ({ ...prev, slug }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isEditing && editingPlano) {
        await apiClient.put(`/superadmin/planos/${editingPlano.id}/`, formData);
        alert('Plano atualizado com sucesso!');
      } else {
        const payload = { ...formData } as Record<string, unknown>;
        if (tipoLojaId != null) {
          payload.tipos_loja = [tipoLojaId];
        }
        await apiClient.post('/superadmin/planos/', payload);
        alert('Plano criado com sucesso!');
      }
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Erro ao salvar plano:', error);
      alert(`Erro: ${error.response?.data?.error || JSON.stringify(error.response?.data) || 'Erro ao salvar plano'}`);
    } finally {
      setLoading(false);
    }
  };

  const planosPreDefinidos = [
    {
      nome: 'Básico',
      ordem: 1,
      preco_mensal: '49.90',
      max_produtos: 100,
      max_usuarios: 3,
      max_pedidos_mes: 100,
      espaco_storage_gb: 5,
    },
    {
      nome: 'Profissional',
      ordem: 2,
      preco_mensal: '99.90',
      max_produtos: 500,
      max_usuarios: 10,
      max_pedidos_mes: 500,
      espaco_storage_gb: 20,
      tem_relatorios_avancados: true,
      tem_whatsapp_integration: true,
    },
    {
      nome: 'Enterprise',
      ordem: 3,
      preco_mensal: '199.90',
      max_produtos: 999999,
      max_usuarios: 50,
      max_pedidos_mes: 999999,
      espaco_storage_gb: 100,
      tem_relatorios_avancados: true,
      tem_api_acesso: true,
      tem_suporte_prioritario: true,
      tem_dominio_customizado: true,
      tem_whatsapp_integration: true,
    },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-3xl w-full my-8 max-h-[85vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-6 text-purple-900 dark:text-purple-400">
          {isEditing ? 'Editar Plano de Assinatura' : 'Novo Plano de Assinatura'}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Templates Pré-definidos */}
          <div>
            <h3 className="text-lg font-semibold mb-3 text-gray-700 dark:text-gray-300">Templates Rápidos</h3>
            <div className="grid grid-cols-3 gap-3">
              {planosPreDefinidos.map((template) => (
                <button
                  key={template.nome}
                  type="button"
                  onClick={() => setFormData(prev => ({
                    ...prev,
                    ...template,
                    nome: template.nome,
                    slug: template.nome.toLowerCase(),
                    descricao: `Plano ${template.nome}`,
                  }))}
                  className="p-4 border-2 border-gray-200 dark:border-gray-600 rounded-lg hover:border-purple-400 dark:hover:border-purple-500 transition-all text-left"
                >
                  <div className="font-semibold text-gray-900 dark:text-gray-100">{template.nome}</div>
                  <div className="text-sm text-purple-600 dark:text-purple-400 mt-1">{formatCurrency(template.preco_mensal)}/mês</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{template.max_usuarios} usuários</div>
                </button>
              ))}
            </div>
          </div>

          {/* Informações Básicas */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-300">Informações Básicas</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nome do Plano *
                </label>
                <input
                  type="text"
                  name="nome"
                  value={formData.nome}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Ex: Básico"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Slug *
                </label>
                <input
                  type="text"
                  name="slug"
                  value={formData.slug}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="basico"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Descrição *
                </label>
                <textarea
                  name="descricao"
                  value={formData.descricao}
                  onChange={handleChange}
                  required
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Descrição do plano..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Preço Mensal (R$) *
                </label>
                <input
                  type="text"
                  name="preco_mensal"
                  value={formData.preco_mensal}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="49.90"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Preço Anual (R$)
                </label>
                <input
                  type="text"
                  name="preco_anual"
                  value={formData.preco_anual}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="499.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Ordem de Exibição *
                </label>
                <select
                  name="ordem"
                  value={formData.ordem}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value={1}>1 - Básico</option>
                  <option value={2}>2 - Intermediário</option>
                  <option value={3}>3 - Avançado</option>
                </select>
              </div>
            </div>
          </div>

          {/* Limites */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-300">Limites</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Produtos
                </label>
                <input
                  type="number"
                  name="max_produtos"
                  value={formData.max_produtos}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">999999 = Ilimitado</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Usuários
                </label>
                <input
                  type="number"
                  name="max_usuarios"
                  value={formData.max_usuarios}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Pedidos/mês
                </label>
                <input
                  type="number"
                  name="max_pedidos_mes"
                  value={formData.max_pedidos_mes}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">999999 = Ilimitado</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Storage (GB)
                </label>
                <input
                  type="number"
                  name="espaco_storage_gb"
                  value={formData.espaco_storage_gb}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
            </div>
          </div>

          {/* Funcionalidades */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-300">Funcionalidades</h3>
            <div className="grid grid-cols-2 gap-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_relatorios_avancados"
                  checked={formData.tem_relatorios_avancados}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm text-gray-900 dark:text-gray-100">📊 Relatórios Avançados</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_api_acesso"
                  checked={formData.tem_api_acesso}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm text-gray-900 dark:text-gray-100">🔌 Acesso à API</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_suporte_prioritario"
                  checked={formData.tem_suporte_prioritario}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm text-gray-900 dark:text-gray-100">⭐ Suporte Prioritário</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_dominio_customizado"
                  checked={formData.tem_dominio_customizado}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm text-gray-900 dark:text-gray-100">🌐 Domínio Customizado</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_whatsapp_integration"
                  checked={formData.tem_whatsapp_integration}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm text-gray-900 dark:text-gray-100">💬 Integração WhatsApp</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm text-gray-900 dark:text-gray-100">✅ Plano Ativo</span>
              </label>
            </div>
          </div>

          {/* Preview */}
          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-3 text-gray-700 dark:text-gray-300">Preview</h3>
            <div className="bg-white dark:bg-gray-800 rounded-lg border-2 border-purple-200 dark:border-purple-700 p-6 text-center">
              <h4 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">{formData.nome || 'Nome do Plano'}</h4>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">{formData.descricao || 'Descrição...'}</p>
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-1">
                {formatCurrency(formData.preco_mensal || 0)}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">por mês</div>
              <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
                {formData.max_usuarios} usuários • {formData.max_produtos === 999999 ? 'Produtos ilimitados' : `${formData.max_produtos} produtos`}
              </div>
            </div>
          </div>

          {/* Botões */}
          <div className="flex justify-end space-x-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (isEditing ? 'Salvando...' : 'Criando...') : (isEditing ? 'Salvar Alterações' : 'Criar Plano')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
