'use client';

import { X } from 'lucide-react';
import PropostaFormContent from '../PropostaFormContent';

export interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria?: string;
  endereco?: string | null;
  cpf_cnpj?: string | null;
  admin_nome?: string | null;
  admin_email?: string | null;
}

export interface LeadInfo {
  id: number;
  nome: string;
  empresa?: string;
  cpf_cnpj?: string;
  email?: string;
  telefone?: string;
  cep?: string;
  logradouro?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  uf?: string;
}

export interface OportunidadeItem {
  id: number;
  produto_servico: number;
  produto_servico_nome: string;
  produto_servico_tipo: string;
  quantidade: string;
  preco_unitario: string;
  subtotal: number;
  observacao?: string;
}

export interface FormDataProposta {
  oportunidade_id: string;
  titulo: string;
  conteudo: string;
  valor_total: string;
  status: string;
  nome_vendedor_assinatura?: string;
  nome_cliente_assinatura?: string;
}

interface ModalPropostaFormProps {
  title: string;
  form: FormDataProposta;
  formErro: string | null;
  enviando: boolean;
  lojaInfo: LojaInfo | null;
  leadInfo: LeadInfo | null;
  oportunidades: Array<{ id: number; titulo: string; lead_nome: string }>;
  itensOportunidade: OportunidadeItem[];
  statusOpcoes: Array<{ value: string; label: string }>;
  onFormChange: (updater: (f: FormDataProposta) => FormDataProposta) => void;
  onOportunidadeChange: (id: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  onClose: () => void;
  isEdit?: boolean;
  /** Callback para salvar o conteúdo atual como Proposta PADRAO */
  onSalvarComoPadrao?: (conteudo: string) => void;
  salvandoPadrao?: boolean;
  /** Templates disponíveis */
  templates?: Array<{ id: number; nome: string; conteudo: string; is_padrao: boolean }>;
  /** Callback quando seleciona template */
  onSelecionarTemplate?: (conteudo: string) => void;
  /** Nome do vendedor logado */
  vendedorNome?: string;
}

export default function ModalPropostaForm({
  title,
  form,
  formErro,
  enviando,
  lojaInfo,
  leadInfo,
  oportunidades,
  itensOportunidade,
  statusOpcoes,
  onFormChange,
  onOportunidadeChange,
  onSubmit,
  onClose,
  isEdit = false,
  onSalvarComoPadrao,
  salvandoPadrao = false,
  templates = [],
  onSelecionarTemplate,
  vendedorNome,
}: ModalPropostaFormProps) {
  return (
    <div
      className="fixed inset-0 z-[80] bg-black/50 flex items-center justify-center md:p-0"
      onClick={() => !enviando && onClose()}
    >
      <div
        className="bg-white dark:bg-gray-800 shadow-xl border border-gray-200 dark:border-gray-700 w-full overflow-y-auto max-w-md max-h-[90vh] rounded-2xl md:w-[calc(100vw-2rem)] md:max-w-4xl md:h-[calc(100vh-2rem)] md:max-h-none md:rounded-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 z-10">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h2>
          <button
            type="button"
            onClick={() => !enviando && onClose()}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>
        <div className="p-4">
          <PropostaFormContent
            form={form}
            formErro={formErro}
            enviando={enviando}
            lojaInfo={lojaInfo}
            leadInfo={leadInfo}
            oportunidades={oportunidades}
            itensOportunidade={itensOportunidade}
            statusOpcoes={statusOpcoes}
            onFormChange={onFormChange}
            onOportunidadeChange={onOportunidadeChange}
            onSubmit={onSubmit}
            isEdit={isEdit}
            onSalvarComoPadrao={onSalvarComoPadrao}
            salvandoPadrao={salvandoPadrao}
            showCancel={true}
            onCancel={onClose}
            templates={templates}
            onSelecionarTemplate={onSelecionarTemplate}
            vendedorNome={vendedorNome}
          />
        </div>
      </div>
    </div>
  );
}
