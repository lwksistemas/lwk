/**
 * Modal para Gerenciar Categorias de Produtos/Serviços
 * 
 * Permite criar, editar e excluir categorias.
 */
'use client';

import { useState } from 'react';
import { X, Plus, Edit2, Trash2, Save } from 'lucide-react';
import { Categoria } from '@/hooks/useProdutosServicos';

interface CategoriasModalProps {
  isOpen: boolean;
  categorias: Categoria[];
  onClose: () => void;
  onCriar: (data: { nome: string; descricao: string; cor: string }) => Promise<void>;
  onEditar: (id: number, data: { nome: string; descricao: string; cor: string }) => Promise<void>;
  onExcluir: (id: number) => Promise<void>;
}

export function CategoriasModal({
  isOpen,
  categorias,
  onClose,
  onCriar,
  onEditar,
  onExcluir,
}: CategoriasModalProps) {
  const [editandoId, setEditandoId] = useState<number | null>(null);
  const [criandoNova, setCriandoNova] = useState(false);
  const [formData, setFormData] = useState({ nome: '', descricao: '', cor: '#3B82F6' });
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleCriar = async () => {
    if (!formData.nome.trim()) {
      alert('Nome é obrigatório');
      return;
    }

    try {
      setSubmitting(true);
      await onCriar(formData);
      setFormData({ nome: '', descricao: '', cor: '#3B82F6' });
      setCriandoNova(false);
    } catch (error) {
      alert('Erro ao criar categoria');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditar = async (id: number) => {
    if (!formData.nome.trim()) {
      alert('Nome é obrigatório');
      return;
    }

    try {
      setSubmitting(true);
      await onEditar(id, formData);
      setEditandoId(null);
      setFormData({ nome: '', descricao: '', cor: '#3B82F6' });
    } catch (error) {
      alert('Erro ao editar categoria');
    } finally {
      setSubmitting(false);
    }
  };

  const handleExcluir = async (id: number) => {
    if (!confirm('Tem certeza que deseja excluir esta categoria?')) return;

    try {
      setSubmitting(true);
      await onExcluir(id);
    } catch (error) {
      alert('Erro ao excluir categoria');
    } finally {
      setSubmitting(false);
    }
  };

  const iniciarEdicao = (categoria: Categoria) => {
    setEditandoId(categoria.id);
    setFormData({
      nome: categoria.nome,
      descricao: categoria.descricao || '',
      cor: categoria.cor || '#3B82F6',
    });
    setCriandoNova(false);
  };

  const cancelarEdicao = () => {
    setEditandoId(null);
    setCriandoNova(false);
    setFormData({ nome: '', descricao: '', cor: '#3B82F6' });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Gerenciar Categorias
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {/* Botão Nova Categoria */}
          {!criandoNova && !editandoId && (
            <button
              onClick={() => setCriandoNova(true)}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-gray-600 dark:text-gray-400 hover:border-blue-500 hover:text-blue-500 transition-colors"
            >
              <Plus size={20} />
              <span>Nova Categoria</span>
            </button>
          )}

          {/* Formulário Nova Categoria */}
          {criandoNova && (
            <div className="border border-gray-300 dark:border-gray-600 rounded-lg p-4 space-y-3 bg-gray-50 dark:bg-gray-700/50">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nome *
                </label>
                <input
                  type="text"
                  value={formData.nome}
                  onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  placeholder="Ex: Hardware, Software, Consultoria"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Descrição
                </label>
                <textarea
                  value={formData.descricao}
                  onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  rows={2}
                  placeholder="Descrição opcional"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Cor
                </label>
                <input
                  type="color"
                  value={formData.cor}
                  onChange={(e) => setFormData({ ...formData, cor: e.target.value })}
                  className="w-20 h-10 border border-gray-300 dark:border-gray-600 rounded cursor-pointer"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleCriar}
                  disabled={submitting}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50"
                >
                  <Save size={16} />
                  Salvar
                </button>
                <button
                  onClick={cancelarEdicao}
                  disabled={submitting}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 rounded-lg"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}

          {/* Lista de Categorias */}
          <div className="space-y-2">
            {categorias.map((categoria) => (
              <div
                key={categoria.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800"
              >
                {editandoId === categoria.id ? (
                  // Modo Edição
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Nome *
                      </label>
                      <input
                        type="text"
                        value={formData.nome}
                        onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Descrição
                      </label>
                      <textarea
                        value={formData.descricao}
                        onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        rows={2}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Cor
                      </label>
                      <input
                        type="color"
                        value={formData.cor}
                        onChange={(e) => setFormData({ ...formData, cor: e.target.value })}
                        className="w-20 h-10 border border-gray-300 dark:border-gray-600 rounded cursor-pointer"
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEditar(categoria.id)}
                        disabled={submitting}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50"
                      >
                        <Save size={16} />
                        Salvar
                      </button>
                      <button
                        onClick={cancelarEdicao}
                        disabled={submitting}
                        className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 rounded-lg"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                ) : (
                  // Modo Visualização
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-4 h-4 rounded"
                        style={{ backgroundColor: categoria.cor }}
                      />
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white">
                          {categoria.nome}
                        </h3>
                        {categoria.descricao && (
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {categoria.descricao}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => iniciarEdicao(categoria)}
                        disabled={submitting}
                        className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                        title="Editar"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        onClick={() => handleExcluir(categoria.id)}
                        disabled={submitting}
                        className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                        title="Excluir"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {categorias.length === 0 && !criandoNova && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              Nenhuma categoria cadastrada
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 rounded-lg"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
