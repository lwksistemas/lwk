'use client';

import Link from 'next/link';
import BuscarLeadInput from '@/components/crm-vendas/BuscarLeadInput';
import OportunidadeItensEditor from '@/components/crm-vendas/OportunidadeItensEditor';
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
    leadLabel,
    handleLeadChange,
    leadResumo,
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
      <BuscarLeadInput
        leadId={form.lead_id}
        onLeadChange={handleLeadChange}
        initialNome={leadLabel}
        placeholder={
          isPage
            ? 'Buscar lead pelo nome, empresa, e-mail ou CPF/CNPJ...'
            : 'Buscar lead pelo nome, empresa ou CPF/CNPJ...'
        }
        required
        inputClassName={inputCls}
        limit={15}
      />
      {form.lead_id && leadResumo && (
        <p className={`text-xs text-green-600 dark:text-green-400 mt-1 ${isPage ? 'font-medium' : ''}`}>
          ✓ {leadResumo.nome}
        </p>
      )}
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
        Não encontrou?{' '}
        <Link href={`/loja/${slug}/crm-vendas/leads/novo`} className={`underline ${isPage ? 'font-medium' : ''}`}>
          Cadastrar novo lead
        </Link>
        .
      </p>
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
    <OportunidadeItensEditor
      slug={slug}
      produtos={produtosServicos}
      itens={form.itens}
      seletorAberto={seletorAberto}
      onSeletorAbertoChange={setSeletorAberto}
      onUpdateItem={updateItem}
      onRemoveItem={removeItem}
      onAddProduto={adicionarProduto}
      layout={layout}
    />
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
