'use client';

import { useState, useEffect } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';
import { extractArrayData, formatApiError } from '@/lib/api-helpers';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

interface ModalBaseProps {
  loja: LojaInfo;
  onClose: () => void;
  onSuccess?: () => void;
  title: string;
  icon: string;
  endpoint: string;
  formFields: any[];
  renderListItem: (item: any, handleEditar: any, handleExcluir: any, loja: any) => React.ReactElement;
  emptyMessage?: string;
}

export function ModalBase({
  loja,
  onClose,
  onSuccess,
  title,
  icon,
  endpoint,
  formFields,
  renderListItem,
  emptyMessage = "Nenhum registro cadastrado"
}: ModalBaseProps) {
  const toast = useToast();
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [editando, setEditando] = useState<number | null>(null);
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingLista, setLoadingLista] = useState(true);
  const [formData, setFormData] = useState<any>({});

  useEffect(() => {
    loadItems();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Executar apenas uma vez no mount

  const loadItems = async () => {
    try {
      setLoadingLista(true);
      const res = await clinicaApiClient.get(endpoint);
      
      // Extrair array de forma segura
      setItems(extractArrayData(res));
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      toast.error(formatApiError(error));
      setItems([]); // Garantir array vazio em caso de erro
    } finally {
      setLoadingLista(false);
    }
  };

  const handleNovo = () => {
    setEditando(null);
    setFormData(formFields.reduce((acc: any, field: any) => ({ ...acc, [field.name]: field.defaultValue || '' }), {}));
    setMostrarFormulario(true);
  };

  const handleEditar = (item: any) => {
    setEditando(item.id);
    setFormData(formFields.reduce((acc: any, field: any) => ({ ...acc, [field.name]: field.getValue ? field.getValue(item) : item[field.name] || '' }), {}));
    setMostrarFormulario(true);
  };

  const handleExcluir = async (id: number, nome: string) => {
    if (!confirm(`Excluir "${nome}"?`)) return;
    
    try {
      await clinicaApiClient.delete(`${endpoint}${id}/`);
      toast.success('Excluído com sucesso');
      await loadItems();
      onSuccess?.();
    } catch (error: any) {
      console.error('Erro ao excluir:', error);
      toast.error(formatApiError(error));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Preparar payload com transformações
      const payload = formFields.reduce((acc: any, field: any) => {
        const value = formData[field.name];
        return { 
          ...acc, 
          [field.apiName || field.name]: field.transform ? field.transform(value) : value 
        };
      }, {});

      if (editando) {
        await clinicaApiClient.put(`${endpoint}${editando}/`, payload);
        toast.success('Atualizado com sucesso');
      } else {
        await clinicaApiClient.post(endpoint, payload);
        toast.success('Criado com sucesso');
      }
      
      setMostrarFormulario(false);
      await loadItems();
      onSuccess?.();
    } catch (error: any) {
      console.error('Erro ao salvar:', error);
      toast.error(formatApiError(error));
    } finally {
      setLoading(false);
    }
  };

  if (mostrarFormulario) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
          <h3 className="text-xl sm:text-2xl font-bold mb-6 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
            {icon} {editando ? 'Editar' : 'Novo'} {title}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {formFields.map((field: any) => (
                <div key={field.name} className={field.fullWidth ? 'md:col-span-2' : ''}>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {field.label} {field.required && '*'}
                  </label>
                  {field.type === 'select' ? (
                    <select
                      value={formData[field.name]}
                      onChange={(e) => setFormData((prev: any) => ({ ...prev, [field.name]: e.target.value }))}
                      required={field.required}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                    >
                      <option value="">Selecione...</option>
                      {field.options?.map((opt: any) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  ) : field.type === 'textarea' ? (
                    <textarea
                      value={formData[field.name]}
                      onChange={(e) => setFormData((prev: any) => ({ ...prev, [field.name]: e.target.value }))}
                      required={field.required}
                      rows={field.rows || 3}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                      placeholder={field.placeholder}
                    />
                  ) : (
                    <input
                      type={field.type || 'text'}
                      value={formData[field.name]}
                      onChange={(e) => setFormData((prev: any) => ({ ...prev, [field.name]: e.target.value }))}
                      required={field.required}
                      min={field.min}
                      step={field.step}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md"
                      placeholder={field.placeholder}
                    />
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <button type="button" onClick={() => setMostrarFormulario(false)} disabled={loading} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]">Cancelar</button>
              <button type="submit" disabled={loading} className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>{loading ? 'Salvando...' : (editando ? 'Atualizar' : 'Criar')}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto shadow-xl">
        <h3 className="text-xl sm:text-2xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>{icon} Gerenciar {title}</h3>
        {loadingLista ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : items.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 dark:text-gray-400 mb-4">{emptyMessage}</p>
            <button onClick={handleNovo} className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo</button>
          </div>
        ) : (
          <div className="space-y-4 mb-6">
            {items.map((item: any) => renderListItem(item, handleEditar, handleExcluir, loja))}
          </div>
        )}
        <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
          <button onClick={onClose} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]">Fechar</button>
          <button onClick={handleNovo} className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo</button>
        </div>
      </div>
    </div>
  );
}
