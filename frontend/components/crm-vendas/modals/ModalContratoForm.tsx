'use client';

import { X } from 'lucide-react';
import ContratoFormContent from '../ContratoFormContent';
import type { LojaInfo, LeadInfo } from './ModalPropostaForm';

export interface FormDataContrato {
  oportunidade_id: string;
  numero: string;
  titulo: string;
  conteudo: string;
  valor_total: string;
  desconto_tipo: 'percentual' | 'valor';
  desconto_valor: string;
  status: string;
  nome_vendedor_assinatura?: string;
  nome_cliente_assinatura?: string;
}

export const EMPTY_FORM_CONTRATO: FormDataContrato = {
  oportunidade_id: '',
  numero: '',
  titulo: '',
  conteudo: '',
  valor_total: '',
  desconto_tipo: 'percentual',
  desconto_valor: '',
  status: 'rascunho',
  nome_vendedor_assinatura: '',
  nome_cliente_assinatura: '',
};

interface ModalContratoFormProps {
  title: string;
  form: FormDataContrato;
  formErro: string | null;
  enviando: boolean;
  lojaInfo: LojaInfo | null;
  leadInfo: LeadInfo | null;
  oportunidades: Array<{ id: number; titulo: string; lead_nome: string; lead?: number }>;
  statusOpcoes: Array<{ value: string; label: string }>;
  onFormChange: (updater: (f: FormDataContrato) => FormDataContrato) => void;
  onOportunidadeChange: (id: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  onClose: () => void;
  isEdit?: boolean;
  vendedorNome?: string;
}

export default function ModalContratoForm({
  title,
  form,
  formErro,
  enviando,
  lojaInfo,
  leadInfo,
  oportunidades,
  statusOpcoes,
  onFormChange,
  onOportunidadeChange,
  onSubmit,
  onClose,
  isEdit = false,
  vendedorNome,
}: ModalContratoFormProps) {
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
          <ContratoFormContent
            form={form}
            formErro={formErro}
            enviando={enviando}
            lojaInfo={lojaInfo}
            leadInfo={leadInfo}
            oportunidades={oportunidades}
            statusOpcoes={statusOpcoes}
            onFormChange={onFormChange}
            onOportunidadeChange={onOportunidadeChange}
            onSubmit={onSubmit}
            isEdit={isEdit}
            showCancel
            onCancel={onClose}
            vendedorNome={vendedorNome}
          />
        </div>
      </div>
    </div>
  );
}
