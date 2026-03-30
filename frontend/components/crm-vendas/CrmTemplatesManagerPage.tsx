'use client';

import { useEffect, useState, useCallback } from 'react';
import type { LucideIcon } from 'lucide-react';
import { Plus, Edit2, Trash2, X, Star } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { normalizeListResponse, getCrmApiErrorDetail } from '@/lib/crm-utils';

export interface CrmTemplateRecord {
  id: number;
  nome: string;
  conteudo: string;
  is_padrao: boolean;
  ativo: boolean;
  created_at?: string;
  updated_at?: string;
}

export type CrmTemplateApiSegment = 'proposta-templates' | 'contrato-templates';

interface CrmTemplatesManagerPageProps {
  apiSegment: CrmTemplateApiSegment;
  title: string;
  subtitle: string;
  namePlaceholder: string;
  EmptyStateIcon: LucideIcon;
}

type ModalType = 'create' | 'edit' | 'delete' | null;

/**
 * CRUD unificado para templates de proposta e de contrato (rotas DRF espelhadas).
 */
export default function CrmTemplatesManagerPage({
  apiSegment,
  title,
  subtitle,
  namePlaceholder,
  EmptyStateIcon,
}: CrmTemplatesManagerPageProps) {
  const base = `/crm-vendas/${apiSegment}`;
  const [templates, setTemplates] = useState<CrmTemplateRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalType, setModalType] = useState<ModalType>(null);
  const [selected, setSelected] = useState<CrmTemplateRecord | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    conteudo: '',
    is_padrao: false,
    ativo: true,
  });
  const [submitting, setSubmitting] = useState(false);

  const loadTemplates = useCallback(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<CrmTemplateRecord[] | { results: CrmTemplateRecord[] }>(`${base}/`);
      setTemplates(normalizeListResponse(res.data));
      setError(null);
    } catch (err: unknown) {
      setError(getCrmApiErrorDetail(err, 'Erro ao carregar templates.'));
    } finally {
      setLoading(false);
    }
  }, [base]);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  const openModal = (type: ModalType, item?: CrmTemplateRecord) => {
    setModalType(type);
    setSelected(item || null);
    if (type === 'edit' && item) {
      setFormData({
        nome: item.nome || '',
        conteudo: item.conteudo || '',
        is_padrao: item.is_padrao ?? false,
        ativo: item.ativo ?? true,
      });
    } else if (type === 'create') {
      setFormData({
        nome: '',
        conteudo: '',
        is_padrao: false,
        ativo: true,
      });
    }
  };

  const closeModal = () => {
    setModalType(null);
    setSelected(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.nome.trim()) {
      alert('Nome é obrigatório');
      return;
    }
    try {
      setSubmitting(true);
      const payload = {
        nome: formData.nome.trim(),
        conteudo: formData.conteudo,
        is_padrao: formData.is_padrao,
        ativo: formData.ativo,
      };
      if (modalType === 'create') {
        await apiClient.post(`${base}/`, payload);
      } else if (modalType === 'edit' && selected) {
        await apiClient.put(`${base}/${selected.id}/`, payload);
      }
      await loadTemplates();
      closeModal();
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao salvar.'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selected) return;
    try {
      setSubmitting(true);
      await apiClient.delete(`${base}/${selected.id}/`);
      await loadTemplates();
      closeModal();
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao excluir.'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleMarcarPadrao = async (id: number) => {
    try {
      await apiClient.post(`${base}/${id}/marcar_padrao/`);
      await loadTemplates();
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao marcar como padrão.'));
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48 animate-pulse" />
        <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{title}</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{subtitle}</p>
        </div>
        <button
          type="button"
          onClick={() => openModal('create')}
          className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded text-sm font-medium transition-colors shadow-sm"
        >
          <Plus size={18} />
          <span>Novo Template</span>
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {templates.length === 0 ? (
          <div className="col-span-full py-12 text-center text-gray-500 dark:text-gray-400 bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c]">
            <EmptyStateIcon size={48} className="mx-auto mb-3 opacity-30" />
            <p className="font-medium">Nenhum template cadastrado</p>
            <p className="text-sm mt-1">Clique em &quot;Novo Template&quot; para criar</p>
          </div>
        ) : (
          templates.map((t) => (
            <div
              key={t.id}
              className="bg-white dark:bg-[#16325c] rounded-lg shadow border border-gray-200 dark:border-[#0d1f3c] p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  {t.nome}
                  {t.is_padrao && (
                    <span title="Template padrão">
                      <Star size={16} className="text-yellow-500 fill-yellow-500" />
                    </span>
                  )}
                </h3>
                <div className="flex gap-1">
                  {!t.is_padrao && (
                    <button
                      type="button"
                      onClick={() => handleMarcarPadrao(t.id)}
                      className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
                      aria-label="Marcar como padrão"
                    >
                      <Star size={16} />
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => openModal('edit', t)}
                    className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
                    aria-label="Editar"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button
                    type="button"
                    onClick={() => openModal('delete', t)}
                    className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400"
                    aria-label="Excluir"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">
                {t.conteudo || 'Sem conteúdo'}
              </p>
              <div className="mt-3 flex items-center gap-2">
                <span
                  className={`text-xs px-2 py-0.5 rounded ${
                    t.ativo
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                  }`}
                >
                  {t.ativo ? 'Ativo' : 'Inativo'}
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {(modalType === 'create' || modalType === 'edit') && (
        <>
          <div className="fixed inset-0 bg-black/50 z-[80]" onClick={() => !submitting && closeModal()} />
          <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {modalType === 'create' ? 'Novo Template' : 'Editar Template'}
                </h2>
                <button type="button" onClick={() => !submitting && closeModal()} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                  <X size={20} />
                </button>
              </div>
              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
                  <input
                    type="text"
                    value={formData.nome}
                    onChange={(e) => setFormData((f) => ({ ...f, nome: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                    placeholder={namePlaceholder}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Conteúdo</label>
                  <textarea
                    value={formData.conteudo}
                    onChange={(e) => setFormData((f) => ({ ...f, conteudo: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                    rows={10}
                    placeholder="Conteúdo do template..."
                  />
                </div>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.is_padrao}
                      onChange={(e) => setFormData((f) => ({ ...f, is_padrao: e.target.checked }))}
                      className="rounded"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Marcar como padrão</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.ativo}
                      onChange={(e) => setFormData((f) => ({ ...f, ativo: e.target.checked }))}
                      className="rounded"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">Ativo</span>
                  </label>
                </div>
                <div className="flex gap-2 pt-2">
                  <button type="button" onClick={() => !submitting && closeModal()} className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg">
                    Cancelar
                  </button>
                  <button type="submit" disabled={submitting} className="flex-1 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded-lg disabled:opacity-50">
                    {submitting ? 'Salvando...' : 'Salvar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </>
      )}

      {modalType === 'delete' && selected && (
        <>
          <div className="fixed inset-0 bg-black/50 z-[80]" onClick={() => !submitting && closeModal()} />
          <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full">
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Excluir Template</h2>
                <button type="button" onClick={() => !submitting && closeModal()} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                  <X size={20} />
                </button>
              </div>
              <div className="p-6">
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Deseja excluir o template &quot;{selected.nome}&quot;? Esta ação não pode ser desfeita.
                </p>
                <div className="flex gap-2">
                  <button type="button" onClick={() => !submitting && closeModal()} className="flex-1 px-4 py-2 border rounded-lg">
                    Cancelar
                  </button>
                  <button type="button" onClick={handleDelete} disabled={submitting} className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50">
                    {submitting ? 'Excluindo...' : 'Excluir'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
