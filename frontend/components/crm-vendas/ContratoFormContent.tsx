'use client';

import type { LojaInfo, LeadInfo } from './modals/ModalPropostaForm';
import { CrmClienteBlock } from '@/components/crm-vendas/CrmLojaClienteBlocks';
import { CrmEmitenteLojaSection } from '@/components/crm-vendas/CrmEmitenteLojaSection';
import CrmDocumentoAssinaturasFields from '@/components/crm-vendas/documentos/CrmDocumentoAssinaturasFields';
import CrmDocumentoConteudoFields from '@/components/crm-vendas/documentos/CrmDocumentoConteudoFields';
import CrmDocumentoFormActions from '@/components/crm-vendas/documentos/CrmDocumentoFormActions';
import CrmDocumentoValoresFields from '@/components/crm-vendas/documentos/CrmDocumentoValoresFields';
import {
  crmFormInputClass,
  crmFormLabelClass,
  crmFormPageInputClass,
  crmFormPageLabelClass,
  crmFormSectionClass,
  crmFormSectionTitleClass,
} from '@/lib/crm-form-styles';
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

const inputClass = crmFormInputClass;
const labelClass = crmFormLabelClass;
const sectionClass = crmFormSectionClass;

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
  const inputCls = pageLayout ? crmFormPageInputClass : inputClass;
  const labelCls = pageLayout ? crmFormPageLabelClass : labelClass;

  const renderLojaBlock = () => (
    <CrmEmitenteLojaSection
      lojaInfo={lojaInfo}
      emitente={{
        emitente_personalizado: form.emitente_personalizado,
        emitente_nome: form.emitente_nome,
        emitente_endereco: form.emitente_endereco,
        emitente_cpf_cnpj: form.emitente_cpf_cnpj,
        emitente_responsavel: form.emitente_responsavel,
        emitente_email: form.emitente_email,
      }}
      onEmitenteChange={(patch) => onFormChange((f) => ({ ...f, ...patch }))}
      labelClass={labelCls}
      titleClass={crmFormSectionTitleClass}
      inputClass={inputCls}
    />
  );

  const renderClienteBlock = () => (
    <CrmClienteBlock
      leadInfo={leadInfo}
      oportunidadeSelecionada={!!form.oportunidade_id}
      labelClass={labelCls}
      titleClass={crmFormSectionTitleClass}
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

  const renderConteudoBlock = (opts?: { minHeightClass?: string; rows?: number }) => (
    <CrmDocumentoConteudoFields
      conteudo={form.conteudo}
      onConteudoChange={(value) => onFormChange((f) => ({ ...f, conteudo: value }))}
      inputCls={inputCls}
      labelCls={labelCls}
      placeholder="Descrição detalhada do contrato..."
      minHeightClass={opts?.minHeightClass ?? 'min-h-[200px] lg:min-h-[240px]'}
      rows={opts?.rows ?? 10}
    />
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
            <section className="space-y-4">
              <h3 className={crmFormSectionTitleClass}>Oportunidade</h3>
              {renderOportunidadeSelect()}
            </section>
            <section className="space-y-4">{renderClienteBlock()}</section>
            <section className="space-y-4">
              <h3 className={crmFormSectionTitleClass}>Contrato</h3>
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
              <h3 className={crmFormSectionTitleClass}>Valores</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">{renderValoresBlock()}</div>
            </section>
            <section className="space-y-4">
              <h3 className={crmFormSectionTitleClass}>Conteúdo</h3>
              {renderConteudoBlock()}
            </section>
            <section className="space-y-4">
              <h3 className={crmFormSectionTitleClass}>Assinaturas</h3>
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
        {renderLojaBlock()}
      </div>

      <div className={spanClass}>{renderOportunidadeSelect()}</div>

      <div className={`${sectionClass} ${spanClass}`}>
        <CrmClienteBlock
          leadInfo={leadInfo}
          oportunidadeSelecionada={!!form.oportunidade_id}
          compact
          titleClass="text-sm font-medium text-gray-700 dark:text-gray-300"
        />
      </div>

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

      <CrmDocumentoConteudoFields
        conteudo={form.conteudo}
        onConteudoChange={(value) => onFormChange((f) => ({ ...f, conteudo: value }))}
        inputCls={inputCls}
        labelCls={labelCls}
        placeholder="Descrição detalhada do contrato..."
        minHeightClass="min-h-[100px]"
        rows={4}
        sectionClassName={spanClass}
      />

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
        <CrmDocumentoFormActions
          enviando={enviando}
          showCancel={showCancel}
          onCancel={onCancel}
          className={spanClass}
        />
      )}
    </form>
  );
}
