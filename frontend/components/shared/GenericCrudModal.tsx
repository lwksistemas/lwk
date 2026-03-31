'use client';

import { useState, useEffect, useCallback } from 'react';
import { Modal } from '@/components/ui/Modal';
import apiClient from '@/lib/api-client';
import { extractArrayData, formatApiError } from '@/lib/api-helpers';

export interface FieldConfig {
  name: string;
  label: string;
  type: 'text' | 'email' | 'tel' | 'date' | 'textarea' | 'select' | 'number';
  required?: boolean;
  options?: { value: string; label: string }[];
  placeholder?: string;
  maxLength?: number;
  rows?: number;
}

export interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

interface GenericCrudModalProps<T extends { id: number }> {
  title: string;
  endpoint: string;
  fields: FieldConfig[];
  loja: LojaInfo;
  onClose: () => void;
  onSuccess?: () => void;
  renderCustomField?: (field: FieldConfig, value: any, onChange: (value: any) => void) => React.ReactNode;
  transformDataBeforeSave?: (data: any) => any;
  transformDataAfterLoad?: (data: T) => any;
}

export function GenericCrudModal<T extends { id: number }>({
  title,
  endpoint,
  fields,
  loja,
  onClose,
  onSuccess,
  renderCustomField,
  transformDataBeforeSave,
  transformDataAfterLoad,
}: GenericCrudModalProps<T>) {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState<T | null>(null);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);

  // Inicializar formData com valores vazios
  useEffect(() => {
    const initialData: Record<string, any> = {};
    fields.forEach(field => {
      initialData[field.name] = '';
    });
    setFormData(initialData);
  }, [fields]);

  const loadItems = useCallback(async () => {
    try {
      setLoading(true);
      setLoadError(false);
      const response = await apiClient.get(endpoint);
      const data = extractArrayData<T>(response);
      setItems(data);
    } catch (error: any) {
      console.error(`Erro ao carregar ${title}:`, error);
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  }, [endpoint, title]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  const handleAdd = () => {
    setEditingItem(null);
    const initialData: Record<string, any> = {};
    fields.forEach(field => {
      initialData[field.name] = '';
    });
    setFormData(initialData);
    setShowForm(true);
  };

  const handleEdit = (item: T) => {
    setEditingItem(item);
    const data = transformDataAfterLoad ? transformDataAfterLoad(item) : item;
    setFormData({ ...data });
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm(`Tem certeza que deseja excluir este ${title.toLowerCase()}?`)) return;

    try {
      setDeleting(id);
      await apiClient.delete(`${endpoint}${id}/`);
      await loadItems();
      onSuccess?.();
    } catch (error: any) {
      alert(formatApiError(error));
    } finally {
      setDeleting(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      const dataToSave = transformDataBeforeSave 
        ? transformDataBeforeSave(formData) 
        : formData;

      if (editingItem) {
        await apiClient.put(`${endpoint}${editingItem.id}/`, dataToSave);
      } else {
        await apiClient.post(endpoint, dataToSave);
      }

      setShowForm(false);
      await loadItems();
      onSuccess?.();
    } catch (error: any) {
      alert(formatApiError(error));
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (name: string, value: any) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const renderField = (field: FieldConfig) => {
    const value = formData[field.name] || '';

    // Permitir customização de campos específicos
    if (renderCustomField) {
      const custom = renderCustomField(field, value, (val) => handleChange(field.name, val));
      if (custom) return custom;
    }

    const commonProps = {
      id: field.name,
      name: field.name,
      value,
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => 
        handleChange(field.name, e.target.value),
      required: field.required,
      placeholder: field.placeholder,
      maxLength: field.maxLength,
      className: "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
    };

    switch (field.type) {
      case 'textarea':
        return (
          <textarea
            {...commonProps}
            rows={field.rows || 3}
          />
        );
      
      case 'select':
        return (
          <select {...commonProps}>
            <option value="">Selecione...</option>
            {field.options?.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        );
      
      default:
        return (
          <input
            {...commonProps}
            type={field.type}
          />
        );
    }
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={title}
      maxWidth="4xl"
    >
      <div className="p-6">
        {!showForm ? (
          <>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Lista de {title}</h3>
              <button
                onClick={handleAdd}
                className="px-4 py-2 rounded-lg text-white"
                style={{ backgroundColor: loja.cor_primaria }}
              >
                + Adicionar
              </button>
            </div>

            {loading && (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                <p className="mt-2 text-gray-600">Carregando...</p>
              </div>
            )}

            {loadError && (
              <div className="text-center py-8">
                <p className="text-red-600">Erro ao carregar dados</p>
                <button
                  onClick={loadItems}
                  className="mt-2 text-blue-600 hover:underline"
                >
                  Tentar novamente
                </button>
              </div>
            )}

            {!loading && !loadError && items.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                Nenhum registro encontrado
              </div>
            )}

            {!loading && !loadError && items.length > 0 && (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {items.map((item: any) => (
                  <div
                    key={item.id}
                    className="flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                  >
                    <div className="flex-1">
                      <p className="font-medium">{item.nome || item.name || item.titulo || `#${item.id}`}</p>
                      {item.email && <p className="text-sm text-gray-600">{item.email}</p>}
                      {item.telefone && <p className="text-sm text-gray-600">{item.telefone}</p>}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(item)}
                        className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        disabled={deleting === item.id}
                        className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
                      >
                        {deleting === item.id ? 'Excluindo...' : 'Excluir'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <h3 className="text-lg font-semibold mb-4">
              {editingItem ? 'Editar' : 'Adicionar'} {title}
            </h3>

            {fields.map(field => (
              <div key={field.name}>
                <label htmlFor={field.name} className="block text-sm font-medium text-gray-700 mb-1">
                  {field.label}
                  {field.required && <span className="text-red-500 ml-1">*</span>}
                </label>
                {renderField(field)}
              </div>
            ))}

            <div className="flex gap-2 pt-4">
              <button
                type="submit"
                disabled={saving}
                className="flex-1 py-2 rounded-lg text-white disabled:opacity-50"
                style={{ backgroundColor: loja.cor_primaria }}
              >
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                disabled={saving}
                className="flex-1 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 disabled:opacity-50"
              >
                Cancelar
              </button>
            </div>
          </form>
        )}
      </div>
    </Modal>
  );
}
