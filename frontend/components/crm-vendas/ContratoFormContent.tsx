'use client';

import type { LojaInfo, LeadInfo } from './modals/ModalPropostaForm';
import { CrmClienteBlock, CrmLojaBlock } from '@/components/crm-vendas/CrmLojaClienteBlocks';
import CrmDocumentoAssinaturasFields from '@/components/crm-vendas/documentos/CrmDocumentoAssinaturasFields';
import CrmDocumentoValoresFields from '@/components/crm-vendas/documentos/CrmDocumentoValoresFields';
import type { FormDataContrato } from './modals/ModalContratoForm';

export interface OportunidadeContratoOption {
  id: number;
  titulo: string;
  lead_nome: string;
  lead?: number;
  valor?: string;
}

export interface ContratoFormContentProps {
  form: FormDataContrato;
  formErro?: string | null;
  enviando: boolean;
  lojaInfo: LojaInfo | null;
  leadInfo: LeadInfo | null;
  oportunidades: OportunidadeContratoOption[];
  statusOpcoes: Array<{ value: string; label: string }>;
  onFormChange: (updater: (f: FormDataContrato) => FormDataContrato) => void;
  onOportunidadeChange: (id: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isEdit?: boolean;
  pageLayout?: boolean;
  hideError?: boolean;
  hideActions?: boolean;
  showCancel?: boolean;
  onCancel?: () => void;
  vendedorNome?: string;
}

const inputClass =
  'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white';
const labelClass = 'block text-xs text-gray-500 dark:text-gray-400 mb-0.5';
const sectionClass = 'space-y-3 border-b border-gray-200 dark:border-gray-600 pb-4';
const pageInputClass =
  'w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#1e3a5f] text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0176d3] focus:ring-offset-0';
const pageLabelClass = 'block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1';
const sectionTitleClass =
  'text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-[#0d1f3c] pb-2';

export default function ContratoFormContent({
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
  isEdit = false,
  pageLayout = false,
  hideError = false,
  hideActions = false,
  showCancel = true,
  onCancel,
  vendedorNome,
}: ContratoFormContentProps) {
  const inputCls = pageLayout ? pageInputClass : inputClass;
  const labelCls = pageLayout ? pageLabelClass : labelClass;

  const renderLojaBlock = () => (
    <CrmLojaBlock lojaInfo={lojaInfo} labelClass={labelCls} titleClass={sectionTitleClass} />
  );

  const renderClienteBlock = () => (
    <CrmClienteBlock
      leadInfo={leadInfo}
      oportunidadeSelecionada={!!form.oportunidade_id}
      labelClass={labelCls}
      titleClass={sectionTitleClass}
    />
  );

  const renderOportunidadeSelect = () => (
    <>
      <label className={labelCls}>Oportunidade (fechada ganha) *</label>
      <select
        value={form.oportunidade_id}
        onChange={(e) => onOportunidadeChange(e.target.value)}
        className={inputCls}
        required
        disabled={isEdit || enviando}
      >
        <option value="">Selecione</option>
        {oportunidades.map((o) => (
          <option key={o.id} value={o.id}>
            {o.titulo} — {o.lead_nome}
          </option>
        ))}
      </select>
      {oportunidades.length === 0 && (
        <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
          Nenhuma oportunidade fechada como ganha. Feche uma oportunidade no pipeline primeiro.
        </p>
      )}
    </>
  );

  const renderValoresBlock = () => (
    <CrmDocumentoValoresFields
      layout="grid"
      valorTotal={form.valor_total}
      descontoTipo={form.desconto_tipo}
      descontoValor={form.desconto_valor || ''}
      onValorTotalChange={(value) => onFormChange((f) => ({ ...f, valor_total: value }))}
      onDescontoTipoChange={(tipo) => onFormChange((f) => ({ ...f, desconto_tipo: tipo }))}
      onDescontoValorChange={(value) => onFormChange((f) => ({ ...f, desconto_valor: value }))}
      inputCls={inputCls}
      labelCls={labelCls}
    />
  );

  const renderConteudoBlock = () => (
    <div>
      <label className={labelCls}>Conteúdo</label>
      <textarea
        value={form.conteudo}
        onChange={(e) => onFormChange((f) => ({ ...f, conteudo: e.target.value }))}
        className={`${inputCls} min-h-[200px] lg:min-h-[240px] resize-y`}
        rows={10}
        placeholder="Descrição detalhada do contrato..."
      />
    </div>
  );

  const renderAssinaturasBlock = () => (
    <CrmDocumentoAssinaturasFields
      nomeVendedor={form.nome_vendedor_assinatura || ''}
      nomeCliente={form.nome_cliente_assinatura || ''}
      onNomeVendedorChange={(value) => onFormChange((f) => ({ ...f, nome_vendedor_assinatura: value }))}
      onNomeClienteChange={(value) => onFormChange((f) => ({ ...f, nome_cliente_assinatura: value }))}
      inputCls={inputCls}
      labelCls={labelCls}
      vendedorPlaceholder={vendedorNome}
      clientePlaceholder={leadInfo?.nome}
    />
  );

  if (pageLayout) {
    return (
      <form onSubmit={onSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 xl:gap-14 w-full">
          <div className="space-y-6">
            <section className="space-y-4">{renderLojaBlock()}</section>
            <section className="space-y-4">{renderClienteBlock()}</section>
            <section className="space-y-4">
              <h3 className={sectionTitleClass}>Oportunidade</h3>
              {renderOportunidadeSelect()}
            </section>
            <section className="space-y-4">
              <h3 className={sectionTitleClass}>Contrato</h3>
              <div>
                <label className={labelCls}>Número</label>
                <input
                  type="text"
                  value={form.numero}
                  onChange={(e) => onFormChange((f) => ({ ...f, numero: e.target.value }))}
                  className={inputCls}
                  placeholder="Ex: 001/2025"
                />
              </div>
              <div>
                <label className={labelCls}>Título *</label>
                <input
                  type="text"
                  value={form.titulo}
                  onChange={(e) => onFormChange((f) => ({ ...f, titulo: e.target.value }))}
                  className={inputCls}
                  placeholder="Título do contrato"
                  required
                />
              </div>
              <div>
                <label className={labelCls}>Status</label>
                <select
                  value={form.status}
                  onChange={(e) => onFormChange((f) => ({ ...f, status: e.target.value }))}
                  className={inputCls}
                >
                  {statusOpcoes.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
            </section>
          </div>

          <div className="space-y-6">
            <section className="space-y-4">
              <h3 className={sectionTitleClass}>Valores</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">{renderValoresBlock()}</div>
            </section>
            <section className="space-y-4">
              <h3 className={sectionTitleClass}>Conteúdo</h3>
              {renderConteudoBlock()}
            </section>
            <section className="space-y-4">
              <h3 className={sectionTitleClass}>Assinaturas</h3>
              {renderAssinaturasBlock()}
            </section>
          </div>
        </div>
      </form>
    );
  }

  const spanClass = 'md:col-span-2';
  return (
    <form onSubmit={onSubmit} className="space-y-4 md:max-w-3xl md:mx-auto md:grid md:grid-cols-2 md:gap-x-6">
      {formErro && !hideError && (
        <p className={`text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg ${spanClass}`}>
          {formErro}
        </p>
      )}

      <div className={`${sectionClass} ${spanClass}`}>
        <CrmLojaBlock lojaInfo={lojaInfo} compact titleClass="text-sm font-medium text-gray-700 dark:text-gray-300" />
      </div>

      <div className={`${sectionClass} ${spanClass}`}>
        <CrmClienteBlock
          leadInfo={leadInfo}
          oportunidadeSelecionada={!!form.oportunidade_id}
          compact
          titleClass="text-sm font-medium text-gray-700 dark:text-gray-300"
        />
      </div>

      <div className={spanClass}>{renderOportunidadeSelect()}</div>

      <div>
        <label className={labelCls}>Número</label>
        <input
          type="text"
          value={form.numero}
          onChange={(e) => onFormChange((f) => ({ ...f, numero: e.target.value }))}
          className={inputCls}
          placeholder="Ex: 001/2025"
        />
      </div>

      <div>
        <label className={labelCls}>Título *</label>
        <input
          type="text"
          value={form.titulo}
          onChange={(e) => onFormChange((f) => ({ ...f, titulo: e.target.value }))}
          className={inputCls}
          placeholder="Título do contrato"
          required
        />
      </div>

      <CrmDocumentoValoresFields
        layout="compact"
        valorTotal={form.valor_total}
        descontoTipo={form.desconto_tipo}
        descontoValor={form.desconto_valor || ''}
        onValorTotalChange={(value) => onFormChange((f) => ({ ...f, valor_total: value }))}
        onDescontoTipoChange={(tipo) => onFormChange((f) => ({ ...f, desconto_tipo: tipo }))}
        onDescontoValorChange={(value) => onFormChange((f) => ({ ...f, desconto_valor: value }))}
        inputCls={inputCls}
        labelCls={labelCls}
        sectionClassName={spanClass}
      />

      <div className={spanClass}>
        <label className={labelCls}>Conteúdo</label>
        <textarea
          value={form.conteudo}
          onChange={(e) => onFormChange((f) => ({ ...f, conteudo: e.target.value }))}
          className={`${inputCls} min-h-[100px]`}
          rows={4}
          placeholder="Descrição detalhada do contrato..."
        />
      </div>

      <div>
        <label className={labelCls}>Status</label>
        <select
          value={form.status}
          onChange={(e) => onFormChange((f) => ({ ...f, status: e.target.value }))}
          className={inputCls}
        >
          {statusOpcoes.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      <div className={`${spanClass} border-t border-gray-200 dark:border-gray-600 pt-4 mt-2`}>
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Assinaturas</p>
        {renderAssinaturasBlock()}
      </div>

      {!hideActions && (
        <div className={`flex gap-2 pt-2 ${spanClass}`}>
          {showCancel && onCancel && (
            <button
              type="button"
              onClick={() => !enviando && onCancel()}
              className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Cancelar
            </button>
          )}
          <button
            type="submit"
            disabled={enviando}
            className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium"
          >
            {enviando ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      )}
    </form>
  );
}
