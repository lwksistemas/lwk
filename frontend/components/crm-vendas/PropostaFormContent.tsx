'use client';

import type { LojaInfo, LeadInfo, OportunidadeItem, FormDataProposta } from './modals/ModalPropostaForm';
import BuscarOportunidadeInput from '@/components/crm-vendas/BuscarOportunidadeInput';
import { CrmClienteBlock, CrmLojaBlock } from '@/components/crm-vendas/CrmLojaClienteBlocks';
import CrmDocumentoAssinaturasFields from '@/components/crm-vendas/documentos/CrmDocumentoAssinaturasFields';
import CrmDocumentoConteudoFields from '@/components/crm-vendas/documentos/CrmDocumentoConteudoFields';
import CrmDocumentoFormActions from '@/components/crm-vendas/documentos/CrmDocumentoFormActions';
import CrmDocumentoValoresFields from '@/components/crm-vendas/documentos/CrmDocumentoValoresFields';
import CrmOportunidadeItensTabela from '@/components/crm-vendas/documentos/CrmOportunidadeItensTabela';
import {
  crmFormInputClass,
  crmFormLabelClass,
  crmFormPageInputClass,
  crmFormPageLabelClass,
  crmFormSectionClass,
  crmFormSectionTitleClass,
} from '@/lib/crm-form-styles';

export interface PropostaFormContentProps {
  form: FormDataProposta;
  formErro: string | null;
  enviando: boolean;
  lojaInfo: LojaInfo | null;
  leadInfo: LeadInfo | null;
  itensOportunidade: OportunidadeItem[];
  statusOpcoes: Array<{ value: string; label: string }>;
  onFormChange: (updater: (f: FormDataProposta) => FormDataProposta) => void;
  onOportunidadeChange: (id: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isEdit?: boolean;
  oportunidadeTituloInicial?: string;
  onSalvarComoPadrao?: (conteudo: string) => void;
  salvandoPadrao?: boolean;
  /** Se true, mostra botão Cancelar que chama onCancel */
  showCancel?: boolean;
  onCancel?: () => void;
  /** Se true, formulário ocupa largura total (para página fullscreen) */
  fullWidth?: boolean;
  /** Layout full-page CRM (CrmFormPageShell): estilos e sem rodapé interno */
  pageLayout?: boolean;
  /** Oculta mensagem de erro interna (ex.: erro no shell) */
  hideError?: boolean;
  /** Oculta botões Cancelar/Salvar (rodapé no CrmFormPageShell) */
  hideActions?: boolean;
  /** Templates disponíveis para seleção */
  templates?: Array<{ id: number; nome: string; conteudo: string; is_padrao: boolean }>;
  /** Callback quando seleciona um template */
  onSelecionarTemplate?: (conteudo: string, nomeTemplate?: string) => void;
  /** Nome do vendedor logado para preencher automaticamente */
  vendedorNome?: string;
}

const inputClass = crmFormInputClass;
const labelClass = crmFormLabelClass;
const sectionClass = crmFormSectionClass;

export default function PropostaFormContent({
  form,
  formErro,
  enviando,
  lojaInfo,
  leadInfo,
  itensOportunidade,
  statusOpcoes,
  onFormChange,
  onOportunidadeChange,
  onSubmit,
  isEdit = false,
  oportunidadeTituloInicial = '',
  onSalvarComoPadrao,
  salvandoPadrao = false,
  showCancel = true,
  onCancel,
  fullWidth = false,
  pageLayout = false,
  hideError = false,
  hideActions = false,
  templates = [],
  onSelecionarTemplate,
  vendedorNome,
}: PropostaFormContentProps) {
  const usePageStyles = pageLayout || fullWidth;
  const inputCls = usePageStyles ? crmFormPageInputClass : inputClass;
  const labelCls = usePageStyles ? crmFormPageLabelClass : labelClass;
  const sectionTitleCls = usePageStyles
    ? crmFormSectionTitleClass
    : 'text-sm font-medium text-gray-700 dark:text-gray-300';
  const sectionWrapCls = usePageStyles ? 'space-y-4' : sectionClass;
  const formClass = pageLayout
    ? 'grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 xl:gap-14 w-full'
    : fullWidth
      ? 'space-y-4 w-full md:grid md:grid-cols-2 md:gap-x-6 lg:gap-x-8'
      : 'space-y-4 md:max-w-3xl md:mx-auto md:grid md:grid-cols-2 md:gap-x-6';
  const spanClass = pageLayout ? 'lg:col-span-2' : 'md:col-span-2';

  const renderLojaBlock = () => (
    <CrmLojaBlock
      lojaInfo={lojaInfo}
      labelClass={labelCls}
      titleClass={pageLayout ? crmFormSectionTitleClass : sectionTitleCls}
      compact={!pageLayout}
    />
  );

  const renderClienteBlock = () => (
    <CrmClienteBlock
      leadInfo={leadInfo}
      oportunidadeSelecionada={!!form.oportunidade_id}
      labelClass={labelCls}
      titleClass={pageLayout ? crmFormSectionTitleClass : sectionTitleCls}
      compact={!pageLayout}
    />
  );

  const renderProdutosBlock = () => {
    if (!form.oportunidade_id) return null;
    return <CrmOportunidadeItensTabela itens={itensOportunidade} />;
  };

  const renderValoresBlock = () => {
    if (!form.oportunidade_id) return null;
    return (
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
  };

  const renderConteudoBlock = (opts?: { minHeightClass?: string; rows?: number }) => (
    <CrmDocumentoConteudoFields
      conteudo={form.conteudo}
      onConteudoChange={(value) => onFormChange((f) => ({ ...f, conteudo: value }))}
      inputCls={inputCls}
      labelCls={labelCls}
      placeholder="Descrição detalhada da proposta..."
      templates={templates}
      onSelecionarTemplate={onSelecionarTemplate}
      onSalvarComoPadrao={onSalvarComoPadrao}
      salvandoPadrao={salvandoPadrao}
      minHeightClass={opts?.minHeightClass}
      rows={opts?.rows}
      wrapTemplateAndContent
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
            <section className="space-y-4">{renderClienteBlock()}</section>
            <section className="space-y-4">
              <h3 className={crmFormSectionTitleClass}>Oportunidade</h3>
              <div>
                <label className={labelCls}>Buscar oportunidade *</label>
                <BuscarOportunidadeInput
                  oportunidadeId={form.oportunidade_id}
                  initialTitulo={oportunidadeTituloInicial}
                  onOportunidadeChange={onOportunidadeChange}
                  required
                  disabled={isEdit || enviando}
                />
              </div>
            </section>
            <section className="space-y-4">
              <h3 className={crmFormSectionTitleClass}>Proposta</h3>
              <div>
                <label className={labelCls}>Título *</label>
                <input
                  type="text"
                  value={form.titulo}
                  onChange={(e) => onFormChange((f) => ({ ...f, titulo: e.target.value }))}
                  className={inputCls}
                  placeholder="Título da proposta"
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
              <h3 className={crmFormSectionTitleClass}>Produtos e serviços</h3>
              {renderProdutosBlock() || (
                <p className="text-xs text-gray-500">Selecione uma oportunidade para ver os itens.</p>
              )}
            </section>
            {form.oportunidade_id && (
              <section className="space-y-4">
                <h3 className={crmFormSectionTitleClass}>Valores</h3>
                {renderValoresBlock()}
              </section>
            )}
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

  return (
    <form onSubmit={onSubmit} className={formClass}>
      {formErro && !hideError && (
        <p className={`text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg ${spanClass}`}>
          {formErro}
        </p>
      )}

      {/* Dados da Loja */}
      <div className={`${sectionWrapCls} ${spanClass}`}>
        <CrmLojaBlock lojaInfo={lojaInfo} labelClass={labelCls} titleClass={sectionTitleCls} compact />
      </div>

      {/* Dados do Cliente */}
      <div className={`${sectionWrapCls} ${spanClass}`}>
        <CrmClienteBlock
          leadInfo={leadInfo}
          oportunidadeSelecionada={!!form.oportunidade_id}
          labelClass={labelCls}
          titleClass={sectionTitleCls}
          compact
        />
      </div>

      {/* Oportunidade */}
      <div className={spanClass}>
        <label className={labelCls}>Oportunidade *</label>
        <BuscarOportunidadeInput
          oportunidadeId={form.oportunidade_id}
          initialTitulo={oportunidadeTituloInicial}
          onOportunidadeChange={onOportunidadeChange}
          required
          disabled={isEdit || enviando}
        />
      </div>

      {/* Produtos e Serviços */}
      {form.oportunidade_id && (
        <div className={spanClass}>
          <label className={labelCls}>Produtos e Serviços da Oportunidade</label>
          <CrmOportunidadeItensTabela itens={itensOportunidade} />
        </div>
      )}

      {/* Valor total e desconto */}
      {form.oportunidade_id && (
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
          valorInputClassName="max-w-[200px]"
          sectionClassName={spanClass}
        />
      )}

      {/* Título */}
      <div>
        <label className={labelCls}>Título *</label>
        <input
          type="text"
          value={form.titulo}
          onChange={(e) => onFormChange((f) => ({ ...f, titulo: e.target.value }))}
          className={inputCls}
          placeholder="Título da proposta"
          required
        />
      </div>

      {/* Conteúdo */}
      <CrmDocumentoConteudoFields
        conteudo={form.conteudo}
        onConteudoChange={(value) => onFormChange((f) => ({ ...f, conteudo: value }))}
        inputCls={inputCls}
        labelCls={labelCls}
        placeholder="Descrição detalhada da proposta..."
        templates={templates}
        onSelecionarTemplate={onSelecionarTemplate}
        onSalvarComoPadrao={onSalvarComoPadrao}
        salvandoPadrao={salvandoPadrao}
        minHeightClass={usePageStyles ? 'min-h-[200px] lg:min-h-[280px]' : 'min-h-[120px] md:min-h-[180px]'}
        rows={usePageStyles ? 12 : 6}
        showTemplateHint
        sectionClassName={spanClass}
      />

      {/* Status */}
      <div>
        <label className={labelCls}>Status</label>
        <select
          value={form.status}
          onChange={(e) => onFormChange((f) => ({ ...f, status: e.target.value }))}
          className={inputCls}
        >
          {statusOpcoes.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Assinaturas */}
      <div className={`${spanClass} border-t border-gray-100 dark:border-[#0d1f3c] pt-4 mt-2`}>
        <p className={`${sectionTitleCls} mb-3`}>Assinaturas</p>
        {renderAssinaturasBlock()}
      </div>

      {/* Botões (modal / formulário embutido) */}
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
