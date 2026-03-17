'use client';

import type { LojaInfo, LeadInfo, OportunidadeItem, FormDataProposta } from './modals/ModalPropostaForm';

export interface PropostaFormContentProps {
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
  isEdit?: boolean;
  onSalvarComoPadrao?: (conteudo: string) => void;
  salvandoPadrao?: boolean;
  /** Se true, mostra botão Cancelar que chama onCancel */
  showCancel?: boolean;
  onCancel?: () => void;
  /** Se true, formulário ocupa largura total (para página fullscreen) */
  fullWidth?: boolean;
  /** Se true, select de oportunidade mostra estado de carregamento */
  loadingOportunidades?: boolean;
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
  oportunidades,
  itensOportunidade,
  statusOpcoes,
  onFormChange,
  onOportunidadeChange,
  onSubmit,
  isEdit = false,
  onSalvarComoPadrao,
  salvandoPadrao = false,
  showCancel = true,
  onCancel,
  fullWidth = false,
  loadingOportunidades = false,
}: PropostaFormContentProps) {
  const formClass = fullWidth
    ? 'space-y-4 w-full md:grid md:grid-cols-2 md:gap-x-6 lg:gap-x-8'
    : 'space-y-4 md:max-w-3xl md:mx-auto md:grid md:grid-cols-2 md:gap-x-6';
  return (
    <form onSubmit={onSubmit} className={formClass}>
      {formErro && (
        <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg md:col-span-2">
          {formErro}
        </p>
      )}

      {/* Dados da Loja */}
      <div className={`${sectionClass} md:col-span-2`}>
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Dados da Loja</p>
        {lojaInfo ? (
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className={labelClass}>Nome da loja</span>
              <p className="font-medium">{lojaInfo.nome}</p>
            </div>
            {lojaInfo.endereco && (
              <div className="col-span-2">
                <span className={labelClass}>Endereço da loja</span>
                <p>{lojaInfo.endereco}</p>
              </div>
            )}
            {lojaInfo.cpf_cnpj && (
              <div>
                <span className={labelClass}>CPF ou CNPJ da loja</span>
                <p>{lojaInfo.cpf_cnpj}</p>
              </div>
            )}
            {lojaInfo.admin_nome && (
              <div>
                <span className={labelClass}>Nome do administrador</span>
                <p>{lojaInfo.admin_nome}</p>
              </div>
            )}
            {lojaInfo.admin_email && (
              <div>
                <span className={labelClass}>Email do administrador</span>
                <p>{lojaInfo.admin_email}</p>
              </div>
            )}
          </div>
        ) : (
          <p className="text-xs text-gray-500">Carregando...</p>
        )}
      </div>

      {/* Dados do Cliente */}
      <div className={`${sectionClass} md:col-span-2`}>
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Dados do Cliente</p>
        {leadInfo ? (
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className={labelClass}>Nome</span>
              <p className="font-medium">{leadInfo.nome}</p>
            </div>
            <div>
              <span className={labelClass}>Empresa</span>
              <p>{leadInfo.empresa || '—'}</p>
            </div>
            {(leadInfo.cpf_cnpj) && (
              <div>
                <span className={labelClass}>CPF/CNPJ</span>
                <p>{leadInfo.cpf_cnpj}</p>
              </div>
            )}
            <div>
              <span className={labelClass}>Email</span>
              <p>{leadInfo.email || '—'}</p>
            </div>
            <div>
              <span className={labelClass}>Telefone</span>
              <p>{leadInfo.telefone || '—'}</p>
            </div>
            <div className="col-span-2">
              <span className={labelClass}>Endereço</span>
              <p>
                {[leadInfo.logradouro, leadInfo.numero, leadInfo.complemento, leadInfo.bairro, leadInfo.cidade, leadInfo.uf, leadInfo.cep]
                  .filter(Boolean).length > 0
                  ? [
                      leadInfo.logradouro,
                      leadInfo.numero ? `nº ${leadInfo.numero}` : '',
                      leadInfo.complemento,
                      leadInfo.bairro,
                      leadInfo.cidade && leadInfo.uf ? `${leadInfo.cidade}/${leadInfo.uf}` : leadInfo.cidade || leadInfo.uf,
                      leadInfo.cep ? `CEP ${leadInfo.cep}` : '',
                    ].filter(Boolean).join(' - ')
                  : '—'}
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
      <div className="md:col-span-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Oportunidade *</label>
        <select
          value={form.oportunidade_id}
          onChange={(e) => onOportunidadeChange(e.target.value)}
          className={inputClass}
          required
          disabled={isEdit || loadingOportunidades}
        >
          <option value="">
            {loadingOportunidades ? 'Carregando oportunidades...' : 'Selecione'}
          </option>
          {!loadingOportunidades && oportunidades.map((o) => (
            <option key={o.id} value={o.id}>{o.titulo} - {o.lead_nome}</option>
          ))}
        </select>
      </div>

      {/* Produtos e Serviços */}
      {form.oportunidade_id && itensOportunidade.length > 0 && (
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Produtos e Serviços da Oportunidade
          </label>
          <div className="rounded-lg border border-gray-200 dark:border-gray-600 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-[#0d1f3c]/50">
                  <th className="text-left py-2 px-3 font-medium">Item</th>
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
        </div>
      )}

      {form.oportunidade_id && itensOportunidade.length === 0 && (
        <p className="text-xs text-gray-500 md:col-span-2">Esta oportunidade não possui produtos ou serviços cadastrados.</p>
      )}

      {/* Valor total */}
      {form.oportunidade_id && (
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Valor total (R$)</label>
          <input
            type="number"
            min="0"
            step="0.01"
            value={form.valor_total}
            onChange={(e) => onFormChange((f) => ({ ...f, valor_total: e.target.value }))}
            className={`${inputClass} max-w-[200px]`}
            placeholder="0,00"
          />
        </div>
      )}

      {/* Título */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Título *</label>
        <input
          type="text"
          value={form.titulo}
          onChange={(e) => onFormChange((f) => ({ ...f, titulo: e.target.value }))}
          className={inputClass}
          placeholder="Título da proposta"
          required
        />
      </div>

      {/* Conteúdo */}
      <div className="md:col-span-2">
        <div className="flex items-center justify-between gap-2 mb-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Conteúdo</label>
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
          className={`${inputClass} ${fullWidth ? 'min-h-[200px] md:min-h-[300px]' : 'min-h-[120px] md:min-h-[180px]'}`}
          rows={fullWidth ? 12 : 6}
          placeholder="Descrição detalhada da proposta..."
        />
      </div>

      {/* Status */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
        <select
          value={form.status}
          onChange={(e) => onFormChange((f) => ({ ...f, status: e.target.value }))}
          className={inputClass}
        >
          {statusOpcoes.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Botões */}
      <div className="flex gap-2 pt-2 md:col-span-2">
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
    </form>
  );
}
