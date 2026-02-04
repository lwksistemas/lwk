'use client';

import { useState, useEffect } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';
import { ModalBase } from './ModalBase';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

const STATUS_AGENDAMENTO = [
  { value: 'agendado', label: 'Agendado' },
  { value: 'confirmado', label: 'Confirmado' },
  { value: 'em_andamento', label: 'Em Andamento' },
  { value: 'concluido', label: 'Concluído' },
  { value: 'cancelado', label: 'Cancelado' }
];

export function ModalAgendamentos({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const [clientes, setClientes] = useState<any[]>([]);
  const [servicos, setServicos] = useState<any[]>([]);
  const [profissionais, setProfissionais] = useState<any[]>([]);

  useEffect(() => {
    const loadDados = async () => {
      try {
        const [cliRes, servRes, profRes] = await Promise.all([
          clinicaApiClient.get('/servicos/clientes/'),
          clinicaApiClient.get('/servicos/servicos/'),
          clinicaApiClient.get('/servicos/profissionais/')
        ]);
        setClientes(Array.isArray(cliRes.data) ? cliRes.data : cliRes.data?.results ?? []);
        setServicos(Array.isArray(servRes.data) ? servRes.data : servRes.data?.results ?? []);
        setProfissionais(Array.isArray(profRes.data) ? profRes.data : profRes.data?.results ?? []);
      } catch (error) {
        console.error('Erro ao carregar dados:', error);
      }
    };
    loadDados();
  }, []);

  return (
    <ModalBase
      loja={loja}
      onClose={onClose}
      onSuccess={onSuccess}
      title="Agendamento"
      icon="📅"
      endpoint="/servicos/agendamentos/"
      formFields={[
        { name: 'cliente_id', apiName: 'cliente', label: 'Cliente', type: 'select', required: true, options: clientes.map(c => ({ value: c.id, label: c.nome })), fullWidth: true, transform: (v: string) => parseInt(v), getValue: (item: any) => String(item.cliente) },
        { name: 'servico_id', apiName: 'servico', label: 'Serviço', type: 'select', required: true, options: servicos.map(s => ({ value: s.id, label: s.nome })), transform: (v: string) => parseInt(v), getValue: (item: any) => String(item.servico) },
        { name: 'profissional_id', apiName: 'profissional', label: 'Profissional', type: 'select', options: profissionais.map(p => ({ value: p.id, label: p.nome })), transform: (v: string) => v ? parseInt(v) : null, getValue: (item: any) => item.profissional ? String(item.profissional) : '' },
        { name: 'data', label: 'Data', type: 'date', required: true },
        { name: 'horario', label: 'Horário', type: 'time', required: true },
        { name: 'status', label: 'Status', type: 'select', required: true, options: STATUS_AGENDAMENTO, defaultValue: 'agendado' },
        { name: 'valor', label: 'Valor (R$)', type: 'number', required: true, min: 0, step: 0.01, transform: (v: string) => parseFloat(v) },
        { name: 'endereco_atendimento', label: 'Endereço de Atendimento', type: 'text', fullWidth: true, placeholder: 'Se o serviço for no local do cliente', transform: (v: string) => v || null },
        { name: 'observacoes', label: 'Observações', type: 'textarea', fullWidth: true, transform: (v: string) => v || null }
      ]}
      renderListItem={(item: any, handleEditar: any, handleExcluir: any, loja: any) => (
        <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
          <div className="flex-1">
            <p className="font-semibold text-lg text-gray-900 dark:text-white">{item.cliente_nome}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{item.servico_nome} • {item.data} {item.horario}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{item.profissional_nome || 'Sem profissional'}</p>
            <span className="inline-block mt-2 px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-semibold rounded-full">{STATUS_AGENDAMENTO.find(s => s.value === item.status)?.label}</span>
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleEditar(item)} className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
            <button onClick={() => handleExcluir(item.id, item.cliente_nome)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]">🗑️ Excluir</button>
          </div>
        </div>
      )}
      emptyMessage="Nenhum agendamento cadastrado"
    />
  );
}
