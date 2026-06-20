'use client';

import type { LojaInfo, LeadInfo } from './modals/ModalPropostaForm';
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
    <>
      <h3 className={sectionTitleClass}>Dados da Loja</h3>
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
      <h3 className={sectionTitleClass}>Dados do Cliente</h3>
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
          <div>
            <span className={labelCls}>Email</span>
            <p className="text-gray-800 dark:text-gray-200">{leadInfo.conta_info?.email || leadInfo.email || '—'}</p>
          </div>
          <div>
            <span className={labelCls}>Telefone</span>
            <p className="text-gray-800 dark:text-gray-200">{leadInfo.conta_info?.telefone || leadInfo.telefone || '—'}</p>
          </div>
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
    <>
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
    </>
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
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Dados da Loja</p>
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

      <div className={`${sectionClass} ${spanClass}`}>
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Dados do Cliente</p>
        {leadInfo ? (
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className={labelCls}>Nome</span>
              <p className="font-medium">{leadInfo.nome}</p>
            </div>
            {leadInfo.empresa && leadInfo.cpf_cnpj?.replace(/\D/g, '').length !== 11 && (
              <div>
                <span className={labelCls}>Empresa</span>
                <p>{leadInfo.empresa}</p>
              </div>
            )}
            {leadInfo.cpf_cnpj && (
              <div>
                <span className={labelCls}>CPF/CNPJ</span>
                <p>{leadInfo.cpf_cnpj}</p>
              </div>
            )}
            <div>
              <span className={labelCls}>Email</span>
              <p>{leadInfo.email || '—'}</p>
            </div>
            <div>
              <span className={labelCls}>Telefone</span>
              <p>{leadInfo.telefone || '—'}</p>
            </div>
          </div>
        ) : form.oportunidade_id ? (
          <p className="text-xs text-gray-500">Carregando dados do cliente...</p>
        ) : (
          <p className="text-xs text-gray-500">Selecione uma oportunidade para ver os dados do cliente.</p>
        )}
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
      </div>

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
