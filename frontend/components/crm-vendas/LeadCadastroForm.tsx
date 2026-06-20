'use client';

import {
  ArrowLeft,
  Building2,
  CreditCard,
  Loader2,
  Mail,
  MapPin,
  Phone,
  Save,
  User,
} from 'lucide-react';
import { CrmPagePanel, CRM_ACCENT } from '@/components/crm-vendas/CrmPagePanel';
import type { FormDataLead } from '@/components/crm-vendas/modals/ModalLeadForm';
import { formatTelefone, toUpperCase } from '@/lib/format-br';

const UF_LIST = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
];

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
      {children}
    </label>
  );
}

function IconInput({
  icon: Icon,
  className = '',
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { icon: typeof User }) {
  return (
    <div className="relative">
      <Icon
        size={16}
        className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
        aria-hidden
      />
      <input
        {...props}
        className={`w-full pl-9 pr-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#1e3a5f] text-gray-900 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0176d3] focus:ring-offset-0 ${className}`}
      />
    </div>
  );
}

interface LeadCadastroFormProps {
  editing?: boolean;
  form: FormDataLead;
  onFormChange: (updater: (f: FormDataLead) => FormDataLead) => void;
  error: string | null;
  saving: boolean;
  origensAtivas: () => Array<{ key: string; label: string }>;
  statusOpcoes: Array<{ value: string; label: string }>;
  buscarCepLoading: boolean;
  buscarCnpjLoading: boolean;
  onCepChange: (value: string) => void;
  onBuscarCep: () => void;
  onBuscarCnpj: () => void;
  onCpfCnpjChange: (value: string) => void;
  onSave: () => void;
  onCancel: () => void;
  showHeader?: boolean;
  accentColor?: string;
}

export function LeadCadastroForm({
  editing = false,
  form,
  onFormChange,
  error,
  saving,
  origensAtivas,
  statusOpcoes,
  buscarCepLoading,
  buscarCnpjLoading,
  onCepChange,
  onBuscarCep,
  onBuscarCnpj,
  onCpfCnpjChange,
  onSave,
  onCancel,
  showHeader = true,
  accentColor = CRM_ACCENT,
}: LeadCadastroFormProps) {
  const selectClass =
    'w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#1e3a5f] text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[#0176d3] focus:ring-offset-0';

  return (
    <div className="flex flex-col flex-1 min-h-0 w-full">
      {showHeader && (
        <div className="flex items-center justify-between gap-3 px-4 md:px-8 py-3 border-b border-gray-200 dark:border-[#0d1f3c] shrink-0 bg-white dark:bg-[#16325c]">
          <button
            type="button"
            onClick={onCancel}
            className="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
          >
            <ArrowLeft size={16} />
            Voltar à lista
          </button>
          <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">
            {editing ? 'Editar lead' : 'Novo lead'}
          </span>
          <div className="w-[100px]" aria-hidden />
        </div>
      )}

      <div className="flex-1 min-h-0 overflow-y-auto p-4 md:p-6 lg:p-8 bg-[#f3f2f2] dark:bg-[#0d1f3c]">
        {error && (
          <div className="mb-5 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
            {error}
          </div>
        )}

        <CrmPagePanel className="p-5 md:p-6 lg:p-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 xl:gap-14 w-full max-w-none">
            <div className="space-y-4">
              <p className="text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-[#0d1f3c] pb-2">
                Dados do lead
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="sm:col-span-2">
                  <FieldLabel>Nome completo *</FieldLabel>
                  <IconInput
                    icon={User}
                    value={form.nome}
                    onChange={(e) => onFormChange((f) => ({ ...f, nome: toUpperCase(e.target.value) }))}
                    placeholder="Nome completo do lead"
                    autoFocus
                    required
                  />
                </div>

                <div className="sm:col-span-2">
                  <FieldLabel>CPF ou CNPJ</FieldLabel>
                  <div className="flex flex-col sm:flex-row gap-2">
                    <IconInput
                      icon={CreditCard}
                      value={form.cpf_cnpj}
                      onChange={(e) => onCpfCnpjChange(e.target.value)}
                      placeholder="000.000.000-00 ou 00.000.000/0001-00"
                      inputMode="numeric"
                      className="sm:flex-1"
                    />
                    <button
                      type="button"
                      onClick={onBuscarCnpj}
                      disabled={buscarCnpjLoading || form.cpf_cnpj.replace(/\D/g, '').length !== 14}
                      className="shrink-0 px-3 py-2 rounded-lg border text-sm font-medium disabled:opacity-50 whitespace-nowrap"
                      style={{ borderColor: accentColor, color: accentColor }}
                    >
                      {buscarCnpjLoading ? '...' : 'Buscar CNPJ'}
                    </button>
                  </div>
                </div>

                {form.cpf_cnpj.replace(/\D/g, '').length !== 11 && (
                  <div className="sm:col-span-2">
                    <FieldLabel>Empresa</FieldLabel>
                    <IconInput
                      icon={Building2}
                      value={form.empresa}
                      onChange={(e) => onFormChange((f) => ({ ...f, empresa: toUpperCase(e.target.value) }))}
                      placeholder="Nome da empresa"
                    />
                  </div>
                )}

                <div>
                  <FieldLabel>E-mail</FieldLabel>
                  <IconInput
                    icon={Mail}
                    type="email"
                    value={form.email}
                    onChange={(e) => onFormChange((f) => ({ ...f, email: e.target.value }))}
                    placeholder="email@exemplo.com"
                  />
                </div>

                <div>
                  <FieldLabel>Telefone</FieldLabel>
                  <IconInput
                    icon={Phone}
                    value={form.telefone}
                    onChange={(e) => onFormChange((f) => ({ ...f, telefone: formatTelefone(e.target.value) }))}
                    placeholder="(00) 00000-0000"
                    inputMode="tel"
                    maxLength={15}
                  />
                </div>

                <div>
                  <FieldLabel>Origem</FieldLabel>
                  <select
                    value={form.origem}
                    onChange={(e) => onFormChange((f) => ({ ...f, origem: e.target.value }))}
                    className={selectClass}
                  >
                    {origensAtivas().map((o) => (
                      <option key={o.key} value={o.key}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <FieldLabel>Status</FieldLabel>
                  <select
                    value={form.status}
                    onChange={(e) => onFormChange((f) => ({ ...f, status: e.target.value }))}
                    className={selectClass}
                  >
                    {statusOpcoes.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <p className="text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-[#0d1f3c] pb-2">
                Endereço
              </p>

              <div>
                <FieldLabel>Logradouro</FieldLabel>
                <div className="relative">
                  <MapPin
                    size={16}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
                    aria-hidden
                  />
                  <input
                    value={form.logradouro}
                    onChange={(e) => onFormChange((f) => ({ ...f, logradouro: toUpperCase(e.target.value) }))}
                    className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#1e3a5f]"
                    placeholder="Rua, avenida..."
                  />
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <div className="w-[120px]">
                  <FieldLabel>CEP</FieldLabel>
                  <input
                    type="text"
                    value={form.cep}
                    onChange={(e) => onCepChange(e.target.value)}
                    onBlur={() => form.cep.replace(/\D/g, '').length === 8 && onBuscarCep()}
                    maxLength={9}
                    className={selectClass}
                    placeholder="00000-000"
                    inputMode="numeric"
                  />
                </div>
                <div className="flex items-end">
                  <button
                    type="button"
                    onClick={onBuscarCep}
                    disabled={buscarCepLoading || form.cep.replace(/\D/g, '').length !== 8}
                    className="px-3 py-2 rounded-lg border text-sm font-medium disabled:opacity-50 whitespace-nowrap"
                    style={{ borderColor: accentColor, color: accentColor }}
                  >
                    {buscarCepLoading ? '...' : 'Consultar CEP'}
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div>
                  <FieldLabel>Número</FieldLabel>
                  <input
                    value={form.numero}
                    onChange={(e) => onFormChange((f) => ({ ...f, numero: e.target.value }))}
                    className={selectClass}
                    placeholder="Nº"
                  />
                </div>
                <div className="col-span-1 sm:col-span-3">
                  <FieldLabel>Complemento</FieldLabel>
                  <input
                    value={form.complemento}
                    onChange={(e) => onFormChange((f) => ({ ...f, complemento: toUpperCase(e.target.value) }))}
                    className={selectClass}
                    placeholder="Opcional"
                  />
                </div>
                <div className="col-span-2 sm:col-span-2">
                  <FieldLabel>Bairro</FieldLabel>
                  <input
                    value={form.bairro}
                    onChange={(e) => onFormChange((f) => ({ ...f, bairro: toUpperCase(e.target.value) }))}
                    className={selectClass}
                    placeholder="Bairro"
                  />
                </div>
                <div>
                  <FieldLabel>Cidade</FieldLabel>
                  <input
                    value={form.cidade}
                    onChange={(e) => onFormChange((f) => ({ ...f, cidade: toUpperCase(e.target.value) }))}
                    className={selectClass}
                    placeholder="Cidade"
                  />
                </div>
                <div>
                  <FieldLabel>UF</FieldLabel>
                  <select
                    value={form.uf}
                    onChange={(e) => onFormChange((f) => ({ ...f, uf: e.target.value }))}
                    className={selectClass}
                  >
                    <option value="">—</option>
                    {UF_LIST.map((uf) => (
                      <option key={uf} value={uf}>
                        {uf}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <FieldLabel>Observações</FieldLabel>
                <textarea
                  value={form.observacoes}
                  onChange={(e) => onFormChange((f) => ({ ...f, observacoes: e.target.value }))}
                  rows={3}
                  className={`${selectClass} resize-y min-h-[72px]`}
                  placeholder="Anotações, histórico de contato..."
                />
              </div>
            </div>
          </div>
        </CrmPagePanel>
      </div>

      <div className="shrink-0 border-t border-gray-200 dark:border-[#0d1f3c] bg-white/80 dark:bg-[#16325c]/80 px-4 md:px-6 lg:px-8 py-4">
        <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3 w-full">
          <button
            type="button"
            onClick={onCancel}
            className="sm:min-w-[120px] py-2.5 px-5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-[#1e3a5f]"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onSave}
            disabled={saving}
            className="sm:min-w-[180px] flex items-center justify-center gap-2 py-2.5 px-5 rounded-lg text-white text-sm font-medium disabled:opacity-60"
            style={{ backgroundColor: accentColor }}
          >
            {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
            {saving ? 'Salvando...' : editing ? 'Salvar alterações' : 'Cadastrar lead'}
          </button>
        </div>
      </div>
    </div>
  );
}
