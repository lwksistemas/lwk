'use client';

import Link from 'next/link';
import { X } from 'lucide-react';
import ProdutoSeletorCategoria from '@/components/crm-vendas/ProdutoSeletorCategoria';
import type { UseOportunidadeFormReturn } from '@/hooks/crm-vendas/useOportunidadeForm';

const inputClassModal =
  'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm';
const inputClassPage =
  'w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#1e3a5f] text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0176d3] focus:ring-offset-0';
const labelClassPage =
  'block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1';
const sectionTitlePage =
  'text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-[#0d1f3c] pb-2';

interface Props {
  slug: string;
  etapas: { key: string; label: string }[];
  layout: 'modal' | 'page';
  formState: UseOportunidadeFormReturn;
}

export default function OportunidadeFormFields({ slug, etapas, layout, formState }: Props) {
  const {
    form,
    setForm,
    leads,
    leadBusca,
    setLeadBusca,
    leadsFiltrados,
    selecionarLead,
    contas,
    produtosServicos,
    seletorAberto,
    setSeletorAberto,
    updateItem,
    removeItem,
    adicionarProduto,
  } = formState;

  const isPage = layout === 'page';
  const inputCls = isPage ? inputClassPage : inputClassModal;
  const labelCls = isPage ? labelClassPage : 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1';

  const leadField = (
    <div>
      <label className={labelCls}>Lead *</label>
      <input
        type="text"
        placeholder={isPage ? 'Digite o nome do lead...' : 'Buscar lead pelo nome...'}
        value={leadBusca}
        onChange={(e) => {
          setLeadBusca(e.target.value);
          setForm((f) => ({ ...f, lead_id: '' }));
        }}
        className={inputCls}
      />
      {leadBusca.trim() && !form.lead_id && leadsFiltrados.length > 0 && (
        <div
          className={`w-full mt-1 border rounded-lg bg-white dark:bg-gray-700 max-h-40 overflow-y-auto shadow-sm ${
            isPage ? 'border-gray-200 dark:border-neutral-600 dark:bg-[#1e3a5f] max-h-48' : 'border-gray-300 dark:border-gray-600'
          }`}
        >
          {leadsFiltrados.map((l) => (
            <button
              key={l.id}
              type="button"
              onClick={() => selecionarLead(l)}
              className={`w-full text-left px-3 py-2 text-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-600 border-b border-gray-100 dark:border-gray-600 last:border-b-0 ${
                isPage ? 'py-2.5 dark:hover:bg-[#264a73] transition' : ''
              }`}
            >
              {l.nome}
            </button>
          ))}
        </div>
      )}
      {leadBusca.trim() && !form.lead_id && leadsFiltrados.length === 0 && (
        <p className="text-xs text-gray-500 mt-1">Nenhum lead encontrado.</p>
      )}
      {form.lead_id && (
        <p className={`text-xs text-green-600 dark:text-green-400 mt-1 ${isPage ? 'font-medium' : ''}`}>
          ✓ {leads.find((l) => String(l.id) === form.lead_id)?.nome}
        </p>
      )}
      {leads.length === 0 && (
        <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
          Nenhum lead cadastrado.{' '}
          <Link href={`/loja/${slug}/crm-vendas/leads`} className={`underline ${isPage ? 'font-medium' : ''}`}>
            Cadastre em Leads
          </Link>
          .
        </p>
      )}
    </div>
  );

  const prestadoraField = (
    <div>
      <label className={labelCls}>Empresa prestadora *</label>
      {contas.length > 0 ? (
        <select
          value={form.empresa_prestadora_id}
          onChange={(e) => {
            const id = e.target.value;
            const conta = contas.find((c) => String(c.id) === id);
            setForm((f) => ({
              ...f,
              empresa_prestadora_id: id,
              titulo: isPage && conta ? conta.nome : f.titulo,
            }));
          }}
          className={inputCls}
          required
        >
          <option value="">Selecione a empresa prestadora</option>
          {contas.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nome}
              {c.cnpj ? ` — ${c.cnpj}` : ''}
            </option>
          ))}
        </select>
      ) : (
        <p className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
          Nenhuma empresa prestadora cadastrada. Cadastre em{' '}
          <Link href={`/loja/${slug}/crm-vendas/contas`} className="underline font-medium">
            Contas
          </Link>{' '}
          com tipo &quot;Prestadora&quot;.
        </p>
      )}
    </div>
  );

  const etapaField = (
    <div>
      <label className={labelCls}>Etapa inicial</label>
      <select
        value={form.etapa}
        onChange={(e) => setForm((f) => ({ ...f, etapa: e.target.value }))}
        className={inputCls}
      >
        {etapas.map((o) => (
          <option key={o.key} value={o.key}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );

  const itensField = (
    <div>
      <div className={`flex items-center justify-between ${isPage ? 'border-b border-gray-100 dark:border-[#0d1f3c] pb-2' : 'mb-1'}`}>
        <label className={isPage ? sectionTitlePage.replace('border-b pb-2', '') : labelCls}>
          {isPage ? 'Produtos e serviços' : 'Produtos e Serviços'}
        </label>
        <Link href={`/loja/${slug}/crm-vendas/produtos-servicos`} className="text-xs text-[#0176d3] hover:underline">
          Cadastrar
        </Link>
      </div>
      {form.itens.map((item, idx) => {
        const ps = produtosServicos.find((p) => p.id === item.produto_servico_id);
        return (
          <div
            key={idx}
            className={`flex gap-2 mb-2 items-center rounded-lg px-2 py-1.5 ${
              isPage ? 'bg-gray-50 dark:bg-[#1e3a5f] px-3 py-2' : 'bg-gray-50 dark:bg-gray-700/50'
            }`}
          >
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
                {ps?.codigo ? <span className="text-gray-400">[{ps.codigo}] </span> : null}
                {ps?.nome || 'Produto'}
              </p>
              {ps?.categoria_nome && (
                <p className="text-[10px] text-gray-500 dark:text-gray-400">{ps.categoria_nome}</p>
              )}
            </div>
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={item.preco_unitario}
              onChange={(e) => updateItem(idx, 'preco_unitario', e.target.value)}
              className={`px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 ${
                isPage ? 'w-24 py-1.5 rounded-lg dark:bg-[#264a73] dark:border-neutral-600' : 'w-20'
              }`}
              placeholder="Preço"
            />
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={item.quantidade}
              onChange={(e) => updateItem(idx, 'quantidade', e.target.value)}
              className={`px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 ${
                isPage ? 'w-16 py-1.5 rounded-lg dark:bg-[#264a73] dark:border-neutral-600' : 'w-14'
              }`}
              placeholder="Qtd"
            />
            <button
              type="button"
              onClick={() => removeItem(idx)}
              className={`rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-500 ${isPage ? 'p-1.5 transition' : 'p-1'}`}
            >
              <X size={isPage ? 14 : 13} />
            </button>
          </div>
        );
      })}
      {seletorAberto && produtosServicos.length > 0 && (
        <div className={isPage ? '' : 'mb-2'}>
          <ProdutoSeletorCategoria
            produtos={produtosServicos}
            itensSelecionados={form.itens.map((i) => i.produto_servico_id)}
            onSelecionar={adicionarProduto}
            onFechar={() => setSeletorAberto(false)}
          />
        </div>
      )}
      {produtosServicos.length > 0 && !seletorAberto && (
        <button
          type="button"
          onClick={() => setSeletorAberto(true)}
          className={`text-sm text-[#0176d3] hover:underline ${isPage ? 'font-medium' : ''}`}
        >
          + Adicionar item
        </button>
      )}
      {produtosServicos.length === 0 && (
        <p className="text-xs text-amber-600 dark:text-amber-400">
          Cadastre produtos/serviços em{' '}
          <Link href={`/loja/${slug}/crm-vendas/produtos-servicos`} className="underline font-medium">
            Produtos e Serviços
          </Link>
          .
        </p>
      )}
    </div>
  );

  const valorField = (
    <div>
      <label className={labelCls}>Valor (R$)</label>
      <input
        type="number"
        min="0"
        step="0.01"
        value={form.valor}
        onChange={(e) => setForm((f) => ({ ...f, valor: e.target.value }))}
        readOnly={form.itens.length > 0}
        className={`${inputCls} ${form.itens.length > 0 ? (isPage ? 'opacity-60 cursor-not-allowed' : 'bg-gray-50 dark:bg-gray-600/50 cursor-not-allowed') : ''}`}
        placeholder="0"
      />
      {form.itens.length > 0 && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Valor calculado automaticamente pelos itens</p>
      )}
    </div>
  );

  const comissaoField = (
    <div>
      <label className={labelCls}>{isPage ? 'Valor da comissão (R$)' : 'Valor da Comissão (R$)'}</label>
      <input
        type="number"
        min="0"
        step="0.01"
        value={form.valor_comissao}
        onChange={(e) => setForm((f) => ({ ...f, valor_comissao: e.target.value }))}
        className={inputCls}
        placeholder="0"
      />
    </div>
  );

  if (isPage) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 xl:gap-14 w-full">
        <div className="space-y-6">
          <section className="space-y-4">
            <h3 className={sectionTitlePage}>Lead</h3>
            {leadField}
          </section>
          <section className="space-y-4">
            <h3 className={sectionTitlePage}>Empresa prestadora</h3>
            {prestadoraField}
          </section>
          <section className="space-y-4">
            <h3 className={sectionTitlePage}>Etapa</h3>
            {etapaField}
          </section>
        </div>
        <div className="space-y-6">
          <section className="space-y-4">{itensField}</section>
          <section className="space-y-4">
            <h3 className={sectionTitlePage}>Valor e comissão</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {valorField}
              {comissaoField}
            </div>
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {leadField}
      {prestadoraField}
      {valorField}
      {itensField}
      {comissaoField}
      {etapaField}
    </div>
  );
}
