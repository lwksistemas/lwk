'use client';

import { useState, useEffect, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { CrudModal } from '../shared/CrudModal';
import { FormField } from '../shared/FormField';
import type { LojaInfo } from '../shared/CrudModal';

interface Funcionario {
  id: number;
  nome: string;
  email: string;
  telefone: string;
  cargo: string;
  is_admin?: boolean;
}

interface ModalFuncionariosProps {
  loja: LojaInfo;
  onClose: () => void;
}

const initialFormData = {
  nome: '',
  email: '',
  telefone: '',
  cargo: ''
};

export function ModalFuncionarios({ loja, onClose }: ModalFuncionariosProps) {
  const [funcionarios, setFuncionarios] = useState<Funcionario[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingFuncionario, setEditingFuncionario] = useState<Funcionario | null>(null);
  const [formData, setFormData] = useState(initialFormData);
  const [submitting, setSubmitting] = useState(false);

  const loadFuncionarios = useCallback(async () => {
    try {
      const response = await clinicaApiClient.get('/clinica/funcionarios/');
      setFuncionarios(response.data);
    } catch (error) {
      console.error('Erro ao carregar funcionários:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFuncionarios();
  }, [loadFuncionarios]);

  const handleEdit = (funcionario: Funcionario) => {
    setEditingFuncionario(funcionario);
    setFormData({
      nome: funcionario.nome || '',
      email: funcionario.email || '',
      telefone: funcionario.telefone || '',
      cargo: funcionario.cargo || ''
    });
    setShowForm(true);
  };

  const handleDelete = async (funcionario: Funcionario) => {
    if (!confirm(`Tem certeza que deseja excluir o funcionário ${funcionario.nome}?`)) return;
    
    try {
      await clinicaApiClient.delete(`/clinica/funcionarios/${funcionario.id}/`);
      alert('✅ Funcionário excluído com sucesso!');
      loadFuncionarios();
    } catch (error) {
      console.error('Erro ao excluir funcionário:', error);
      alert('❌ Erro ao excluir funcionário');
    }
  };

  const resetForm = () => {
    setFormData(initialFormData);
    setEditingFuncionario(null);
    setShowForm(false);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      if (editingFuncionario) {
        await clinicaApiClient.put(`/clinica/funcionarios/${editingFuncionario.id}/`, formData);
        alert('✅ Funcionário atualizado com sucesso!');
      } else {
        await clinicaApiClient.post('/clinica/funcionarios/', formData);
        alert('✅ Funcionário cadastrado com sucesso!');
      }
      loadFuncionarios();
      resetForm();
    } catch (error) {
      console.error('Erro ao salvar funcionário:', error);
      alert('❌ Erro ao salvar funcionário');
    } finally {
      setSubmitting(false);
    }
  };

  if (showForm) {
    return (
      <CrudModal loja={loja} onClose={resetForm} title={editingFuncionario ? 'Editar Funcionário' : 'Novo Funcionário'} icon="👥" maxWidth="2xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="Nome Completo" name="nome" value={formData.nome} onChange={handleChange} required placeholder="Ex: Maria Silva" colSpan={2} />
            <FormField label="Email" name="email" type="email" value={formData.email} onChange={handleChange} required placeholder="email@exemplo.com" />
            <FormField label="Telefone" name="telefone" type="tel" value={formData.telefone} onChange={handleChange} required placeholder="(00) 00000-0000" />
            <FormField label="Cargo" name="cargo" value={formData.cargo} onChange={handleChange} required placeholder="Ex: Recepcionista, Auxiliar, etc." colSpan={2} />
          </div>

          <div className="flex justify-end space-x-4 pt-4 border-t">
            <button type="button" onClick={resetForm} disabled={submitting} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">
              Cancelar
            </button>
            <button type="submit" disabled={submitting} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>
              {submitting ? 'Salvando...' : (editingFuncionario ? 'Atualizar' : 'Cadastrar')}
            </button>
          </div>
        </form>
      </CrudModal>
    );
  }

  return (
    <CrudModal loja={loja} onClose={onClose} title="Gerenciar Funcionários" icon="👥" maxWidth="4xl" fullScreen>
      {loading ? (
        <div className="text-center py-8">Carregando funcionários...</div>
      ) : funcionarios.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">Nenhum funcionário cadastrado</p>
          <p className="text-sm mb-4">O administrador da loja é automaticamente cadastrado como funcionário</p>
          <button onClick={() => setShowForm(true)} className="px-6 py-3 rounded-md text-white hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
            + Cadastrar Funcionário
          </button>
        </div>
      ) : (
        <div className="space-y-4 mb-6">
          {funcionarios.map((func) => (
            <div key={func.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <p className="font-semibold text-lg">{func.nome}</p>
                  {func.is_admin && (
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full">
                      👤 Administrador
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600">{func.cargo}</p>
                <p className="text-sm text-gray-600">{func.email} • {func.telefone}</p>
              </div>
              <div className="flex space-x-2">
                <button onClick={() => handleEdit(func)} className="px-4 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600">
                  ✏️ Editar
                </button>
                {!func.is_admin && (
                  <button onClick={() => handleDelete(func)} className="px-4 py-2 text-sm bg-red-500 text-white rounded-md hover:bg-red-600">
                    🗑️ Excluir
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex justify-end space-x-4">
        <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
          Fechar
        </button>
        <button onClick={() => setShowForm(true)} className="px-6 py-2 text-white rounded-md hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
          + Novo Funcionário
        </button>
      </div>
    </CrudModal>
  );
}
