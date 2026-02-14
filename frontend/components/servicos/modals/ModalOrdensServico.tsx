'use client';

import { useState, useEffect } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { ModalBase } from './ModalBase';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

const STATUS_OS = [
  { value: 'aberta', label: 'Aberta' },
  { value: 'em_andamento', label: 'Em Andamento' },
  { value: 'aguardando_peca', label: 'Aguardando Peça' },
  { value: 'concluida', label: 'Concluída' },
  { value: 'cancelada', label: 'Cancelada' }
];

export function ModalOrdensServico({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
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
      title="Ordens de Serviço"
      icon="🔧"
      endpoint="/servicos/ordens-servico/"
      formFields={[
        { name: 'numero_os', label: 'Número da OS', type: 'text', required: true, placeholder: 'Ex: OS-001' },
        { name: 'cliente_id', apiName: 'cliente', label: 'Cliente', type: 'select', required: true, options: clientes.map(c => ({ value: c.id, label: c.nome })), transform: (v: string) => parseInt(v), getValue: (item: any) => String(item.cliente) },
        { name: 'servico_id', apiName: 'servico', label: 'Serviço', type: 'select', required: true, options: servicos.map(s => ({ value: s.id, label: s.nome })), transform: (v: string) => parseInt(v), getValue: (item: any) => String(item.servico) },
        { name: 'profissional_id', apiName: 'profissional', label: 'Profissional', type: 'select', options: profissionais.map(p => ({ value: p.id, label: p.nome })), transform: (v: string) => v ? parseInt(v) : null, getValue: (item: any) => item.profissional ? String(item.profissional) : '' },
        { name: 'status', label: 'Status', type: 'select', required: true, options: STATUS_OS, defaultValue: 'aberta' },
        { name: 'descricao_problema', label: 'Descrição do Problema', type: 'textarea', required: true, fullWidth: true, rows: 3 },
        { name: 'diagnostico', label: 'Diagnóstico', type: 'textarea', fullWidth: true, rows: 2, transform: (v: string) => v || null },
        { name: 'solucao', label: 'Solução', type: 'textarea', fullWidth: true, rows: 2, transform: (v: string) => v || null },
        { name: 'data_previsao', label: 'Data de Previsão', type: 'date', transform: (v: string) => v || null },
        { name: 'data_conclusao', label: 'Data de Conclusão', type: 'date', transform: (v: string) => v || null },
        { name: 'valor_servico', label: 'Valor do Serviço (R$)', type: 'number', required: true, min: 0, step: 0.01, transform: (v: string) => parseFloat(v) },
        { name: 'valor_pecas', label: 'Valor das Peças (R$)', type: 'number', min: 0, step: 0.01, defaultValue: '0', transform: (v: string) => parseFloat(v) },
        { name: 'valor_total', label: 'Valor Total (R$)', type: 'number', required: true, min: 0, step: 0.01, transform: (v: string) => parseFloat(v) },
        { name: 'observacoes', label: 'Observações', type: 'textarea', fullWidth: true, transform: (v: string) => v || null }
      ]}
      renderListItem={(item: any, handleEditar: any, handleExcluir: any, loja: any) => (
        <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-bold text-lg" style={{ color: loja.cor_primaria }}>OS #{item.numero_os}</span>
              <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-semibold rounded-full">
                {STATUS_OS.find(s => s.value === item.status)?.label}
              </span>
            </div>
            <p className="font-semibold text-gray-900 dark:text-white">{item.cliente_nome}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{item.servico_nome}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{item.profissional_nome || 'Sem profissional'}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{item.descricao_problema}</p>
            <div className="flex gap-2 mt-2">
              <span className="text-sm font-bold" style={{ color: loja.cor_primaria }}>
                Total: R$ {Number(item.valor_total).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </span>
              {item.data_previsao && <span className="text-xs text-gray-500">Previsão: {item.data_previsao}</span>}
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleEditar(item)} className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
            <button onClick={() => handleExcluir(item.id, `OS #${item.numero_os}`)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]">🗑️ Excluir</button>
          </div>
        </div>
      )}
      emptyMessage="Nenhuma ordem de serviço cadastrada"
    />
  );
}
