'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { LojaInfo } from '@/components/crm-vendas/modals/ModalPropostaForm';
import {
  type EmitenteLojaFields,
  lojaInfoParaEmitente,
  resumoEmitenteLoja,
} from '@/lib/crm-emitente-loja';

interface CrmEmitenteLojaSectionProps {
  lojaInfo: LojaInfo | null;
  emitente: EmitenteLojaFields;
  onEmitenteChange: (patch: Partial<EmitenteLojaFields>) => void;
  labelClass?: string;
  titleClass?: string;
  inputClass?: string;
  /** Seção recolhida ao abrir o formulário */
  defaultCollapsed?: boolean;
}

export function CrmEmitenteLojaSection({
  lojaInfo,
  emitente,
  onEmitenteChange,
  labelClass = 'block text-xs text-gray-500 dark:text-gray-400 mb-0.5',
  titleClass = 'text-sm font-medium text-gray-700 dark:text-gray-300',
  inputClass = 'w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#1e3a5f] text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0176d3]',
  defaultCollapsed = true,
}: CrmEmitenteLojaSectionProps) {
  const [aberta, setAberta] = useState(!defaultCollapsed);
  const personalizado = emitente.emitente_personalizado;
  const resumo = resumoEmitenteLoja(lojaInfo, emitente);

  const iniciarPersonalizacao = () => {
    const base = lojaInfoParaEmitente(lojaInfo);
    onEmitenteChange({
      emitente_personalizado: true,
      ...base,
    });
    setAberta(true);
  };

  const restaurarPadrao = () => {
    onEmitenteChange({
      emitente_personalizado: false,
      emitente_nome: '',
      emitente_endereco: '',
      emitente_cpf_cnpj: '',
      emitente_responsavel: '',
      emitente_email: '',
    });
  };

  const setCampo = (campo: keyof EmitenteLojaFields, valor: string) => {
    onEmitenteChange({ [campo]: valor } as Partial<EmitenteLojaFields>);
  };

  const renderReadonlyLoja = () => {
    if (!lojaInfo) {
      return <p className="text-xs text-gray-500">Carregando...</p>;
    }
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
        <div className="sm:col-span-2">
          <span className={labelClass}>Nome da loja</span>
          <p className="font-medium text-gray-900 dark:text-white">{lojaInfo.nome}</p>
        </div>
        {lojaInfo.endereco && (
          <div className="sm:col-span-2">
            <span className={labelClass}>Endereço da loja</span>
            <p className="text-gray-800 dark:text-gray-200">{lojaInfo.endereco}</p>
          </div>
        )}
        {lojaInfo.cpf_cnpj && (
          <div>
            <span className={labelClass}>CPF ou CNPJ da loja</span>
            <p className="text-gray-800 dark:text-gray-200">{lojaInfo.cpf_cnpj}</p>
          </div>
        )}
        {lojaInfo.admin_nome && (
          <div>
            <span className={labelClass}>Nome do administrador</span>
            <p className="text-gray-800 dark:text-gray-200">{lojaInfo.admin_nome}</p>
          </div>
        )}
        {lojaInfo.admin_email && (
          <div className="sm:col-span-2">
            <span className={labelClass}>Email do administrador</span>
            <p className="text-gray-800 dark:text-gray-200">{lojaInfo.admin_email}</p>
          </div>
        )}
      </div>
    );
  };

  const renderCamposEditaveis = () => (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
      <div className="sm:col-span-2">
        <label className={labelClass}>Nome / razão social *</label>
        <input
          type="text"
          value={emitente.emitente_nome}
          onChange={(e) => setCampo('emitente_nome', e.target.value)}
          className={inputClass}
          placeholder="Nome do emitente"
          required={personalizado}
        />
      </div>
      <div className="sm:col-span-2">
        <label className={labelClass}>Endereço</label>
        <input
          type="text"
          value={emitente.emitente_endereco}
          onChange={(e) => setCampo('emitente_endereco', e.target.value)}
          className={inputClass}
          placeholder="Endereço completo"
        />
      </div>
      <div>
        <label className={labelClass}>CPF ou CNPJ</label>
        <input
          type="text"
          value={emitente.emitente_cpf_cnpj}
          onChange={(e) => setCampo('emitente_cpf_cnpj', e.target.value)}
          className={inputClass}
          placeholder="00.000.000/0000-00"
        />
      </div>
      <div>
        <label className={labelClass}>Responsável</label>
        <input
          type="text"
          value={emitente.emitente_responsavel}
          onChange={(e) => setCampo('emitente_responsavel', e.target.value)}
          className={inputClass}
          placeholder="Nome do responsável"
        />
      </div>
      <div className="sm:col-span-2">
        <label className={labelClass}>E-mail</label>
        <input
          type="email"
          value={emitente.emitente_email}
          onChange={(e) => setCampo('emitente_email', e.target.value)}
          className={inputClass}
          placeholder="email@exemplo.com"
        />
      </div>
    </div>
  );

  return (
    <div className="rounded-lg border border-gray-200 dark:border-[#0d1f3c] bg-gray-50/50 dark:bg-[#0d1f3c]/30">
      <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2.5">
        <button
          type="button"
          onClick={() => setAberta((v) => !v)}
          className="flex flex-1 min-w-0 items-center gap-2 text-left group"
        >
          <span className={titleClass}>Dados da Loja</span>
          {!aberta && (
            <span className="text-xs text-gray-500 dark:text-gray-400 truncate">{resumo}</span>
          )}
          {aberta ? (
            <ChevronUp className="w-4 h-4 text-gray-400 shrink-0" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" />
          )}
        </button>
        {aberta && (
          <div className="flex flex-wrap gap-2 shrink-0">
            {!personalizado ? (
              <button
                type="button"
                onClick={iniciarPersonalizacao}
                className="text-xs font-medium text-[#0176d3] hover:underline"
              >
                Personalizar
              </button>
            ) : (
              <button
                type="button"
                onClick={restaurarPadrao}
                className="text-xs font-medium text-gray-600 dark:text-gray-300 hover:underline"
              >
                Restaurar padrão da loja
              </button>
            )}
          </div>
        )}
      </div>

      {aberta && (
        <div className="px-3 pb-3 pt-0 border-t border-gray-100 dark:border-[#0d1f3c]">
          {personalizado ? (
            <>
              <p className="text-xs text-amber-700 dark:text-amber-300/90 mb-3 mt-2">
                Emitente personalizado — estes dados serão usados no PDF deste documento.
              </p>
              {renderCamposEditaveis()}
            </>
          ) : (
            <>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-3 mt-2">
                Padrão: dados do administrador da loja. Use &quot;Personalizar&quot; apenas em exceções.
              </p>
              {renderReadonlyLoja()}
            </>
          )}
        </div>
      )}
    </div>
  );
}
