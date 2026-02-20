'use client';

import { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/Toast';
import { Modal } from '@/components/ui/Modal';
import { LojaInfo } from '@/types/dashboard';
import { ensureArray } from '@/lib/array-helpers';
import apiClient from '@/lib/api-client';

interface Horario {
  id: number;
  dia_semana: number;
  dia_semana_display: string;
  horario_abertura: string;
  horario_fechamento: string;
  is_active: boolean;
}

export function ModalHorarios({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [horarios, setHorarios] = useState<Horario[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<Horario | null>(null);
  const [formData, setFormData] = useState({
    dia_semana: '0',
    horario_abertura: '08:00',
    horario_fechamento: '18:00'
  });

  const diasSemana = [
    { value: 0, label: 'Segunda-feira' },
    { value: 1, label: 'Terça-feira' },
    { value: 2, label: 'Quarta-feira' },
    { value: 3, label: 'Quinta-feira' },
    { value: 4, label: 'Sexta-feira' },
    { value: 5, label: 'Sábado' },
    { value: 6, label: 'Domingo' }
  ];

  useEffect(() => {
    carregarHorarios();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const carregarHorarios = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/cabeleireiro/horarios/');
      setHorarios(ensureArray(response.data));
    } catch (error) {
      console.error('Erro ao carregar horários:', error);
      toast.error('Erro ao carregar horários');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = {
        dia_semana: parseInt(formData.dia_semana),
        horario_abertura: formData.horario_abertura,
        horario_fechamento: formData.horario_fechamento
      };

      if (editando) {
        await apiClient.put(`/cabeleireiro/horarios/${editando.id}/`, data);
        toast.success('Horário atualizado!');
      } else {
        await apiClient.post('/cabeleireiro/horarios/', data);
        toast.success('Horário cadastrado!');
      }
      resetForm();
      carregarHorarios();
    } catch (error) {
      console.error('Erro ao salvar horário:', error);
      toast.error('Erro ao salvar horário');
    }
  };

  const handleEditar = (horario: Horario) => {
    setEditando(horario);
    setFormData({
      dia_semana: horario.dia_semana.toString(),
      horario_abertura: horario.horario_abertura,
      horario_fechamento: horario.horario_fechamento
    });
    setShowForm(true);
  };

  const handleExcluir = async (horario: Horario) => {
    if (!confirm(`Deseja realmente excluir o horário de ${horario.dia_semana_display}?`)) return;
    try {
      await apiClient.delete(`/cabeleireiro/horarios/${horario.id}/`);
      toast.success('Horário excluído!');
      carregarHorarios();
    } catch (error) {
      console.error('Erro ao excluir horário:', error);
      toast.error('Erro ao excluir horário');
    }
  };

  const resetForm = () => {
    setFormData({
      dia_semana: '0',
      horario_abertura: '08:00',
      horario_fechamento: '18:00'
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
              {editando ? '✏️ Editar Horário' : '🕐 Novo Horário'}
            </h3>
            <button onClick={resetForm} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1 dark:text-white">Dia da Semana *</label>
              <select
                value={formData.dia_semana}
                onChange={(e) => setFormData({ ...formData, dia_semana: e.target.value })}
                required
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                {diasSemana.map(dia => (
                  <option key={dia.value} value={dia.value}>{dia.label}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Horário de Abertura *</label>
                <input
                  type="time"
                  value={formData.horario_abertura}
                  onChange={(e) => setFormData({ ...formData, horario_abertura: e.target.value })}
                  required
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 dark:text-white">Horário de Fechamento *</label>
                <input
                  type="time"
                  value={formData.horario_fechamento}
                  onChange={(e) => setFormData({ ...formData, horario_fechamento: e.target.value })}
                  required
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
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
    <Modal isOpen={true} onClose={onClose} maxWidth="3xl">
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white">🕐 Horários de Funcionamento</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-2 rounded">✕</button>
        </div>

        {loading ? (
          <p className="text-center text-gray-500 py-8">Carregando horários...</p>
        ) : horarios.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-4">Nenhum horário configurado</p>
            <button 
              onClick={() => setShowForm(true)} 
              className="px-6 py-3 rounded-lg text-white" 
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Configurar Horário
            </button>
          </div>
        ) : (
          <>
            <div className="space-y-3 mb-6">
              {horarios.map((horario) => (
                <div key={horario.id} className="flex items-center justify-between p-4 border rounded-lg bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                  <div className="flex-1">
                    <p className="font-semibold text-lg dark:text-white">{horario.dia_semana_display}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      🕐 {horario.horario_abertura} às {horario.horario_fechamento}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => handleEditar(horario)} 
                      className="px-4 py-2 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                    >
                      ✏️ Editar
                    </button>
                    <button 
                      onClick={() => handleExcluir(horario)} 
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
                + Novo Horário
              </button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
