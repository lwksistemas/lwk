/**
 * Modal para criar/editar Tipo de App
 * ✅ REFATORADO v770: Componente extraído e simplificado
 */
import { useState, useEffect } from 'react';
import { TipoApp, TipoAppFormData, useTipoAppActions } from '@/hooks/useTipoAppActions';

interface TipoAppModalProps {
  onClose: () => void;
  onSuccess: () => void;
  editingTipo?: TipoApp | null;
}

const CORES_PRE_DEFINIDAS = [
  { nome: 'Verde', primaria: '#10B981', secundaria: '#059669' },
  { nome: 'Azul', primaria: '#3B82F6', secundaria: '#2563EB' },
  { nome: 'Vermelho', primaria: '#EF4444', secundaria: '#DC2626' },
  { nome: 'Roxo', primaria: '#8B5CF6', secundaria: '#7C3AED' },
  { nome: 'Laranja', primaria: '#F97316', secundaria: '#EA580C' },
  { nome: 'Rosa', primaria: '#EC4899', secundaria: '#DB2777' },
];

export function TipoAppModal({ onClose, onSuccess, editingTipo }: TipoAppModalProps) {
  const { criarTipoApp, atualizarTipoApp, loading, error } = useTipoAppActions();
  const isEditing = !!editingTipo;

  const [formData, setFormData] = useState<TipoAppFormData>({
    nome: editingTipo?.nome || '',
    slug: editingTipo?.slug || '',
    descricao: editingTipo?.descricao || '',
    dashboard_template: editingTipo?.dashboard_template || 'default',
    cor_primaria: editingTipo?.cor_primaria || '#10B981',
    cor_secundaria: editingTipo?.cor_secundaria || '#059669',
    tem_produtos: editingTipo?.tem_produtos ?? true,
    tem_servicos: editingTipo?.tem_servicos ?? false,
    tem_agendamento: editingTipo?.tem_agendamento ?? false,
    tem_delivery: editingTipo?.tem_delivery ?? false,
    tem_estoque: editingTipo?.tem_estoque ?? true,
  });

  // Auto-gerar slug a partir do nome
  const handleNomeChange = (nome: string) => {
    const slug = nome.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '');
    
    setFormData(prev => ({ ...prev, nome, slug }));
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else if (name === 'nome') {
      handleNomeChange(value);
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    let success = false;
    if (isEditing && editingTipo) {
      success = await atualizarTipoApp(editingTipo.id, formData);
      if (success) alert('Tipo de app atualizado com sucesso!');
    } else {
      success = await criarTipoApp(formData);
      if (success) alert('Tipo de app criado com sucesso!');
    }

    if (success) {
      onSuccess();
      onClose();
    } else if (error) {
      alert(`Erro: ${error}`);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-6 text-purple-900">
          {isEditing ? 'Editar Tipo de App' : 'Novo Tipo de App'}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Informações Básicas */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Informações Básicas</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome do Tipo *
                </label>
                <input
                  type="text"
                  name="nome"
                  value={formData.nome}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Ex: E-commerce"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Slug *
                </label>
                <input
                  type="text"
                  name="slug"
                  value={formData.slug}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="e-commerce"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descrição *
                </label>
                <textarea
                  name="descricao"
                  value={formData.descricao}
                  onChange={handleChange}
                  required
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  placeholder="Descrição do tipo de app..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template do Dashboard
                </label>
                <select
                  name="dashboard_template"
                  value={formData.dashboard_template}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="default">Padrão</option>
                  <option value="ecommerce">E-commerce</option>
                  <option value="servicos">Serviços</option>
                  <option value="restaurante">Restaurante</option>
                </select>
              </div>
            </div>
          </div>

          {/* Cores */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Cores do Tema</h3>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Cores Pré-definidas
              </label>
              <div className="grid grid-cols-3 gap-2">
                {CORES_PRE_DEFINIDAS.map((cor) => (
                  <button
                    key={cor.nome}
                    type="button"
                    onClick={() => setFormData(prev => ({
                      ...prev,
                      cor_primaria: cor.primaria,
                      cor_secundaria: cor.secundaria
                    }))}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      formData.cor_primaria === cor.primaria
                        ? 'border-purple-600 bg-purple-50'
                        : 'border-gray-200 hover:border-purple-300'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <div
                        className="w-6 h-6 rounded-full"
                        style={{ backgroundColor: cor.primaria }}
                      />
                      <span className="text-sm font-medium">{cor.nome}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cor Primária
                </label>
                <div className="flex space-x-2">
                  <input
                    type="color"
                    name="cor_primaria"
                    value={formData.cor_primaria}
                    onChange={handleChange}
                    className="w-12 h-10 border border-gray-300 rounded"
                  />
                  <input
                    type="text"
                    value={formData.cor_primaria}
                    onChange={(e) => setFormData(prev => ({ ...prev, cor_primaria: e.target.value }))}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cor Secundária
                </label>
                <div className="flex space-x-2">
                  <input
                    type="color"
                    name="cor_secundaria"
                    value={formData.cor_secundaria}
                    onChange={handleChange}
                    className="w-12 h-10 border border-gray-300 rounded"
                  />
                  <input
                    type="text"
                    value={formData.cor_secundaria}
                    onChange={(e) => setFormData(prev => ({ ...prev, cor_secundaria: e.target.value }))}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Funcionalidades */}
          <div>
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Funcionalidades</h3>
            <div className="grid grid-cols-2 gap-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_produtos"
                  checked={formData.tem_produtos}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">Produtos</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_servicos"
                  checked={formData.tem_servicos}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">Serviços</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_agendamento"
                  checked={formData.tem_agendamento}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">Agendamento</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_delivery"
                  checked={formData.tem_delivery}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">Delivery</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="tem_estoque"
                  checked={formData.tem_estoque}
                  onChange={handleChange}
                  className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                />
                <span className="text-sm">Controle de Estoque</span>
              </label>
            </div>
          </div>

          {/* Preview */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-3 text-gray-700">Preview</h3>
            <div 
              className="h-16 rounded-lg flex items-center justify-center mb-2"
              style={{ backgroundColor: formData.cor_primaria }}
            >
              <span className="text-white font-bold">{formData.nome || 'Nome do Tipo'}</span>
            </div>
            <p className="text-sm text-gray-600">{formData.descricao || 'Descrição do tipo...'}</p>
          </div>

          {/* Botões */}
          <div className="flex justify-end space-x-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (isEditing ? 'Salvando...' : 'Criando...') : (isEditing ? 'Salvar Alterações' : 'Criar Tipo')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
