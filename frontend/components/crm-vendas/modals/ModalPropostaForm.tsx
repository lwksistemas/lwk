'use client';

import { X } from 'lucide-react';

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
}: ModalPropostaFormProps) {
  const inputClass = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white';
  const labelClass = 'block text-xs text-gray-500 dark:text-gray-400 mb-0.5';
  const sectionClass = 'space-y-3 border-b border-gray-200 dark:border-gray-600 pb-4';

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
        <form onSubmit={onSubmit} className="p-4 space-y-4 md:max-w-3xl md:mx-auto md:grid md:grid-cols-2 md:gap-x-6">
          {formErro && (
            <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg md:col-span-2">
              {formErro}
            </p>
          )}

          {/* Dados da Loja - nome, endereço, CPF/CNPJ, administrador (sem Site e Tipo) */}
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
              disabled={isEdit}
            >
              <option value="">Selecione</option>
              {oportunidades.map((o) => (
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

          {/* Valor total */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Valor total (R$)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={form.valor_total}
              onChange={(e) => onFormChange((f) => ({ ...f, valor_total: e.target.value }))}
              className={inputClass}
              placeholder="0,00"
            />
          </div>

          {/* Conteúdo */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Conteúdo</label>
            <textarea
              value={form.conteudo}
              onChange={(e) => onFormChange((f) => ({ ...f, conteudo: e.target.value }))}
              className={`${inputClass} min-h-[100px]`}
              rows={4}
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
            <button
              type="button"
              onClick={() => !enviando && onClose()}
              className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={enviando}
              className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium"
            >
              {enviando ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
