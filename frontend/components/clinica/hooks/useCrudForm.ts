import { useState, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';

interface UseCrudFormOptions<T> {
  endpoint: string;
  initialFormData: T;
  onSuccess?: () => void;
  formatDataForApi?: (data: T) => Record<string, unknown>;
}

interface UseCrudFormReturn<T> {
  // Estados
  items: T[];
  loading: boolean;
  showForm: boolean;
  editingItem: T | null;
  formData: T;
  submitting: boolean;
  error: string | null;

  // Ações
  loadItems: () => Promise<void>;
  handleEdit: (item: T) => void;
  handleDelete: (item: T & { id: number; nome?: string }) => Promise<void>;
  handleChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  resetForm: () => void;
  setShowForm: (show: boolean) => void;
  setFormData: React.Dispatch<React.SetStateAction<T>>;
}

export function useCrudForm<T extends Record<string, unknown>>({
  endpoint,
  initialFormData,
  onSuccess,
  formatDataForApi,
}: UseCrudFormOptions<T>): UseCrudFormReturn<T> {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState<T | null>(null);
  const [formData, setFormData] = useState<T>(initialFormData);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadItems = useCallback(async () => {
    try {
      setLoading(true);
      const response = await clinicaApiClient.get(endpoint);
      setItems(response.data);
      setError(null);
    } catch (err) {
      console.error(`Erro ao carregar ${endpoint}:`, err);
      setError('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  const handleEdit = useCallback((item: T) => {
    setEditingItem(item);
    // Preencher formData com os valores do item
    const newFormData = { ...initialFormData };
    Object.keys(initialFormData).forEach((key) => {
      const value = (item as Record<string, unknown>)[key];
      (newFormData as Record<string, unknown>)[key] = value ?? '';
    });
    setFormData(newFormData);
    setShowForm(true);
  }, [initialFormData]);

  const handleDelete = useCallback(async (item: T & { id: number; nome?: string }) => {
    const itemName = item.nome || 'item';
    if (!confirm(`Tem certeza que deseja excluir ${itemName}?`)) return;

    try {
      await clinicaApiClient.delete(`${endpoint}${item.id}/`);
      alert('✅ Excluído com sucesso!');
      await loadItems();
      onSuccess?.();
    } catch (err) {
      console.error('Erro ao excluir:', err);
      alert('❌ Erro ao excluir');
    }
  }, [endpoint, loadItems, onSuccess]);

  const handleChange = useCallback((
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  }, []);

  const resetForm = useCallback(() => {
    setFormData(initialFormData);
    setEditingItem(null);
    setShowForm(false);
    setError(null);
  }, [initialFormData]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      // Limpar campos vazios - converter strings vazias para null
      const dataToSend = formatDataForApi 
        ? formatDataForApi(formData)
        : Object.fromEntries(
            Object.entries(formData).map(([key, value]) => {
              // Para campos de data, converter string vazia para null
              if ((key.includes('data') || key.includes('nascimento')) && value === '') {
                return [key, null];
              }
              // Para outros campos string, converter vazio para null
              return [key, value === '' ? null : value];
            })
          );

      if (editingItem && (editingItem as Record<string, unknown>).id) {
        await clinicaApiClient.put(
          `${endpoint}${(editingItem as Record<string, unknown>).id}/`,
          dataToSend
        );
        alert('✅ Atualizado com sucesso!');
      } else {
        await clinicaApiClient.post(endpoint, dataToSend);
        alert('✅ Criado com sucesso!');
      }

      await loadItems();
      onSuccess?.();
      resetForm();
    } catch (err: unknown) {
      console.error('Erro ao salvar:', err);
      
      let errorMessage = '❌ Erro ao salvar';
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: Record<string, unknown> } };
        if (axiosError.response?.data) {
          const errorData = axiosError.response.data;
          if (typeof errorData === 'object') {
            const errorFields = Object.keys(errorData);
            if (errorFields.length > 0) {
              errorMessage += `\nCampos com erro: ${errorFields.join(', ')}`;
            }
          }
        }
      }
      setError(errorMessage);
      alert(errorMessage);
    } finally {
      setSubmitting(false);
    }
  }, [formData, editingItem, endpoint, formatDataForApi, loadItems, onSuccess, resetForm]);

  return {
    items,
    loading,
    showForm,
    editingItem,
    formData,
    submitting,
    error,
    loadItems,
    handleEdit,
    handleDelete,
    handleChange,
    handleSubmit,
    resetForm,
    setShowForm,
    setFormData,
  };
}
