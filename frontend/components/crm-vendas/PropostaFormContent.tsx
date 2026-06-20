'use client';

import type { LojaInfo, LeadInfo, OportunidadeItem, FormDataProposta } from './modals/ModalPropostaForm';
import BuscarOportunidadeInput from '@/components/crm-vendas/BuscarOportunidadeInput';

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

const inputClass = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white';
const labelClass = 'block text-xs text-gray-500 dark:text-gray-400 mb-0.5';
const sectionClass = 'space-y-3 border-b border-gray-200 dark:border-gray-600 pb-4';

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
  const inputCls = usePageStyles
    ? 'w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#1e3a5f] text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0176d3] focus:ring-offset-0'
    : inputClass;
  const labelCls = usePageStyles
    ? 'block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1'
    : labelClass;
  const sectionTitleCls = usePageStyles
    ? 'text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-[#0d1f3c] pb-2'
    : 'text-sm font-medium text-gray-700 dark:text-gray-300';
  const sectionWrapCls = usePageStyles ? 'space-y-4' : sectionClass;
  const formClass = pageLayout
    ? 'grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 xl:gap-14 w-full'
    : fullWidth
      ? 'space-y-4 w-full md:grid md:grid-cols-2 md:gap-x-6 lg:gap-x-8'
      : 'space-y-4 md:max-w-3xl md:mx-auto md:grid md:grid-cols-2 md:gap-x-6';
  const spanClass = pageLayout ? 'lg:col-span-2' : 'md:col-span-2';
  const sectionTitleClass =
    'text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-[#0d1f3c] pb-2';

  const renderLojaBlock = () => (
    <>
      <h3 className={pageLayout ? sectionTitleClass : sectionTitleCls}>Dados da Loja</h3>
      {lojaInfo ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <div className="sm:col-span-2">
            <span className={labelCls}>Nome da loja</span>
            <p className="font-medium text-gray-900 dark:text-white">{lojaInfo.nome}</p>
          </div>
          {lojaInfo.endereco && (
            <div className="sm:col-span-2">
              <span className={labelCls}>Endereço da loja</span>
              <p className="text-gray-800 dark:text-gray-200">{lojaInfo.endereco}</p>
            </div>
          )}
          {lojaInfo.cpf_cnpj && (
            <div>
              <span className={labelCls}>CPF ou CNPJ da loja</span>
              <p className="text-gray-800 dark:text-gray-200">{lojaInfo.cpf_cnpj}</p>
            </div>
          )}
          {lojaInfo.admin_nome && (
            <div>
              <span className={labelCls}>Nome do administrador</span>
              <p className="text-gray-800 dark:text-gray-200">{lojaInfo.admin_nome}</p>
            </div>
          )}
          {lojaInfo.admin_email && (
            <div className="sm:col-span-2">
              <span className={labelCls}>Email do administrador</span>
              <p className="text-gray-800 dark:text-gray-200">{lojaInfo.admin_email}</p>
            </div>
          )}
        </div>
      ) : (
        <p className="text-xs text-gray-500">Carregando...</p>
      )}
    </>
  );

  const renderClienteBlock = () => (
    <>
      <h3 className={pageLayout ? sectionTitleClass : sectionTitleCls}>Dados do Cliente</h3>
      {leadInfo ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <div className="sm:col-span-2">
            <span className={labelCls}>Nome</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {leadInfo.conta_info?.nome ||
                (leadInfo.cpf_cnpj?.replace(/\D/g, '').length === 11
                  ? leadInfo.nome
                  : leadInfo.empresa || leadInfo.nome)}
            </p>
          </div>
          {leadInfo.conta_info?.razao_social && (
            <div className="sm:col-span-2">
              <span className={labelCls}>Razão Social</span>
              <p className="text-gray-800 dark:text-gray-200">{leadInfo.conta_info.razao_social}</p>
            </div>
          )}
          {(leadInfo.conta_info?.cnpj || leadInfo.cpf_cnpj) && (
            <div>
              <span className={labelCls}>CNPJ</span>
              <p className="text-gray-800 dark:text-gray-200">{leadInfo.conta_info?.cnpj || leadInfo.cpf_cnpj}</p>
            </div>
          )}
          {leadInfo.conta_info?.inscricao_estadual && (
            <div>
              <span className={labelCls}>Inscrição Estadual</span>
              <p className="text-gray-800 dark:text-gray-200">{leadInfo.conta_info.inscricao_estadual}</p>
            </div>
          )}
          <div>
            <span className={labelCls}>Email</span>
            <p className="text-gray-800 dark:text-gray-200">{leadInfo.conta_info?.email || leadInfo.email || '—'}</p>
          </div>
          <div>
            <span className={labelCls}>Telefone</span>
            <p className="text-gray-800 dark:text-gray-200">{leadInfo.conta_info?.telefone || leadInfo.telefone || '—'}</p>
          </div>
          {leadInfo.conta_info?.site && (
            <div className="sm:col-span-2">
              <span className={labelCls}>Site</span>
              <p className="text-gray-800 dark:text-gray-200">{leadInfo.conta_info.site}</p>
            </div>
          )}
          <div className="sm:col-span-2">
            <span className={labelCls}>Endereço</span>
            <p className="text-gray-800 dark:text-gray-200">
              {(() => {
                const endereco = leadInfo.conta_info || leadInfo;
                const partes = [
                  endereco.logradouro,
                  endereco.numero ? `nº ${endereco.numero}` : '',
                  endereco.complemento,
                  endereco.bairro,
                  endereco.cidade && endereco.uf
                    ? `${endereco.cidade}/${endereco.uf}`
                    : endereco.cidade || endereco.uf,
                  endereco.cep ? `CEP ${endereco.cep}` : '',
                ].filter(Boolean);
                return partes.length > 0 ? partes.join(' - ') : '—';
              })()}
            </p>
          </div>
        </div>
      ) : form.oportunidade_id ? (
        <p className="text-xs text-gray-500">Carregando dados do cliente...</p>
      ) : (
        <p className="text-xs text-gray-500">Selecione uma oportunidade para ver os dados do cliente.</p>
      )}
    </>
  );

  const renderProdutosBlock = () => {
    if (!form.oportunidade_id) return null;
    if (itensOportunidade.length === 0) {
      return <p className="text-xs text-gray-500">Esta oportunidade não possui produtos ou serviços cadastrados.</p>;
    }
    const RECORRENCIA_LABEL: Record<string, string> = {
      unico: 'Único',
      mensal: 'Mensal',
      trimestral: 'Trimestral',
      anual: 'Anual',
    };
    const valorUnico = itensOportunidade
      .filter((i) => !i.produto_servico_recorrencia || i.produto_servico_recorrencia === 'unico')
      .reduce((s, i) => s + i.subtotal, 0);
    const valorMensal = itensOportunidade
      .filter((i) => i.produto_servico_recorrencia === 'mensal')
      .reduce((s, i) => s + i.subtotal, 0);
    const valorTrimestral = itensOportunidade
      .filter((i) => i.produto_servico_recorrencia === 'trimestral')
      .reduce((s, i) => s + i.subtotal, 0);
    const valorAnual = itensOportunidade
      .filter((i) => i.produto_servico_recorrencia === 'anual')
      .reduce((s, i) => s + i.subtotal, 0);
    const fmt = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

    return (
      <>
        <div className="rounded-lg border border-gray-200 dark:border-neutral-600 overflow-x-auto">
          <table className="w-full text-sm min-w-[480px]">
            <thead>
              <tr className="bg-gray-50 dark:bg-[#0d1f3c]/50">
                <th className="text-left py-2 px-3 font-medium">Item</th>
                <th className="text-center py-2 px-3 font-medium">Recorrência</th>
                <th className="text-right py-2 px-3 font-medium">Qtd</th>
                <th className="text-right py-2 px-3 font-medium">Preço Unit.</th>
                <th className="text-right py-2 px-3 font-medium">Subtotal</th>
              </tr>
            </thead>
            <tbody>
              {itensOportunidade.map((item) => (
                <tr key={item.id} className="border-t border-gray-100 dark:border-[#0d1f3c]">
                  <td className="py-2 px-3">
                    <span className="text-xs text-gray-500 dark:text-gray-400 mr-1">
                      {item.produto_servico_tipo === 'produto' ? 'Produto' : 'Serviço'}:
                    </span>
                    {item.produto_servico_nome}
                  </td>
                  <td className="py-2 px-3 text-center">
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded ${
                        item.produto_servico_recorrencia === 'mensal'
                          ? 'bg-blue-100 text-blue-700'
                          : item.produto_servico_recorrencia === 'anual'
                            ? 'bg-purple-100 text-purple-700'
                            : item.produto_servico_recorrencia === 'trimestral'
                              ? 'bg-indigo-100 text-indigo-700'
                              : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {RECORRENCIA_LABEL[item.produto_servico_recorrencia || 'unico'] || 'Único'}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right">{item.quantidade}</td>
                  <td className="py-2 px-3 text-right">
                    {parseFloat(item.preco_unitario).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </td>
                  <td className="py-2 px-3 text-right font-medium">
                    {item.subtotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {(valorMensal > 0 || valorTrimestral > 0 || valorAnual > 0) && (
          <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800 space-y-1">
            {valorUnico > 0 && (
              <p className="text-sm text-gray-700 dark:text-gray-300">
                <span className="font-medium">Adesão/Implantação:</span> {fmt(valorUnico)}
              </p>
            )}
            {valorMensal > 0 && (
              <p className="text-sm text-blue-700 dark:text-blue-300 font-semibold">
                Valor Mensal: {fmt(valorMensal)}/mês
              </p>
            )}
            {valorTrimestral > 0 && (
              <p className="text-sm text-indigo-700 dark:text-indigo-300 font-semibold">
                Valor Trimestral: {fmt(valorTrimestral)}/trimestre
              </p>
            )}
            {valorAnual > 0 && (
              <p className="text-sm text-purple-700 dark:text-purple-300 font-semibold">
                Valor Anual: {fmt(valorAnual)}/ano
              </p>
            )}
          </div>
        )}
      </>
    );
  };

  const renderValoresBlock = () => {
    if (!form.oportunidade_id) return null;
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className={labelCls}>Valor total (R$)</label>
          <input
            type="number"
            min="0"
            step="0.01"
            value={form.valor_total}
            onChange={(e) => onFormChange((f) => ({ ...f, valor_total: e.target.value }))}
            className={inputCls}
            placeholder="0,00"
          />
        </div>
        <div>
          <label className={labelCls}>Desconto</label>
          <div className="flex gap-2">
            <select
              value={form.desconto_tipo || 'percentual'}
              onChange={(e) =>
                onFormChange((f) => ({ ...f, desconto_tipo: e.target.value as 'percentual' | 'valor' }))
              }
              className={`${inputCls} max-w-[120px]`}
            >
              <option value="percentual">%</option>
              <option value="valor">R$</option>
            </select>
            <input
              type="number"
              min="0"
              step="0.01"
              max={form.desconto_tipo === 'percentual' ? '100' : undefined}
              value={form.desconto_valor || ''}
              onChange={(e) => onFormChange((f) => ({ ...f, desconto_valor: e.target.value }))}
              className={inputCls}
              placeholder={form.desconto_tipo === 'percentual' ? '0%' : '0,00'}
            />
          </div>
          {form.valor_total && form.desconto_valor && parseFloat(form.desconto_valor) > 0 && (
            <p className="text-xs text-green-600 dark:text-green-400 mt-1">
              Valor com desconto:{' '}
              {(() => {
                const base = parseFloat(form.valor_total) || 0;
                const desc = parseFloat(form.desconto_valor) || 0;
                const final_val =
                  form.desconto_tipo === 'percentual'
                    ? Math.max(base - (base * desc) / 100, 0)
                    : Math.max(base - desc, 0);
                return final_val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
              })()}
            </p>
          )}
        </div>
      </div>
    );
  };

  const renderConteudoBlock = () => (
    <>
      {templates.length > 0 && onSelecionarTemplate && (
        <div>
          <label className={labelCls}>Usar template</label>
          <select
            onChange={(e) => {
              const template = templates.find((t) => String(t.id) === e.target.value);
              if (template) onSelecionarTemplate(template.conteudo, template.nome);
              e.target.value = '';
            }}
            className={inputCls}
            defaultValue=""
          >
            <option value="">Selecione um template (opcional)</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nome} {t.is_padrao ? '(PADRÃO)' : ''}
              </option>
            ))}
          </select>
        </div>
      )}
      <div>
        <div className="flex items-center justify-between gap-2 mb-1">
          <label className={labelCls}>Conteúdo</label>
          {onSalvarComoPadrao && form.conteudo.trim() && (
            <button
              type="button"
              onClick={() => onSalvarComoPadrao(form.conteudo)}
              disabled={salvandoPadrao}
              className="text-xs text-[#0176d3] hover:underline disabled:opacity-50"
            >
              {salvandoPadrao ? 'Salvando...' : 'Salvar como Proposta PADRAO'}
            </button>
          )}
        </div>
        <textarea
          value={form.conteudo}
          onChange={(e) => onFormChange((f) => ({ ...f, conteudo: e.target.value }))}
          className={`${inputCls} min-h-[200px] lg:min-h-[240px] resize-y`}
          rows={10}
          placeholder="Descrição detalhada da proposta..."
        />
      </div>
    </>
  );

  const renderAssinaturasBlock = () => (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <label className={labelCls}>Nome do Vendedor</label>
        <input
          type="text"
          value={form.nome_vendedor_assinatura || ''}
          onChange={(e) => onFormChange((f) => ({ ...f, nome_vendedor_assinatura: e.target.value }))}
          className={inputCls}
          placeholder={vendedorNome || 'Nome do vendedor'}
        />
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Nome que aparecerá na assinatura do PDF</p>
      </div>
      <div>
        <label className={labelCls}>Nome do Cliente</label>
        <input
          type="text"
          value={form.nome_cliente_assinatura || ''}
          onChange={(e) => onFormChange((f) => ({ ...f, nome_cliente_assinatura: e.target.value }))}
          className={inputCls}
          placeholder={leadInfo?.nome || 'Nome do cliente'}
        />
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Nome que aparecerá na assinatura do PDF</p>
      </div>
    </div>
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
              <h3 className={sectionTitleClass}>Proposta</h3>
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
              <h3 className={sectionTitleClass}>Produtos e serviços</h3>
              {renderProdutosBlock() || (
                <p className="text-xs text-gray-500">Selecione uma oportunidade para ver os itens.</p>
              )}
            </section>
            {form.oportunidade_id && (
              <section className="space-y-4">
                <h3 className={sectionTitleClass}>Valores</h3>
                {renderValoresBlock()}
              </section>
            )}
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

  return (
    <form onSubmit={onSubmit} className={formClass}>
      {formErro && !hideError && (
        <p className={`text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg ${spanClass}`}>
          {formErro}
        </p>
      )}

      {/* Dados da Loja */}
      <div className={`${sectionWrapCls} ${spanClass}`}>
        <p className={sectionTitleCls}>Dados da Loja</p>
        {lojaInfo ? (
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className={labelCls}>Nome da loja</span>
              <p className="font-medium">{lojaInfo.nome}</p>
            </div>
            {lojaInfo.endereco && (
              <div className="col-span-2">
                <span className={labelCls}>Endereço da loja</span>
                <p>{lojaInfo.endereco}</p>
              </div>
            )}
            {lojaInfo.cpf_cnpj && (
              <div>
                <span className={labelCls}>CPF ou CNPJ da loja</span>
                <p>{lojaInfo.cpf_cnpj}</p>
              </div>
            )}
            {lojaInfo.admin_nome && (
              <div>
                <span className={labelCls}>Nome do administrador</span>
                <p>{lojaInfo.admin_nome}</p>
              </div>
            )}
            {lojaInfo.admin_email && (
              <div>
                <span className={labelCls}>Email do administrador</span>
                <p>{lojaInfo.admin_email}</p>
              </div>
            )}
          </div>
        ) : (
          <p className="text-xs text-gray-500">Carregando...</p>
        )}
      </div>

      {/* Dados do Cliente */}
      <div className={`${sectionWrapCls} ${spanClass}`}>
        <p className={sectionTitleCls}>Dados do Cliente</p>
        {leadInfo ? (
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className={labelCls}>Nome</span>
              <p className="font-medium">{leadInfo.conta_info?.nome || (leadInfo.cpf_cnpj?.replace(/\D/g, '').length === 11 ? leadInfo.nome : (leadInfo.empresa || leadInfo.nome))}</p>
            </div>
            {leadInfo.conta_info?.razao_social && (
              <div>
                <span className={labelCls}>Razão Social</span>
                <p>{leadInfo.conta_info.razao_social}</p>
              </div>
            )}
            {(leadInfo.conta_info?.cnpj || leadInfo.cpf_cnpj) && (
              <div>
                <span className={labelCls}>CNPJ</span>
                <p>{leadInfo.conta_info?.cnpj || leadInfo.cpf_cnpj}</p>
              </div>
            )}
            {leadInfo.conta_info?.inscricao_estadual && (
              <div>
                <span className={labelCls}>Inscrição Estadual</span>
                <p>{leadInfo.conta_info.inscricao_estadual}</p>
              </div>
            )}
            <div>
              <span className={labelCls}>Email</span>
              <p>{leadInfo.conta_info?.email || leadInfo.email || '—'}</p>
            </div>
            <div>
              <span className={labelCls}>Telefone</span>
              <p>{leadInfo.conta_info?.telefone || leadInfo.telefone || '—'}</p>
            </div>
            {leadInfo.conta_info?.site && (
              <div className="col-span-2">
                <span className={labelCls}>Site</span>
                <p>{leadInfo.conta_info.site}</p>
              </div>
            )}
            <div className="col-span-2">
              <span className={labelCls}>Endereço</span>
              <p>
                {(() => {
                  // Priorizar endereço da conta
                  const endereco = leadInfo.conta_info || leadInfo;
                  const partes = [
                    endereco.logradouro,
                    endereco.numero ? `nº ${endereco.numero}` : '',
                    endereco.complemento,
                    endereco.bairro,
                    endereco.cidade && endereco.uf ? `${endereco.cidade}/${endereco.uf}` : endereco.cidade || endereco.uf,
                    endereco.cep ? `CEP ${endereco.cep}` : '',
                  ].filter(Boolean);
                  return partes.length > 0 ? partes.join(' - ') : '—';
                })()}
              </p>
            </div>
          </div>
        ) : form.oportunidade_id ? (
          <p className="text-xs text-gray-500">Carregando dados do cliente...</p>
        ) : (
          <p className="text-xs text-gray-500">Selecione uma oportunidade para ver os dados do cliente.</p>
        )}
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
      {form.oportunidade_id && itensOportunidade.length > 0 && (() => {
        const RECORRENCIA_LABEL: Record<string, string> = { unico: 'Único', mensal: 'Mensal', trimestral: 'Trimestral', anual: 'Anual' };
        const valorUnico = itensOportunidade.filter(i => !i.produto_servico_recorrencia || i.produto_servico_recorrencia === 'unico').reduce((s, i) => s + i.subtotal, 0);
        const valorMensal = itensOportunidade.filter(i => i.produto_servico_recorrencia === 'mensal').reduce((s, i) => s + i.subtotal, 0);
        const valorTrimestral = itensOportunidade.filter(i => i.produto_servico_recorrencia === 'trimestral').reduce((s, i) => s + i.subtotal, 0);
        const valorAnual = itensOportunidade.filter(i => i.produto_servico_recorrencia === 'anual').reduce((s, i) => s + i.subtotal, 0);
        const fmt = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

        return (
          <div className={spanClass}>
            <label className={labelCls}>
              Produtos e Serviços da Oportunidade
            </label>
            <div className="rounded-lg border border-gray-200 dark:border-gray-600 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-[#0d1f3c]/50">
                    <th className="text-left py-2 px-3 font-medium">Item</th>
                    <th className="text-center py-2 px-3 font-medium">Recorrência</th>
                    <th className="text-right py-2 px-3 font-medium">Qtd</th>
                    <th className="text-right py-2 px-3 font-medium">Preço Unit.</th>
                    <th className="text-right py-2 px-3 font-medium">Subtotal</th>
                  </tr>
                </thead>
                <tbody>
                  {itensOportunidade.map((item) => (
                    <tr key={item.id} className="border-t border-gray-100 dark:border-[#0d1f3c]">
                      <td className="py-2 px-3">
                        <span className="text-xs text-gray-500 dark:text-gray-400 mr-1">
                          {item.produto_servico_tipo === 'produto' ? 'Produto' : 'Serviço'}:
                        </span>
                        {item.produto_servico_nome}
                      </td>
                      <td className="py-2 px-3 text-center">
                        <span className={`text-xs px-1.5 py-0.5 rounded ${item.produto_servico_recorrencia === 'mensal' ? 'bg-blue-100 text-blue-700' : item.produto_servico_recorrencia === 'anual' ? 'bg-purple-100 text-purple-700' : item.produto_servico_recorrencia === 'trimestral' ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600'}`}>
                          {RECORRENCIA_LABEL[item.produto_servico_recorrencia || 'unico'] || 'Único'}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-right">{item.quantidade}</td>
                      <td className="py-2 px-3 text-right">
                        {parseFloat(item.preco_unitario).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                      </td>
                      <td className="py-2 px-3 text-right font-medium">
                        {item.subtotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {/* Resumo: Adesão + Mensal */}
            {(valorMensal > 0 || valorTrimestral > 0 || valorAnual > 0) && (
              <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800 space-y-1">
                {valorUnico > 0 && (
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    <span className="font-medium">Adesão/Implantação:</span> {fmt(valorUnico)}
                  </p>
                )}
                {valorMensal > 0 && (
                  <p className="text-sm text-blue-700 dark:text-blue-300 font-semibold">
                    💰 Valor Mensal: {fmt(valorMensal)}/mês
                  </p>
                )}
                {valorTrimestral > 0 && (
                  <p className="text-sm text-indigo-700 dark:text-indigo-300 font-semibold">
                    💰 Valor Trimestral: {fmt(valorTrimestral)}/trimestre
                  </p>
                )}
                {valorAnual > 0 && (
                  <p className="text-sm text-purple-700 dark:text-purple-300 font-semibold">
                    💰 Valor Anual: {fmt(valorAnual)}/ano
                  </p>
                )}
              </div>
            )}
          </div>
        );
      })()}

      {form.oportunidade_id && itensOportunidade.length === 0 && (
        <p className={`text-xs text-gray-500 ${spanClass}`}>Esta oportunidade não possui produtos ou serviços cadastrados.</p>
      )}

      {/* Valor total */}
      {form.oportunidade_id && (
        <div className={spanClass}>
          <label className={labelCls}>Valor total (R$)</label>
          <input
            type="number"
            min="0"
            step="0.01"
            value={form.valor_total}
            onChange={(e) => onFormChange((f) => ({ ...f, valor_total: e.target.value }))}
            className={`${inputCls} max-w-[200px]`}
            placeholder="0,00"
          />
        </div>
      )}

      {/* Desconto */}
      {form.oportunidade_id && (
        <div className={spanClass}>
          <label className={labelCls}>Desconto</label>
          <div className="flex gap-2 items-end">
            <select
              value={form.desconto_tipo || 'percentual'}
              onChange={(e) => onFormChange((f) => ({ ...f, desconto_tipo: e.target.value as 'percentual' | 'valor' }))}
              className={`${inputCls} max-w-[160px]`}
            >
              <option value="percentual">Percentual (%)</option>
              <option value="valor">Valor fixo (R$)</option>
            </select>
            <input
              type="number"
              min="0"
              step="0.01"
              max={form.desconto_tipo === 'percentual' ? '100' : undefined}
              value={form.desconto_valor || ''}
              onChange={(e) => onFormChange((f) => ({ ...f, desconto_valor: e.target.value }))}
              className={`${inputCls} max-w-[160px]`}
              placeholder={form.desconto_tipo === 'percentual' ? '0%' : '0,00'}
            />
          </div>
          {form.valor_total && form.desconto_valor && parseFloat(form.desconto_valor) > 0 && (
            <p className="text-xs text-green-600 dark:text-green-400 mt-1">
              Valor com desconto:{' '}
              {(() => {
                const base = parseFloat(form.valor_total) || 0;
                const desc = parseFloat(form.desconto_valor) || 0;
                const final_val = form.desconto_tipo === 'percentual'
                  ? Math.max(base - (base * desc / 100), 0)
                  : Math.max(base - desc, 0);
                return final_val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
              })()}
            </p>
          )}
        </div>
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

      {/* Seletor de Template */}
      {templates.length > 0 && onSelecionarTemplate && (
        <div className={spanClass}>
          <label className={labelCls}>
            Usar template
          </label>
          <select
            onChange={(e) => {
              const template = templates.find(t => String(t.id) === e.target.value);
              if (template) {
                onSelecionarTemplate(template.conteudo, template.nome);
              }
              e.target.value = ''; // Reset select
            }}
            className={inputCls}
            defaultValue=""
          >
            <option value="">Selecione um template (opcional)</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nome} {t.is_padrao ? '(PADRÃO)' : ''}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Selecione um template para preencher o conteúdo automaticamente
          </p>
        </div>
      )}

      {/* Conteúdo */}
      <div className={spanClass}>
        <div className="flex items-center justify-between gap-2 mb-1">
          <label className={labelCls}>Conteúdo</label>
          {onSalvarComoPadrao && form.conteudo.trim() && (
            <button
              type="button"
              onClick={() => onSalvarComoPadrao(form.conteudo)}
              disabled={salvandoPadrao}
              className="text-xs text-[#0176d3] hover:underline disabled:opacity-50"
            >
              {salvandoPadrao ? 'Salvando...' : 'Salvar como Proposta PADRAO'}
            </button>
          )}
        </div>
        <textarea
          value={form.conteudo}
          onChange={(e) => onFormChange((f) => ({ ...f, conteudo: e.target.value }))}
          className={`${inputCls} ${usePageStyles ? 'min-h-[200px] lg:min-h-[280px]' : 'min-h-[120px] md:min-h-[180px]'}`}
          rows={usePageStyles ? 12 : 6}
          placeholder="Descrição detalhada da proposta..."
        />
      </div>

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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>
              Nome do Vendedor
            </label>
            <input
              type="text"
              value={form.nome_vendedor_assinatura || ''}
              onChange={(e) => onFormChange((f) => ({ ...f, nome_vendedor_assinatura: e.target.value }))}
              className={inputCls}
              placeholder={vendedorNome || 'Nome do vendedor'}
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Nome que aparecerá na assinatura do PDF
            </p>
          </div>
          <div>
            <label className={labelCls}>
              Nome do Cliente
            </label>
            <input
              type="text"
              value={form.nome_cliente_assinatura || ''}
              onChange={(e) => onFormChange((f) => ({ ...f, nome_cliente_assinatura: e.target.value }))}
              className={inputCls}
              placeholder={leadInfo?.nome || 'Nome do cliente'}
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Nome que aparecerá na assinatura do PDF
            </p>
          </div>
        </div>
      </div>

      {/* Botões (modal / formulário embutido) */}
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
