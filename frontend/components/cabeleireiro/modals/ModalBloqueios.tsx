'use client';

import { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/Toast';
import { Modal } from '@/components/ui/Modal';
import { LojaInfo } from '@/types/dashboard';
import { ensureArray } from '@/lib/array-helpers';
import apiClient from '@/lib/api-client';

interface Bloqueio {
  id: number;
  profissional?: { id: number; nome: string };
  data_inicio: string;
  data_fim: string;
  motivo: string;
  observacoes?: string;
}

export function ModalBloqueios({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [bloqueios, setBloqueios] = useState<Bloqueio[]>([]);
  const [profissionais, setProfissionais] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<Bloqueio | null>(null);
  const [formData, setFormData] = useState({
    profissional: '',
    data_inicio: '',
    data_fim: '',
    motivo: '',
    observacoes: ''
  });

  useEffect(() => {
    carregarDados();
  }, []);

  const carregarDados = async () => {
    try {
      setLoading(true);
      const [bloqueiosRes, funcionariosRes] = await Promise.all([
        apiClient.get('/cabeleireiro/bloqueios/'),
        apiClient.get('/cabeleireiro/funcionarios/')  // ✅ Buscar funcionários
      ]);
      setBloqueios(ensureArray(bloqueiosRes.data));
      // ✅ Filtrar apenas funcionários com função 'profissional'
      const todosFuncionarios = ensureArray(funcionariosRes.data);
      const profissionaisAtivos = todosFuncionarios.filter((f: any) => 
        f.funcao === 'profissional' && f.is_active
      );
      setProfissionais(profissionaisAtivos);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = {
        profissional: formData.profissional ? parseInt(formData.profissional) : null,
        data_inicio: formData.data_inicio,
        data_fim: formData.data_fim,
        motivo: formData.motivo,
        observacoes: formData.observacoes
      };

      if (editando) {
        await apiClient.put(`/cabeleireiro/bloqueios/${editando.id}/`, data);
        toast.success('Bloqueio atualizado!');
      } else {
        await apiClient.post('/cabeleireiro/bloqueios/', data);
        toast.success('Bloqueio cadastrado!');
      }
      resetForm();
      carregarDados();
    } catch (error) {
      console.error('Erro ao salvar bloqueio:', error);
      toast.error('Erro ao salvar bloqueio');
    }
  };

  const handleEditar = (bloqueio: Bloqueio) => {
    setEditando(bloqueio);
    setFormData({
      profissional: bloqueio.profissional?.id.toString() || '',
      data_inicio: bloqueio.data_inicio,
      data_fim: bloqueio.data_fim,
      motivo: bloqueio.motivo,
      observacoes: bloqueio.observacoes || ''
    });
    setShowForm(true);
  };

  const handleExcluir = async (bloqueio: Bloqueio) => {
    if (!confirm('Deseja realmente excluir este bloqueio?')) return;
    try {
      await apiClient.delete(`/cabeleireiro/bloqueios/${bloqueio.id}/`);
      toast.success('Bloqueio excluído!');
      carregarDados();
    } catch (error) {
      console.error('Erro ao excluir bloqueio:', error);
      toast.error('Erro ao excluir bloqueio');
    }
  };

  const resetForm = () => {
    setFormData({
      profissional: '',
      data_inicio: '',
      data_fim: '',
      motivo: '',
      observacoes: ''
    });
    setEditando(null);
    setShowForm(false);
  };

  if (showForm) {
    return (
      <Modal isOpen={true} onClose={onClose} maxWidth="2xl">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              {editando ? '✏️ Editar Bloqueio' : '🚫 Novo Bloqueio'}
            </h3>
            <button onClick={resetForm} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1 dark:text-white">Profissional (opcional)</label>
              <select
                value={formData.profissional}
                onChange={(e) => setFormData({ ...formData, profissional: e.target.value })}
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                <option value="">Bloqueio geral (todos os profissionais)</option>
                {profissionais.map(prof => (
                  <option key={prof.id} value={prof.id}>{prof.nome}</option>
                ))}
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Deixe em branco para bloquear a agenda de todos os profissionais
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Data Início *</label>
                <input
                  type="date"
                  value={formData.data_inicio}
                  onChange={(e) => setFormData({ ...formData, data_inicio: e.target.value })}
                  required
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Data Fim *</label>
                <input
                  type="date"
                  value={formData.data_fim}
                  onChange={(e) => setFormData({ ...formData, data_fim: e.target.value })}
                  required
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 dark:text-white">Motivo *</label>
              <input
                type="text"
                value={formData.motivo}
                onChange={(e) => setFormData({ ...formData, motivo: e.target.value })}
                required
                placeholder="Ex: Férias, Folga, Treinamento"
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1 dark:text-white">Observações</label>
              <textarea
                value={formData.observacoes}
                onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
                placeholder="Observações adicionais..."
                rows={3}
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t">
              <button type="button" onClick={resetForm} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">
                Cancelar
              </button>
              <button type="submit" className="px-6 py-2 text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>
                {editando ? 'Atualizar' : 'Cadastrar'}
              </button>
            </div>
          </form>
        </div>
      </Modal>
    );
  }

  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="4xl">
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">🚫 Bloqueios de Agenda</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
        </div>

        {loading ? (
          <p className="text-center text-gray-500 py-8">Carregando bloqueios...</p>
        ) : bloqueios.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-4">Nenhum bloqueio cadastrado</p>
            <button 
              onClick={() => setShowForm(true)} 
              className="px-6 py-3 rounded-lg text-white" 
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Cadastrar Bloqueio
            </button>
          </div>
        ) : (
          <>
            <div className="space-y-3 mb-6 max-h-96 overflow-y-auto">
              {bloqueios.map((bloqueio) => (
                <div key={bloqueio.id} className="flex items-center justify-between p-4 border rounded-lg bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-semibold text-lg dark:text-white">{bloqueio.motivo}</p>
                      {!bloqueio.profissional && (
                        <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 text-xs font-semibold rounded-full">
                          🌐 Bloqueio Geral
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {bloqueio.profissional ? `Profissional: ${bloqueio.profissional.nome}` : 'Todos os profissionais'}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      📅 {new Date(bloqueio.data_inicio).toLocaleDateString('pt-BR')} até {new Date(bloqueio.data_fim).toLocaleDateString('pt-BR')}
                    </p>
                    {bloqueio.observacoes && (
                      <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                        {bloqueio.observacoes}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => handleEditar(bloqueio)} 
                      className="px-4 py-2 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                    >
                      ✏️ Editar
                    </button>
                    <button 
                      onClick={() => handleExcluir(bloqueio)} 
                      className="px-4 py-2 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600"
                    >
                      🗑️ Excluir
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t">
              <button onClick={onClose} className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">
                Fechar
              </button>
              <button 
                onClick={() => setShowForm(true)} 
                className="px-6 py-2 text-white rounded-lg" 
                style={{ backgroundColor: loja.cor_primaria }}
              >
                + Novo Bloqueio
              </button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
