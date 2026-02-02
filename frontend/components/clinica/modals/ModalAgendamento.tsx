'use client';

import { useState, useEffect, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { CrudModal } from '../shared/CrudModal';
import { FormField } from '../shared/FormField';
import type { LojaInfo } from '../shared/CrudModal';

interface Cliente {
  id: number;
  nome: string;
  telefone: string;
}

interface Profissional {
  id: number;
  nome: string;
  especialidade: string;
}

interface Procedimento {
  id: number;
  nome: string;
  preco: string;
}

interface ModalAgendamentoProps {
  loja: LojaInfo;
  onClose: () => void;
  onSuccess: () => void;
}

const HORARIOS = [
  { value: '08:00', label: '08:00' },
  { value: '08:30', label: '08:30' },
  { value: '09:00', label: '09:00' },
  { value: '09:30', label: '09:30' },
  { value: '10:00', label: '10:00' },
  { value: '10:30', label: '10:30' },
  { value: '11:00', label: '11:00' },
  { value: '11:30', label: '11:30' },
  { value: '12:00', label: '12:00' },
  { value: '12:30', label: '12:30' },
  { value: '13:00', label: '13:00' },
  { value: '13:30', label: '13:30' },
  { value: '14:00', label: '14:00' },
  { value: '14:30', label: '14:30' },
  { value: '15:00', label: '15:00' },
  { value: '15:30', label: '15:30' },
  { value: '16:00', label: '16:00' },
  { value: '16:30', label: '16:30' },
  { value: '17:00', label: '17:00' },
  { value: '17:30', label: '17:30' },
  { value: '18:00', label: '18:00' },
  { value: '18:30', label: '18:30' },
  { value: '19:00', label: '19:00' },
];

import { ensureArray } from '@/lib/array-helpers';

const initialFormData = {
  cliente: '',
  profissional: '',
  procedimento: '',
  data: '',
  horario: '',
  valor: '',
  observacoes: ''
};

export function ModalAgendamento({ loja, onClose, onSuccess }: ModalAgendamentoProps) {
  const [formData, setFormData] = useState(initialFormData);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [profissionais, setProfissionais] = useState<Profissional[]>([]);
  const [procedimentos, setProcedimentos] = useState<Procedimento[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);

  const loadFormData = useCallback(async () => {
    try {
      const [clientesRes, profissionaisRes, procedimentosRes] = await Promise.all([
        clinicaApiClient.get('/clinica/clientes/'),
        clinicaApiClient.get('/clinica/profissionais/'),
        clinicaApiClient.get('/clinica/procedimentos/')
      ]);
      
      setClientes(ensureArray(clientesRes.data));
      setProfissionais(ensureArray(profissionaisRes.data));
      setProcedimentos(ensureArray(procedimentosRes.data));
    } catch (error) {
      console.error('Erro ao carregar dados do formulário:', error);
    } finally {
      setLoadingData(false);
    }
  }, []);

  useEffect(() => {
    loadFormData();
  }, [loadFormData]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Auto-preencher valor quando procedimento for selecionado
    if (name === 'procedimento' && value) {
      const procedimento = procedimentos.find(p => p.id.toString() === value);
      if (procedimento) {
        setFormData(prev => ({
          ...prev,
          valor: procedimento.preco
        }));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const cleanedData = Object.fromEntries(
        Object.entries(formData).map(([key, value]) => [key, value === '' ? null : value])
      );

      await clinicaApiClient.post('/clinica/agendamentos/', cleanedData);
      alert('✅ Agendamento criado com sucesso!');
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Erro ao criar agendamento:', error);
      alert('❌ Erro ao criar agendamento');
    } finally {
      setLoading(false);
    }
  };

  const clientesOptions = clientes.map(c => ({ value: c.id, label: `${c.nome} - ${c.telefone}` }));
  const profissionaisOptions = profissionais.map(p => ({ value: p.id, label: `${p.nome} - ${p.especialidade}` }));
  const procedimentosOptions = procedimentos.map(p => ({ value: p.id, label: `${p.nome} - R$ ${p.preco}` }));

  if (loadingData) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="text-center">Carregando formulário...</div>
        </div>
      </div>
    );
  }

  return (
    <CrudModal loja={loja} onClose={onClose} title="Novo Agendamento" icon="📅" maxWidth="2xl">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField label="Cliente" name="cliente" type="select" value={formData.cliente} onChange={handleChange} required options={clientesOptions} />
          <FormField label="Profissional" name="profissional" type="select" value={formData.profissional} onChange={handleChange} required options={profissionaisOptions} />
          <FormField label="Procedimento" name="procedimento" type="select" value={formData.procedimento} onChange={handleChange} required options={procedimentosOptions} />
          <FormField label="Data" name="data" type="date" value={formData.data} onChange={handleChange} required />
          <FormField label="Horário" name="horario" type="select" value={formData.horario} onChange={handleChange} required options={HORARIOS} />
          <FormField label="Valor (R$)" name="valor" type="number" value={formData.valor} onChange={handleChange} required min={0} step={0.01} placeholder="0.00" />
          <FormField label="Observações" name="observacoes" type="textarea" value={formData.observacoes} onChange={handleChange} rows={3} placeholder="Informações adicionais sobre o agendamento..." colSpan={2} />
        </div>

        <div className="flex justify-end space-x-4 pt-4">
          <button type="button" onClick={onClose} disabled={loading} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">
            Cancelar
          </button>
          <button type="submit" disabled={loading} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>
            {loading ? 'Criando...' : 'Criar Agendamento'}
          </button>
        </div>
      </form>
    </CrudModal>
  );
}
