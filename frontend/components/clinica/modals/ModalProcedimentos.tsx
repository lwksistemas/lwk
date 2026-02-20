'use client';
import { ensureArray } from '@/lib/array-helpers';
import { formatCurrency } from '@/lib/financeiro-helpers';

import { useState, useEffect, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';
import { CrudModal } from '../shared/CrudModal';
import { FormField } from '../shared/FormField';
import type { LojaInfo } from '../shared/CrudModal';

interface Procedimento {
  id: number;
  nome: string;
  descricao: string;
  duracao: number;
  preco: string;
  categoria: string;
}

interface ModalProcedimentosProps {
  loja: LojaInfo;
  onClose: () => void;
  onSuccess: () => void;
}

const CATEGORIAS = [
  { value: 'Facial', label: 'Facial' },
  { value: 'Corporal', label: 'Corporal' },
  { value: 'Capilar', label: 'Capilar' },
  { value: 'Massagem', label: 'Massagem' },
  { value: 'Depilação', label: 'Depilação' },
  { value: 'Outro', label: 'Outro' },
];

const initialFormData = {
  nome: '',
  descricao: '',
  duracao: '',
  preco: '',
  categoria: ''
};

export function ModalProcedimentos({ loja, onClose, onSuccess }: ModalProcedimentosProps) {
  const toast = useToast();
  const [procedimentos, setProcedimentos] = useState<Procedimento[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingProcedimento, setEditingProcedimento] = useState<Procedimento | null>(null);
  const [formData, setFormData] = useState(initialFormData);
  const [submitting, setSubmitting] = useState(false);

  const loadProcedimentos = useCallback(async () => {
    try {
      setLoading(true);
      setLoadError(false);
      const response = await clinicaApiClient.get('/clinica/procedimentos/');
      setProcedimentos(ensureArray<Procedimento>(response.data));
    } catch (error) {
      console.error('Erro ao carregar procedimentos:', error);
      setLoadError(true);
      toast.error('Erro ao carregar procedimentos. Tente novamente.');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadProcedimentos();
  }, [loadProcedimentos]);

  const handleEdit = (procedimento: Procedimento) => {
    setEditingProcedimento(procedimento);
    setFormData({
      nome: procedimento.nome || '',
      descricao: procedimento.descricao || '',
      duracao: procedimento.duracao?.toString() || '',
      preco: procedimento.preco || '',
      categoria: procedimento.categoria || ''
    });
    setShowForm(true);
  };

  const handleDelete = async (procedimento: Procedimento) => {
    if (!confirm(`Tem certeza que deseja excluir o procedimento ${procedimento.nome}?`)) return;
    
    try {
      await clinicaApiClient.delete(`/clinica/procedimentos/${procedimento.id}/`);
      alert('✅ Procedimento excluído com sucesso!');
      loadProcedimentos();
      onSuccess();
    } catch (error) {
      console.error('Erro ao excluir procedimento:', error);
      alert('❌ Erro ao excluir procedimento');
    }
  };

  const resetForm = () => {
    setFormData(initialFormData);
    setEditingProcedimento(null);
    setShowForm(false);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      const cleanedData = Object.fromEntries(
        Object.entries(formData).map(([key, value]) => [key, value === '' ? null : value])
      );

      if (editingProcedimento) {
        await clinicaApiClient.put(`/clinica/procedimentos/${editingProcedimento.id}/`, cleanedData);
        alert('✅ Procedimento atualizado com sucesso!');
      } else {
        await clinicaApiClient.post('/clinica/procedimentos/', cleanedData);
        alert('✅ Procedimento cadastrado com sucesso!');
      }
      loadProcedimentos();
      onSuccess();
      resetForm();
    } catch (error) {
      console.error('Erro ao salvar procedimento:', error);
      alert('❌ Erro ao salvar procedimento');
    } finally {
      setSubmitting(false);
    }
  };

  if (showForm) {
    return (
      <CrudModal loja={loja} onClose={resetForm} title={editingProcedimento ? 'Editar Procedimento' : 'Novo Procedimento'} icon="💆" maxWidth="2xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="Nome do Procedimento" name="nome" value={formData.nome} onChange={handleChange} required placeholder="Ex: Limpeza de Pele Profunda" colSpan={2} />
            <FormField label="Categoria" name="categoria" type="select" value={formData.categoria} onChange={handleChange} required options={CATEGORIAS} />
            <FormField label="Duração (minutos)" name="duracao" type="number" value={formData.duracao} onChange={handleChange} required min={1} placeholder="60" />
            <FormField label="Preço (R$)" name="preco" type="number" value={formData.preco} onChange={handleChange} required min={0} step={0.01} placeholder="80.00" />
            <FormField label="Descrição" name="descricao" type="textarea" value={formData.descricao} onChange={handleChange} required rows={3} placeholder="Descreva o procedimento e seus benefícios..." colSpan={2} />
          </div>

          <div className="flex justify-end space-x-4 pt-4 border-t">
            <button type="button" onClick={resetForm} disabled={submitting} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">
              Cancelar
            </button>
            <button type="submit" disabled={submitting} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>
              {submitting ? 'Salvando...' : (editingProcedimento ? 'Atualizar' : 'Cadastrar')}
            </button>
          </div>
        </form>
      </CrudModal>
    );
  }

  return (
    <CrudModal loja={loja} onClose={onClose} title="Gerenciar Procedimentos" icon="💆" maxWidth="4xl">
      {loading ? (
        <div className="flex flex-col items-center justify-center py-12 gap-3">
          <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: loja.cor_primaria }} />
          <p className="text-gray-600 dark:text-gray-400">Carregando procedimentos...</p>
        </div>
      ) : loadError ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">Não foi possível carregar os procedimentos</p>
          <button onClick={() => loadProcedimentos()} className="px-6 py-3 rounded-md text-white hover:opacity-90 mt-2" style={{ backgroundColor: loja.cor_primaria }}>
            Tentar novamente
          </button>
        </div>
      ) : procedimentos.length === 0 ? (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <p className="text-lg mb-2 text-gray-700 dark:text-gray-300">Nenhum procedimento cadastrado</p>
          <p className="text-sm mb-4">Cadastre os procedimentos oferecidos pela sua clínica</p>
          <button onClick={() => setShowForm(true)} className="px-6 py-3 rounded-md text-white hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
            + Cadastrar Primeiro Procedimento
          </button>
        </div>
      ) : (
        <div className="space-y-4 mb-6">
          {procedimentos.map((proc) => (
            <div key={proc.id} className="flex items-center justify-between p-4 border dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 bg-white dark:bg-gray-700/30">
              <div className="flex-1">
                <p className="font-semibold text-lg text-gray-900 dark:text-white">{proc.nome}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">{proc.duracao} min • {proc.categoria}</p>
                <p className="text-sm text-gray-700 dark:text-gray-300">{proc.descricao}</p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="font-bold text-lg" style={{ color: loja.cor_primaria }}>{formatCurrency(proc.preco)}</p>
                </div>
                <div className="flex space-x-2">
                  <button onClick={() => handleEdit(proc)} className="px-4 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600">
                    ✏️ Editar
                  </button>
                  <button onClick={() => handleDelete(proc)} className="px-4 py-2 text-sm bg-red-500 text-white rounded-md hover:bg-red-600">
                    🗑️ Excluir
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex justify-end space-x-4">
        <button onClick={onClose} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white">
          Fechar
        </button>
        <button onClick={() => setShowForm(true)} className="px-6 py-2 text-white rounded-md hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
          + Novo Procedimento
        </button>
      </div>
    </CrudModal>
  );
}
