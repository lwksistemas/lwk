'use client';

import { Eye, Pencil, RefreshCw, Trash2 } from 'lucide-react';

export interface Lead {
  id: number;
  nome: string;
  empresa: string;
  cpf_cnpj?: string;
  email: string;
  telefone?: string;
  origem: string;
  status: string;
  valor_estimado?: string;
  cep?: string;
  logradouro?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  uf?: string;
  created_at: string;
}

const ORIGEM_LABELS: Record<string, string> = {
  whatsapp: 'WhatsApp',
  facebook: 'Facebook',
  instagram: 'Instagram',
  site: 'Site',
  indicacao: 'Indicação',
  outro: 'Outro',
};

const STATUS_STYLES: Record<string, string> = {
  novo: 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-300',
  contato: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300',
  qualificado: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300',
  perdido: 'bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400',
};

const ORIGEM_STYLES: Record<string, string> = {
  whatsapp: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300',
  facebook: 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300',
  instagram: 'bg-pink-100 text-pink-700 dark:bg-pink-500/20 dark:text-pink-300',
  site: 'bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300',
  indicacao: 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300',
  outro: 'bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400',
};

interface LeadsTableProps {
  leads: Lead[];
  loading?: boolean;
  colunas?: Array<{ key: string; label: string }>;
  onVerLead?: (lead: Lead) => void;
  onEditarLead?: (lead: Lead) => void;
  onExcluirLead?: (lead: Lead) => void;
  onMudarStatus?: (lead: Lead) => void;
}

export default function LeadsTable({
  leads,
  loading = false,
  colunas,
  onVerLead,
  onEditarLead,
  onExcluirLead,
  onMudarStatus,
}: LeadsTableProps) {
  const getOrigemLabel = (origem: string) =>
    ORIGEM_LABELS[origem] || origem.charAt(0).toUpperCase() + origem.slice(1).replace('_', ' ');
  const getStatusLabel = (status: string) =>
    status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  const origemClass = (origem: string) => ORIGEM_STYLES[origem] || ORIGEM_STYLES.outro;
  const statusClass = (status: string) => STATUS_STYLES[status] || STATUS_STYLES.novo;

  // Colunas padrão se não fornecidas
  const colunasVisiveis = colunas || [
    { key: 'nome', label: 'Lead' },
    { key: 'empresa', label: 'Empresa' },
    { key: 'email', label: 'Email' },
    { key: 'origem', label: 'Origem' },
    { key: 'status', label: 'Status' },
  ];

  const formatarData = (s: string) => {
    if (!s) return '–';
    try {
      const d = new Date(s);
      return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    } catch {
      return s;
    }
  };

  const renderCelula = (lead: Lead, coluna: string) => {
    switch (coluna) {
      case 'nome':
        return (
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 shrink-0 rounded-full bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center text-blue-600 dark:text-blue-300 font-semibold">
              {lead.nome.charAt(0).toUpperCase()}
            </div>
            <span className="font-medium text-gray-800 dark:text-white">
              {lead.nome}
            </span>
          </div>
        );
      case 'empresa':
        return <span className="text-gray-600 dark:text-gray-400">{lead.empresa || '–'}</span>;
      case 'email':
        return <span className="text-gray-600 dark:text-gray-400">{lead.email || '–'}</span>;
      case 'telefone':
        return <span className="text-gray-600 dark:text-gray-400">{lead.telefone || '–'}</span>;
      case 'origem':
        return (
          <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${origemClass(lead.origem)}`}>
            {getOrigemLabel(lead.origem)}
          </span>
        );
      case 'status':
        return (
          <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${statusClass(lead.status)}`}>
            {getStatusLabel(lead.status)}
          </span>
        );
      case 'valor_estimado':
        return (
          <span className="text-gray-800 dark:text-white font-medium">
            {lead.valor_estimado 
              ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(lead.valor_estimado))
              : '–'}
          </span>
        );
      case 'created_at':
        return <span className="text-gray-600 dark:text-gray-400">{formatarData(lead.created_at)}</span>;
      default:
        return <span className="text-gray-600 dark:text-gray-400">–</span>;
    }
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow border border-gray-200 dark:border-slate-700 overflow-hidden">
        <div className="py-16 flex flex-col items-center justify-center gap-3">
          <div className="h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-500 dark:text-gray-400">Carregando leads...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow border border-gray-200 dark:border-slate-700 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[680px]">
          <thead className="bg-gray-50 dark:bg-slate-700/50 border-b border-gray-200 dark:border-slate-600">
            <tr>
              {colunasVisiveis.map((coluna) => (
                <th
                  key={coluna.key}
                  className="p-4 text-left text-gray-500 dark:text-gray-400 text-sm font-medium"
                >
                  {coluna.label}
                </th>
              ))}
              <th className="p-4 text-right text-gray-500 dark:text-gray-400 text-sm font-medium">
                Ações
              </th>
            </tr>
          </thead>
          <tbody>
            {leads.length === 0 ? (
              <tr>
                <td
                  colSpan={colunasVisiveis.length + 1}
                  className="py-16 text-center text-gray-500 dark:text-gray-400 text-sm"
                >
                  Nenhum lead cadastrado. Clique em &quot;Novo Lead&quot; para começar.
                </td>
              </tr>
            ) : (
              leads.map((lead) => (
                <tr
                  key={lead.id}
                  className="border-b border-gray-100 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-700/30 transition-colors"
                >
                  {colunasVisiveis.map((coluna) => (
                    <td key={coluna.key} className="p-4">
                      {renderCelula(lead, coluna.key)}
                    </td>
                  ))}
                  <td className="p-4">
                    <div className="flex justify-end gap-4 text-sm">
                      <button
                        type="button"
                        onClick={() => onVerLead?.(lead)}
                        className="inline-flex items-center gap-1.5 text-blue-600 dark:text-blue-400 hover:underline font-medium"
                      >
                        <Eye size={16} />
                        Ver
                      </button>
                      <button
                        type="button"
                        onClick={() => onEditarLead?.(lead)}
                        className="inline-flex items-center gap-1.5 text-orange-600 dark:text-orange-400 hover:underline font-medium"
                        title="Editar lead"
                      >
                        <Pencil size={16} />
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => onMudarStatus?.(lead)}
                        className="inline-flex items-center gap-1.5 text-green-600 dark:text-green-400 hover:underline font-medium"
                        title="Mudar status"
                      >
                        <RefreshCw size={16} />
                        Status
                      </button>
                      <button
                        type="button"
                        onClick={() => onExcluirLead?.(lead)}
                        className="inline-flex items-center gap-1.5 text-red-600 dark:text-red-400 hover:underline font-medium"
                        title="Excluir lead"
                      >
                        <Trash2 size={16} />
                        Excluir
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
