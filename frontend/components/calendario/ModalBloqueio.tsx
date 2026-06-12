'use client';

import { useState } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { logger } from '@/lib/logger';
import { HORARIOS_AGENDAMENTO } from './constants';
import type { LojaInfo, Profissional } from './types';

export function ModalBloqueio({
  loja,
  profissionais,
  profissionalSelecionado,
  onClose,
  onSuccess
}: {
  loja: LojaInfo;
  profissionais: Profissional[];
  profissionalSelecionado: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    tipo: 'periodo', // 'periodo' ou 'dia_completo'
    profissional: '', // Sempre vazio inicialmente - usuário deve escolher explicitamente
    data_inicio: '',
    data_fim: '',
    horario_inicio: '08:00',
    horario_fim: '18:00',
    motivo: ''
  });
  const [loading, setLoading] = useState(false);

  const horarios = [...HORARIOS_AGENDAMENTO];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const bloqueioData: any = {
        titulo: formData.motivo || 'Bloqueio de agenda',
        tipo: formData.tipo === 'dia_completo' ? 'feriado' : 'outros',
        data_inicio: formData.data_inicio,
        data_fim: formData.data_fim,
        observacoes: formData.motivo
      };

      // Adicionar profissional apenas se selecionado
      if (formData.profissional) {
        const profissionalId = parseInt(formData.profissional);
        
        // Validar que o profissional existe na lista carregada
        const profissionalExiste = profissionais.some(p => p.id === profissionalId);
        
        if (!profissionalExiste) {
          alert('❌ Erro: Profissional inválido. Por favor, recarregue a página (Ctrl+Shift+R) e tente novamente.');
          setLoading(false);
          return;
        }
        
        bloqueioData.profissional = profissionalId;
      }

      // Adicionar horários apenas se for período
      if (formData.tipo === 'periodo') {
        bloqueioData.horario_inicio = formData.horario_inicio;
        bloqueioData.horario_fim = formData.horario_fim;
      }

      await clinicaApiClient.post('/clinica/bloqueios/', bloqueioData);
      alert('✅ Bloqueio criado com sucesso!');
      onSuccess();
      onClose();
    } catch (error: any) {
      logger.warn('Erro ao criar bloqueio:', error);
      
      // Mensagem de erro mais detalhada
      const errorMessage = error?.response?.data?.profissional?.[0] || 
                          error?.response?.data?.detail || 
                          'Erro ao criar bloqueio';
      
      alert(`❌ ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="border-b dark:border-gray-700 p-6 flex items-center justify-between">
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
            🚫 Bloquear Horário
          </h3>
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                       hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white"
          >
            ✕ Fechar
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Tipo de Bloqueio */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Tipo de Bloqueio *
              </label>
              <select
                name="tipo"
                value={formData.tipo}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 
                           bg-white dark:bg-gray-700 
                           text-gray-900 dark:text-white 
                           border border-gray-300 dark:border-gray-600 
                           rounded-md"
              >
                <option value="periodo">Período Específico</option>
                <option value="dia_completo">Dia Completo</option>
              </select>
            </div>

            {/* Profissional */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Profissional
              </label>
              <select
                name="profissional"
                value={formData.profissional}
                onChange={handleChange}
                className="w-full px-3 py-2 
                           bg-white dark:bg-gray-700 
                           text-gray-900 dark:text-white 
                           border border-gray-300 dark:border-gray-600 
                           rounded-md"
              >
                <option value="">Todos os profissionais</option>
                {profissionais.map(prof => (
                  <option key={prof.id} value={prof.id}>
                    {prof.nome}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Deixe em branco para bloquear para todos
              </p>
            </div>

            {/* Data Início */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data Início *
              </label>
              <input
                type="date"
                name="data_inicio"
                value={formData.data_inicio}
                onChange={handleChange}
                required
                min={new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 
                           bg-white dark:bg-gray-700 
                           text-gray-900 dark:text-white 
                           border border-gray-300 dark:border-gray-600 
                           rounded-md"
              />
            </div>

            {/* Data Fim */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data Fim *
              </label>
              <input
                type="date"
                name="data_fim"
                value={formData.data_fim}
                onChange={handleChange}
                required
                min={formData.data_inicio || new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 
                           bg-white dark:bg-gray-700 
                           text-gray-900 dark:text-white 
                           border border-gray-300 dark:border-gray-600 
                           rounded-md"
              />
            </div>

            {/* Horário Início (apenas para período) */}
            {formData.tipo === 'periodo' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Horário Início *
                  </label>
                  <select
                    name="horario_inicio"
                    value={formData.horario_inicio}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 
                               bg-white dark:bg-gray-700 
                               text-gray-900 dark:text-white 
                               border border-gray-300 dark:border-gray-600 
                               rounded-md"
                  >
                    {horarios.map(hora => (
                      <option key={hora} value={hora}>{hora}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Horário Fim *
                  </label>
                  <select
                    name="horario_fim"
                    value={formData.horario_fim}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 
                               bg-white dark:bg-gray-700 
                               text-gray-900 dark:text-white 
                               border border-gray-300 dark:border-gray-600 
                               rounded-md"
                  >
                    {horarios.map(hora => (
                      <option key={hora} value={hora}>{hora}</option>
                    ))}
                  </select>
                </div>
              </>
            )}

            {/* Motivo */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Motivo do Bloqueio *
              </label>
              <textarea
                name="motivo"
                value={formData.motivo}
                onChange={handleChange}
                required
                rows={3}
                className="w-full px-3 py-2 
                           bg-white dark:bg-gray-700 
                           text-gray-900 dark:text-white 
                           border border-gray-300 dark:border-gray-600 
                           rounded-md 
                           resize-none"
                placeholder="Ex: Férias, Reunião, Treinamento..."
              />
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 
                         border border-gray-300 dark:border-gray-600 
                         rounded-md 
                         hover:bg-gray-50 dark:hover:bg-gray-700 
                         disabled:opacity-50 
                         text-gray-900 dark:text-white"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              {loading ? 'Criando...' : '🚫 Criar Bloqueio'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
