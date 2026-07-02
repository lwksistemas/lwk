'use client';

import BuscarContaInput from '@/components/crm-vendas/BuscarContaInput';
import { formatTelefone, toUpperCase } from '@/lib/format-br';
import type { CrmContatoFormData } from '@/lib/crm-contato-form-types';

const inputClassModal =
  'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0176d3] focus:border-transparent';
const inputClassPage =
  'w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#1e3a5f] text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0176d3] focus:ring-offset-0';
const labelClassPage =
  'block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1';

interface Props {
  formData: CrmContatoFormData;
  contaNomeInicial?: string;
  disabled?: boolean;
  layout: 'modal' | 'page';
  onChange: (data: CrmContatoFormData) => void;
}

export function ContatoFormFields({
  formData,
  contaNomeInicial,
  disabled = false,
  layout,
  onChange,
}: Props) {
  const inputCls = layout === 'page' ? inputClassPage : inputClassModal;
  const labelCls =
    layout === 'page'
      ? labelClassPage
      : 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1';

  const set = (field: keyof CrmContatoFormData, value: string) =>
    onChange({ ...formData, [field]: value });
  const setUpper = (field: keyof CrmContatoFormData, value: string) =>
    onChange({ ...formData, [field]: toUpperCase(value) });
  const setPhone = (field: keyof CrmContatoFormData, value: string) =>
    onChange({ ...formData, [field]: formatTelefone(value) });

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="md:col-span-2">
        <label className={labelCls}>
          Nome <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={formData.nome}
          onChange={(e) => setUpper('nome', e.target.value)}
          className={inputCls}
          required
          disabled={disabled}
        />
      </div>
      <div className="md:col-span-2">
        <label className={labelCls}>
          Conta <span className="text-red-500">*</span>
        </label>
        <BuscarContaInput
          contaId={formData.conta}
          initialNome={contaNomeInicial}
          onContaChange={(id) => set('conta', id)}
          required
          disabled={disabled}
          inputClassName={inputCls}
        />
      </div>
      <div>
        <label className={labelCls}>Cargo</label>
        <input
          type="text"
          value={formData.cargo}
          onChange={(e) => setUpper('cargo', e.target.value)}
          className={inputCls}
          placeholder="Ex: Gerente de Compras"
          disabled={disabled}
        />
      </div>
      <div>
        <label className={labelCls}>Telefone</label>
        <input
          type="tel"
          value={formData.telefone}
          onChange={(e) => setPhone('telefone', e.target.value)}
          className={inputCls}
          placeholder="(00) 00000-0000"
          disabled={disabled}
        />
      </div>
      <div className="md:col-span-2">
        <label className={labelCls}>Email</label>
        <input
          type="email"
          value={formData.email}
          onChange={(e) => set('email', e.target.value)}
          className={inputCls}
          disabled={disabled}
        />
      </div>
      <div className="md:col-span-2">
        <label className={labelCls}>Observações</label>
        <textarea
          value={formData.observacoes}
          onChange={(e) => set('observacoes', e.target.value)}
          rows={3}
          className={inputCls}
          disabled={disabled}
        />
      </div>
    </div>
  );
}
