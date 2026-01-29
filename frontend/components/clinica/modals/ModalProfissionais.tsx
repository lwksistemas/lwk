'use client';

import { useState, useEffect, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';
import { CrudModal } from '../shared/CrudModal';
import { FormField } from '../shared/FormField';
import type { LojaInfo } from '../shared/CrudModal';

interface Profissional {
  id: number;
  nome: string;
  email: string;
  telefone: string;
  especialidade: string;
  registro_profissional?: string;
}

interface ModalProfissionaisProps {
  loja: LojaInfo;
  onClose: () => void;
}

const ESPECIALIDADES = [
  { value: 'Esteticista', label: 'Esteticista' },
  { value: 'Massoterapeuta', label: 'Massoterapeuta' },
  { value: 'Dermatologista', label: 'Dermatologista' },
  { value: 'Fisioterapeuta', label: 'Fisioterapeuta' },
  { value: 'Cosmetólogo(a)', label: 'Cosmetólogo(a)' },
  { value: 'Maquiador(a)', label: 'Maquiador(a)' },
  { value: 'Outro', label: 'Outro' },
];

const initialFormData = {
  nome: '',
  email: '',
  telefone: '',
  especialidade: '',
  registro_profissional: ''
};

export function ModalProfissionais({ loja, onClose }: ModalProfissionaisProps) {
  const toast = useToast();
  const [profissionais, setProfissionais] = useState<Profissional[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingProfissional, setEditingProfissional] = useState<Profissional | null>(null);
  const [formData, setFormData] = useState(initialFormData);
  const [submitting, setSubmitting] = useState(false);

  const loadProfissionais = useCallback(async () => {
    try {
      setLoading(true);
      setLoadError(false);
      const response = await clinicaApiClient.get('/clinica/profissionais/');
      setProfissionais(response.data ?? []);
    } catch (error) {
      console.error('Erro ao carregar profissionais:', error);
      setLoadError(true);
      toast.error('Erro ao carregar profissionais. Tente novamente.');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadProfissionais();
  }, [loadProfissionais]);

  const handleEdit = (profissional: Profissional) => {
    setEditingProfissional(profissional);
    setFormData({
      nome: profissional.nome || '',
      email: profissional.email || '',
      telefone: profissional.telefone || '',
      especialidade: profissional.especialidade || '',
      registro_profissional: profissional.registro_profissional || ''
    });
    setShowForm(true);
  };

  const handleDelete = async (profissional: Profissional) => {
    if (!confirm(`Tem certeza que deseja excluir o profissional ${profissional.nome}?`)) return;
    
    try {
      await clinicaApiClient.delete(`/clinica/profissionais/${profissional.id}/`);
      alert('✅ Profissional excluído com sucesso!');
      loadProfissionais();
    } catch (error) {
      console.error('Erro ao excluir profissional:', error);
      alert('❌ Erro ao excluir profissional');
    }
  };

  const resetForm = () => {
    setFormData(initialFormData);
    setEditingProfissional(null);
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

      if (editingProfissional) {
        await clinicaApiClient.put(`/clinica/profissionais/${editingProfissional.id}/`, cleanedData);
        alert('✅ Profissional atualizado com sucesso!');
      } else {
        await clinicaApiClient.post('/clinica/profissionais/', cleanedData);
        alert('✅ Profissional cadastrado com sucesso!');
      }
      loadProfissionais();
      resetForm();
    } catch (error) {
      console.error('Erro ao salvar profissional:', error);
      alert('❌ Erro ao salvar profissional');
    } finally {
      setSubmitting(false);
    }
  };

  if (showForm) {
    return (
      <CrudModal loja={loja} onClose={resetForm} title={editingProfissional ? 'Editar Profissional' : 'Novo Profissional'} icon="👨‍⚕️" maxWidth="2xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="Nome Completo" name="nome" value={formData.nome} onChange={handleChange} required placeholder="Ex: Dr. João Silva" colSpan={2} />
            <FormField label="Email" name="email" type="email" value={formData.email} onChange={handleChange} required placeholder="email@exemplo.com" />
            <FormField label="Telefone" name="telefone" type="tel" value={formData.telefone} onChange={handleChange} required placeholder="(00) 00000-0000" />
            <FormField label="Especialidade" name="especialidade" type="select" value={formData.especialidade} onChange={handleChange} required options={ESPECIALIDADES} />
            <FormField label="Registro Profissional" name="registro_profissional" value={formData.registro_profissional} onChange={handleChange} placeholder="Ex: CRF 12345" />
          </div>

          <div className="flex justify-end space-x-4 pt-4 border-t">
            <button type="button" onClick={resetForm} disabled={submitting} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">
              Cancelar
            </button>
            <button type="submit" disabled={submitting} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>
              {submitting ? 'Salvando...' : (editingProfissional ? 'Atualizar' : 'Cadastrar')}
            </button>
          </div>
        </form>
      </CrudModal>
    );
  }

  return (
    <CrudModal loja={loja} onClose={onClose} title="Gerenciar Profissionais" icon="👨‍⚕️" maxWidth="4xl" fullScreen>
      {loading ? (
        <div className="flex flex-col items-center justify-center py-12 gap-3">
          <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: loja.cor_primaria }} />
          <p className="text-gray-600 dark:text-gray-400">Carregando profissionais...</p>
        </div>
      ) : loadError ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">Não foi possível carregar os profissionais</p>
          <button onClick={() => loadProfissionais()} className="px-6 py-3 rounded-md text-white hover:opacity-90 mt-2" style={{ backgroundColor: loja.cor_primaria }}>
            Tentar novamente
          </button>
        </div>
      ) : profissionais.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">Nenhum profissional cadastrado</p>
          <p className="text-sm mb-4">Comece adicionando seu primeiro profissional</p>
          <button onClick={() => setShowForm(true)} className="px-6 py-3 rounded-md text-white hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
            + Cadastrar Primeiro Profissional
          </button>
        </div>
      ) : (
        <div className="space-y-4 mb-6">
          {profissionais.map((profissional) => (
            <div key={profissional.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold" style={{ backgroundColor: loja.cor_primaria }}>
                    {profissional.nome.charAt(0)}
                  </div>
                  <div>
                    <p className="font-semibold text-lg">{profissional.nome}</p>
                    <p className="text-sm text-gray-600">{profissional.especialidade}</p>
                    <p className="text-xs text-gray-500">{profissional.email} • {profissional.telefone}</p>
                    {profissional.registro_profissional && (
                      <p className="text-xs text-gray-500">Registro: {profissional.registro_profissional}</p>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex space-x-2">
                <button onClick={() => handleEdit(profissional)} className="px-4 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600">
                  ✏️ Editar
                </button>
                <button onClick={() => handleDelete(profissional)} className="px-4 py-2 text-sm bg-red-500 text-white rounded-md hover:bg-red-600">
                  🗑️ Excluir
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex justify-end space-x-4">
        <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
          Fechar
        </button>
        {profissionais.length > 0 && (
          <button onClick={() => setShowForm(true)} className="px-6 py-2 text-white rounded-md hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
            + Novo Profissional
          </button>
        )}
      </div>
    </CrudModal>
  );
}
