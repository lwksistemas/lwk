'use client';

import { CrmFormPageShell } from '@/components/crm-vendas/CrmFormPageShell';
import { formatCep, formatCpfCnpj, formatTelefone, toUpperCase } from '@/lib/format-br';

export interface ContaFormData {
  nome: string;
  razao_social: string;
  cnpj: string;
  inscricao_estadual: string;
  tipo: string;
  segmento: string;
  telefone: string;
  email: string;
  site: string;
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  uf: string;
  observacoes: string;
}

const inputClass =
  'w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#1e3a5f] text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0176d3] focus:ring-offset-0';
const labelClass = 'block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1';
const sectionTitleClass =
  'text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-[#0d1f3c] pb-2';

interface ContaCadastroFormProps {
  editing?: boolean;
  formData: ContaFormData;
  onChange: (data: ContaFormData) => void;
  error?: string | null;
  saving?: boolean;
  consultingCNPJ?: boolean;
  consultingCEP?: boolean;
  onConsultarCNPJ: () => void;
  onConsultarCEP: () => void;
  onSave: () => void;
  onCancel: () => void;
}

export function ContaCadastroForm({
  editing = false,
  formData,
  onChange,
  error,
  saving = false,
  consultingCNPJ = false,
  consultingCEP = false,
  onConsultarCNPJ,
  onConsultarCEP,
  onSave,
  onCancel,
}: ContaCadastroFormProps) {
  const set = (field: keyof ContaFormData, value: string) => onChange({ ...formData, [field]: value });
  const setUpper = (field: keyof ContaFormData, value: string) =>
    onChange({ ...formData, [field]: toUpperCase(value) });
  const setCnpj = (value: string) => onChange({ ...formData, cnpj: formatCpfCnpj(value) });
  const setCep = (value: string) => onChange({ ...formData, cep: formatCep(value) });
  const setPhone = (value: string) => onChange({ ...formData, telefone: formatTelefone(value) });

  return (
    <CrmFormPageShell
      error={error}
      saving={saving}
      saveLabel={editing ? 'Salvar alterações' : 'Cadastrar conta'}
      savingLabel="Salvando..."
      onSave={onSave}
      onCancel={onCancel}
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 xl:gap-14 w-full">
        <div className="space-y-6">
          <section className="space-y-4">
            <h3 className={sectionTitleClass}>Identificação</h3>
            <div>
              <label className={labelClass}>CNPJ</label>
              <div className="flex flex-col sm:flex-row gap-2">
                <input
                  type="text"
                  value={formData.cnpj}
                  onChange={(e) => setCnpj(e.target.value)}
                  className={`${inputClass} sm:flex-1`}
                  placeholder="00.000.000/0000-00"
                  maxLength={18}
                />
                <button
                  type="button"
                  onClick={onConsultarCNPJ}
                  disabled={consultingCNPJ || formData.cnpj.replace(/\D/g, '').length !== 14}
                  className="shrink-0 px-4 py-2 rounded-lg border border-[#0176d3] text-[#0176d3] text-sm font-medium disabled:opacity-50 whitespace-nowrap hover:bg-[#0176d3]/5"
                >
                  {consultingCNPJ ? 'Consultando...' : 'Consultar CNPJ'}
                </button>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Consulte o CNPJ para preencher os dados automaticamente
              </p>
            </div>
            <div>
              <label className={labelClass}>Tipo de empresa *</label>
              <select
                value={formData.tipo}
                onChange={(e) => set('tipo', e.target.value)}
                className={inputClass}
                required
              >
                <option value="cliente">Cliente</option>
                <option value="prestadora">Prestadora de Serviço</option>
                <option value="ambos">Cliente e Prestadora</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Razão social</label>
              <input
                type="text"
                value={formData.razao_social}
                onChange={(e) => setUpper('razao_social', e.target.value)}
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Nome fantasia *</label>
              <input
                type="text"
                value={formData.nome}
                onChange={(e) => setUpper('nome', e.target.value)}
                className={inputClass}
                required
                autoFocus
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Inscrição estadual</label>
                <input
                  type="text"
                  value={formData.inscricao_estadual}
                  onChange={(e) => set('inscricao_estadual', e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Segmento</label>
                <input
                  type="text"
                  value={formData.segmento}
                  onChange={(e) => setUpper('segmento', e.target.value)}
                  className={inputClass}
                  placeholder="Ex: Tecnologia, Varejo"
                />
              </div>
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <section className="space-y-4">
            <h3 className={sectionTitleClass}>Contato</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Telefone</label>
                <input
                  type="tel"
                  value={formData.telefone}
                  onChange={(e) => setPhone(e.target.value)}
                  className={inputClass}
                  placeholder="(00) 00000-0000"
                />
              </div>
              <div>
                <label className={labelClass}>E-mail</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => set('email', e.target.value)}
                  className={inputClass}
                />
              </div>
              <div className="sm:col-span-2">
                <label className={labelClass}>Site</label>
                <input
                  type="url"
                  value={formData.site}
                  onChange={(e) => set('site', e.target.value)}
                  className={inputClass}
                  placeholder="https://exemplo.com.br"
                />
              </div>
            </div>
          </section>

          <section className="space-y-4">
            <h3 className={sectionTitleClass}>Endereço</h3>
            <div className="flex flex-wrap gap-2">
              <div className="flex-1 min-w-[140px]">
                <label className={labelClass}>CEP</label>
                <input
                  type="text"
                  value={formData.cep}
                  onChange={(e) => setCep(e.target.value)}
                  onBlur={() => {
                    if (formData.cep.replace(/\D/g, '').length === 8) onConsultarCEP();
                  }}
                  className={inputClass}
                  placeholder="00000-000"
                  maxLength={9}
                />
              </div>
              <div className="flex items-end">
                <button
                  type="button"
                  onClick={onConsultarCEP}
                  disabled={consultingCEP || formData.cep.replace(/\D/g, '').length !== 8}
                  className="px-4 py-2 rounded-lg border border-[#0176d3] text-[#0176d3] text-sm font-medium disabled:opacity-50 whitespace-nowrap hover:bg-[#0176d3]/5"
                >
                  {consultingCEP ? '...' : 'Consultar CEP'}
                </button>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div className="sm:col-span-3">
                <label className={labelClass}>Logradouro</label>
                <input
                  type="text"
                  value={formData.logradouro}
                  onChange={(e) => setUpper('logradouro', e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>UF</label>
                <input
                  type="text"
                  value={formData.uf}
                  onChange={(e) => set('uf', e.target.value.toUpperCase())}
                  className={inputClass}
                  placeholder="SP"
                  maxLength={2}
                />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Número</label>
                <input
                  type="text"
                  value={formData.numero}
                  onChange={(e) => set('numero', e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Complemento</label>
                <input
                  type="text"
                  value={formData.complemento}
                  onChange={(e) => setUpper('complemento', e.target.value)}
                  className={inputClass}
                  placeholder="Apto, Sala"
                />
              </div>
              <div>
                <label className={labelClass}>Bairro</label>
                <input
                  type="text"
                  value={formData.bairro}
                  onChange={(e) => setUpper('bairro', e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Cidade</label>
                <input
                  type="text"
                  value={formData.cidade}
                  onChange={(e) => setUpper('cidade', e.target.value)}
                  className={inputClass}
                />
              </div>
            </div>
          </section>

          <section className="space-y-4">
            <h3 className={sectionTitleClass}>Observações</h3>
            <textarea
              value={formData.observacoes}
              onChange={(e) => set('observacoes', e.target.value)}
              rows={3}
              className={`${inputClass} resize-y min-h-[72px]`}
              placeholder="Anotações sobre a conta..."
            />
          </section>
        </div>
      </div>
    </CrmFormPageShell>
  );
}
