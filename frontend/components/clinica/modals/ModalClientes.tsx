'use client';
import { ensureArray } from '@/lib/array-helpers';

import { useState, useEffect, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';
import { CrudModal } from '../shared/CrudModal';
import { FormField } from '../shared/FormField';
import { ESTADOS_BRASIL } from '../constants/estados-brasil';
import type { LojaInfo } from '../shared/CrudModal';

interface Cliente {
  id: number;
  nome: string;
  email: string;
  telefone: string;
  cpf?: string;
  data_nascimento?: string;
  endereco?: string;
  cidade?: string;
  estado?: string;
  observacoes?: string;
}

interface ModalClientesProps {
  loja: LojaInfo;
  onClose: () => void;
  onSuccess: () => void;
}

const initialFormData = {
  nome: '',
  email: '',
  telefone: '',
  cpf: '',
  data_nascimento: '',
  endereco: '',
  cidade: '',
  estado: '',
  observacoes: ''
};

export function ModalClientes({ loja, onClose, onSuccess }: ModalClientesProps) {
  const toast = useToast();
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingCliente, setEditingCliente] = useState<Cliente | null>(null);
  const [formData, setFormData] = useState(initialFormData);
  const [submitting, setSubmitting] = useState(false);

  const loadClientes = useCallback(async () => {
    try {
      setLoading(true);
      setLoadError(false);
      const response = await clinicaApiClient.get('/clinica/clientes/');
      setClientes(ensureArray(response.data));
    } catch (error) {
      console.error('Erro ao carregar clientes:', error);
      setLoadError(true);
      toast.error('Erro ao carregar clientes. Tente novamente.');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadClientes();
  }, [loadClientes]);

  const handleEdit = (cliente: Cliente) => {
    setEditingCliente(cliente);
    setFormData({
      nome: cliente.nome || '',
      email: cliente.email || '',
      telefone: cliente.telefone || '',
      cpf: cliente.cpf || '',
      data_nascimento: cliente.data_nascimento || '',
      endereco: cliente.endereco || '',
      cidade: cliente.cidade || '',
      estado: cliente.estado || '',
      observacoes: cliente.observacoes || ''
    });
    setShowForm(true);
  };

  const handleDelete = async (cliente: Cliente) => {
    if (!confirm(`Tem certeza que deseja excluir o cliente ${cliente.nome}?`)) return;
    
    try {
      await clinicaApiClient.delete(`/clinica/clientes/${cliente.id}/`);
      alert('✅ Cliente excluído com sucesso!');
      loadClientes();
      onSuccess();
    } catch (error) {
      console.error('Erro ao excluir cliente:', error);
      alert('❌ Erro ao excluir cliente');
    }
  };

  const resetForm = () => {
    setFormData(initialFormData);
    setEditingCliente(null);
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
        Object.entries(formData).map(([key, value]) => {
          if ((key === 'data_nascimento' || key.includes('data')) && value === '') {
            return [key, null];
          }
          return [key, value === '' ? null : value];
        })
      );

      if (editingCliente) {
        await clinicaApiClient.put(`/clinica/clientes/${editingCliente.id}/`, cleanedData);
        alert('✅ Cliente atualizado com sucesso!');
      } else {
        await clinicaApiClient.post('/clinica/clientes/', cleanedData);
        alert('✅ Cliente cadastrado com sucesso!');
      }
      loadClientes();
      onSuccess();
      resetForm();
    } catch (error: unknown) {
      console.error('Erro ao salvar cliente:', error);
      let errorMessage = '❌ Erro ao salvar cliente';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: Record<string, unknown> } };
        if (axiosError.response?.data && typeof axiosError.response.data === 'object') {
          const errorFields = Object.keys(axiosError.response.data);
          if (errorFields.length > 0) {
            errorMessage += `\nCampos com erro: ${errorFields.join(', ')}`;
          }
        }
      }
      alert(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  const estadosOptions = ESTADOS_BRASIL.map(uf => ({ value: uf, label: uf }));

  // Formulário de cadastro/edição
  if (showForm) {
    return (
      <CrudModal loja={loja} onClose={resetForm} title={editingCliente ? 'Editar Cliente' : 'Novo Cliente'} icon="👤" fullScreen>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Dados Pessoais</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField label="Nome Completo" name="nome" value={formData.nome} onChange={handleChange} required placeholder="Ex: Maria Silva Santos" colSpan={2} />
              <FormField label="Email" name="email" type="email" value={formData.email} onChange={handleChange} required placeholder="email@exemplo.com" />
              <FormField label="Telefone" name="telefone" type="tel" value={formData.telefone} onChange={handleChange} required placeholder="(00) 00000-0000" />
              <FormField label="CPF" name="cpf" value={formData.cpf} onChange={handleChange} placeholder="000.000.000-00" />
              <FormField label="Data de Nascimento" name="data_nascimento" type="date" value={formData.data_nascimento} onChange={handleChange} />
            </div>
          </div>
          
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Endereço</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <FormField label="Endereço Completo" name="endereco" value={formData.endereco} onChange={handleChange} placeholder="Rua, número, bairro" />
              </div>
              <FormField label="Estado" name="estado" type="select" value={formData.estado} onChange={handleChange} options={estadosOptions} />
              <div className="md:col-span-3">
                <FormField label="Cidade" name="cidade" value={formData.cidade} onChange={handleChange} placeholder="Ex: São Paulo" />
              </div>
            </div>
          </div>
          
          <FormField label="Observações" name="observacoes" type="textarea" value={formData.observacoes} onChange={handleChange} placeholder="Informações adicionais sobre o cliente (alergias, preferências, etc.)" rows={3} />
          
          <div className="flex justify-end space-x-4 pt-4 border-t">
            <button type="button" onClick={resetForm} disabled={submitting} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">
              Cancelar
            </button>
            <button type="submit" disabled={submitting} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>
              {submitting ? 'Salvando...' : (editingCliente ? 'Atualizar' : 'Cadastrar')}
            </button>
          </div>
        </form>
      </CrudModal>
    );
  }

  // Lista de clientes
  return (
    <CrudModal loja={loja} onClose={onClose} title="Gerenciar Clientes" icon="👥" maxWidth="4xl" fullScreen>
      {loading ? (
        <div className="flex flex-col items-center justify-center py-12 gap-3">
          <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: loja.cor_primaria }} />
          <p className="text-gray-600 dark:text-gray-400">Carregando clientes...</p>
        </div>
      ) : loadError ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">Não foi possível carregar os clientes</p>
          <button onClick={() => loadClientes()} className="px-6 py-3 rounded-md text-white hover:opacity-90 mt-2" style={{ backgroundColor: loja.cor_primaria }}>
            Tentar novamente
          </button>
        </div>
      ) : clientes.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">Nenhum cliente cadastrado</p>
          <p className="text-sm mb-4">Comece adicionando seu primeiro cliente</p>
          <button onClick={() => setShowForm(true)} className="px-6 py-3 rounded-md text-white hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
            + Cadastrar Primeiro Cliente
          </button>
        </div>
      ) : (
        <div className="space-y-4 mb-6">
          {clientes.map((cliente) => (
            <div key={cliente.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold" style={{ backgroundColor: loja.cor_primaria }}>
                    {cliente.nome.charAt(0)}
                  </div>
                  <div>
                    <p className="font-semibold text-lg">{cliente.nome}</p>
                    <p className="text-sm text-gray-600">{cliente.email} • {cliente.telefone}</p>
                    {cliente.cidade && cliente.estado && (
                      <p className="text-xs text-gray-500">{cliente.cidade}, {cliente.estado}</p>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex space-x-2">
                <button onClick={() => handleEdit(cliente)} className="px-4 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600">
                  ✏️ Editar
                </button>
                <button onClick={() => handleDelete(cliente)} className="px-4 py-2 text-sm bg-red-500 text-white rounded-md hover:bg-red-600">
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
        {clientes.length > 0 && (
          <button onClick={() => setShowForm(true)} className="px-6 py-2 text-white rounded-md hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>
            + Novo Cliente
          </button>
        )}
      </div>
    </CrudModal>
  );
}
