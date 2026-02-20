'use client';

import { useState, useEffect } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { formatCurrency } from '@/lib/financeiro-helpers';
import { ModalBase } from './ModalBase';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

const STATUS_ORCAMENTO = [
  { value: 'pendente', label: 'Pendente' },
  { value: 'aprovado', label: 'Aprovado' },
  { value: 'recusado', label: 'Recusado' },
  { value: 'expirado', label: 'Expirado' }
];

export function ModalOrcamentos({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [clientes, setClientes] = useState<any[]>([]);
  const [servicos, setServicos] = useState<any[]>([]);

  useEffect(() => {
    const loadDados = async () => {
      try {
        const [cliRes, servRes] = await Promise.all([
          clinicaApiClient.get('/servicos/clientes/'),
          clinicaApiClient.get('/servicos/servicos/')
        ]);
        setClientes(Array.isArray(cliRes.data) ? cliRes.data : cliRes.data?.results ?? []);
        setServicos(Array.isArray(servRes.data) ? servRes.data : servRes.data?.results ?? []);
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
      title="Orçamentos"
      icon="💰"
      endpoint="/servicos/orcamentos/"
      formFields={[
        { name: 'numero_orcamento', label: 'Número do Orçamento', type: 'text', required: true, placeholder: 'Ex: ORC-001' },
        { name: 'cliente_id', apiName: 'cliente', label: 'Cliente', type: 'select', required: true, options: clientes.map(c => ({ value: c.id, label: c.nome })), fullWidth: true, transform: (v: string) => parseInt(v), getValue: (item: any) => String(item.cliente) },
        { name: 'servico_id', apiName: 'servico', label: 'Serviço', type: 'select', required: true, options: servicos.map(s => ({ value: s.id, label: s.nome })), fullWidth: true, transform: (v: string) => parseInt(v), getValue: (item: any) => String(item.servico) },
        { name: 'descricao', label: 'Descrição', type: 'textarea', required: true, fullWidth: true, rows: 3 },
        { name: 'valor', label: 'Valor (R$)', type: 'number', required: true, min: 0, step: 0.01, transform: (v: string) => parseFloat(v) },
        { name: 'validade', label: 'Validade', type: 'date', required: true },
        { name: 'status', label: 'Status', type: 'select', required: true, options: STATUS_ORCAMENTO, defaultValue: 'pendente' },
        { name: 'observacoes', label: 'Observações', type: 'textarea', fullWidth: true, transform: (v: string) => v || null }
      ]}
      renderListItem={(item: any, handleEditar: any, handleExcluir: any, loja: any) => (
        <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-bold text-lg" style={{ color: loja.cor_primaria }}>Orçamento #{item.numero_orcamento}</span>
              <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
                item.status === 'aprovado' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' :
                item.status === 'recusado' ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300' :
                item.status === 'expirado' ? 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300' :
                'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300'
              }`}>
                {STATUS_ORCAMENTO.find(s => s.value === item.status)?.label}
              </span>
            </div>
            <p className="font-semibold text-gray-900 dark:text-white">{item.cliente_nome}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">{item.servico_nome}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{item.descricao}</p>
            <div className="flex gap-3 mt-2">
              <span className="text-sm font-bold" style={{ color: loja.cor_primaria }}>
                {formatCurrency(item.valor)}
              </span>
              <span className="text-xs text-gray-500">Validade: {item.validade}</span>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleEditar(item)} className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
            <button onClick={() => handleExcluir(item.id, `Orçamento #${item.numero_orcamento}`)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]">🗑️ Excluir</button>
          </div>
        </div>
      )}
      emptyMessage="Nenhum orçamento cadastrado"
    />
  );
}
