"use client";

import {
  ArrowLeft,
  Calendar,
  CreditCard,
  Loader2,
  Mail,
  MapPin,
  Phone,
  Save,
  User,
} from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import type { ConvenioItem } from "@/lib/clinica-beleza-api";
import {
  CONVENIO_PARTICULAR_LABEL,
  findConvenioParticular,
  isConvenioParticularNome,
  ordenarConveniosComParticularPrimeiro,
} from "@/lib/convenio-precos";
import { formatCep, formatCpf, formatTelefone, toUpperCase } from "@/lib/format-br";

export const PACIENTE_EMPTY_FORM = {
  name: "",
  phone: "",
  email: "",
  cpf: "",
  birth_date: "",
  cep: "",
  logradouro: "",
  numero: "",
  complemento: "",
  bairro: "",
  cidade: "",
  uf: "",
  notes: "",
  allow_whatsapp: true,
  convenio: "" as number | "",
};

export type PacienteFormState = typeof PACIENTE_EMPTY_FORM;

const UF_LIST = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
  "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
  "RS", "RO", "RR", "SC", "SP", "SE", "TO",
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
  className = "",
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
        className={`w-full pl-9 pr-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-0 ${className}`}
      />
    </div>
  );
}

interface PacienteCadastroFormProps {
  editing: boolean;
  form: PacienteFormState;
  setForm: React.Dispatch<React.SetStateAction<PacienteFormState>>;
  error: string;
  saving: boolean;
  convenios: ConvenioItem[];
  buscarCepLoading: boolean;
  onCepChange: (value: string) => void;
  onBuscarCep: () => void;
  onSave: () => void;
  onCancel: () => void;
  accentColor?: string;
}

export function PacienteCadastroForm({
  editing,
  form,
  setForm,
  error,
  saving,
  convenios,
  buscarCepLoading,
  onCepChange,
  onBuscarCep,
  onSave,
  onCancel,
  accentColor = CLINICA_BELEZA_PRIMARY,
}: PacienteCadastroFormProps) {
  const selectClass =
    "w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-0";

  return (
    <div className="min-h-full bg-[#ececec] dark:bg-neutral-950 py-4 px-4 md:py-6 md:px-6">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-lg border border-gray-100 dark:border-neutral-800 overflow-hidden">
          {/* Barra superior compacta */}
          <div className="flex items-center justify-between gap-3 px-5 py-3 border-b border-gray-100 dark:border-neutral-800 bg-gray-50/80 dark:bg-neutral-900/80">
            <button
              type="button"
              onClick={onCancel}
              className="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
            >
              <ArrowLeft size={16} />
              Voltar à lista
            </button>
            <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
              {editing ? "Editar cliente" : "Novo cliente"}
            </span>
            <div className="w-[100px]" aria-hidden />
          </div>

          <div className="p-5 md:p-6 lg:p-8">
            {error && (
              <div className="mb-5 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
                {error}
              </div>
            )}

            {/* Layout paisagem: duas colunas */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10">
              {/* Coluna esquerda — dados pessoais */}
              <div className="space-y-4">
                <p className="text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-neutral-800 pb-2">
                  Dados pessoais
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <FieldLabel>Nome completo *</FieldLabel>
                    <IconInput
                      icon={User}
                      value={form.name}
                      onChange={(e) => setForm((f) => ({ ...f, name: toUpperCase(e.target.value) }))}
                      placeholder="Nome completo"
                      autoFocus
                    />
                  </div>
                  <div>
                    <FieldLabel>Data de nascimento</FieldLabel>
                    <IconInput
                      icon={Calendar}
                      type="date"
                      value={form.birth_date}
                      onChange={(e) => setForm((f) => ({ ...f, birth_date: e.target.value }))}
                    />
                  </div>
                  <div>
                    <FieldLabel>CPF</FieldLabel>
                    <IconInput
                      icon={CreditCard}
                      value={form.cpf}
                      onChange={(e) => setForm((f) => ({ ...f, cpf: formatCpf(e.target.value) }))}
                      placeholder="000.000.000-00"
                      inputMode="numeric"
                      maxLength={14}
                    />
                  </div>
                  <div>
                    <FieldLabel>E-mail</FieldLabel>
                    <IconInput
                      icon={Mail}
                      type="email"
                      value={form.email}
                      onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                      placeholder="email@exemplo.com"
                    />
                  </div>
                  <div>
                    <FieldLabel>Telefone</FieldLabel>
                    <IconInput
                      icon={Phone}
                      value={form.phone}
                      onChange={(e) => setForm((f) => ({ ...f, phone: formatTelefone(e.target.value) }))}
                      placeholder="(00) 00000-0000"
                      inputMode="tel"
                      maxLength={15}
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <FieldLabel>Convênio padrão</FieldLabel>
                    <select
                      value={form.convenio}
                      onChange={(e) =>
                        setForm((f) => ({
                          ...f,
                          convenio: e.target.value ? Number(e.target.value) : "",
                        }))
                      }
                      className={selectClass}
                    >
                      {!findConvenioParticular(convenios) && (
                        <option value="">{CONVENIO_PARTICULAR_LABEL}</option>
                      )}
                      {ordenarConveniosComParticularPrimeiro(convenios).map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.nome}
                          {isConvenioParticularNome(c.nome) ? " (padrão)" : ""}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <label className="flex items-start gap-2.5 cursor-pointer pt-1">
                  <input
                    type="checkbox"
                    checked={form.allow_whatsapp}
                    onChange={(e) => setForm((f) => ({ ...f, allow_whatsapp: e.target.checked }))}
                    className="mt-0.5 rounded border-gray-300"
                    style={{ accentColor }}
                  />
                  <span className="text-xs text-gray-600 dark:text-gray-400 leading-snug">
                    Permitir WhatsApp (lembretes e cobranças) — LGPD
                  </span>
                </label>
              </div>

              {/* Coluna direita — endereço e observações */}
              <div className="space-y-4">
                <p className="text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-neutral-800 pb-2">
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
                      onChange={(e) => setForm((f) => ({ ...f, logradouro: toUpperCase(e.target.value) }))}
                      className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800"
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
                      onBlur={() => form.cep.replace(/\D/g, "").length === 8 && onBuscarCep()}
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
                      disabled={buscarCepLoading || form.cep.replace(/\D/g, "").length !== 8}
                      className="px-3 py-2 rounded-lg border text-sm font-medium disabled:opacity-50 whitespace-nowrap"
                      style={{ borderColor: accentColor, color: accentColor }}
                    >
                      {buscarCepLoading ? "..." : "Consultar CEP"}
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div>
                    <FieldLabel>Número</FieldLabel>
                    <input
                      value={form.numero}
                      onChange={(e) => setForm((f) => ({ ...f, numero: e.target.value }))}
                      className={selectClass}
                      placeholder="Nº"
                    />
                  </div>
                  <div className="col-span-1 sm:col-span-3">
                    <FieldLabel>Complemento</FieldLabel>
                    <input
                      value={form.complemento}
                      onChange={(e) => setForm((f) => ({ ...f, complemento: toUpperCase(e.target.value) }))}
                      className={selectClass}
                      placeholder="Opcional"
                    />
                  </div>
                  <div className="col-span-2 sm:col-span-2">
                    <FieldLabel>Bairro</FieldLabel>
                    <input
                      value={form.bairro}
                      onChange={(e) => setForm((f) => ({ ...f, bairro: toUpperCase(e.target.value) }))}
                      className={selectClass}
                      placeholder="Bairro"
                    />
                  </div>
                  <div>
                    <FieldLabel>Cidade</FieldLabel>
                    <input
                      value={form.cidade}
                      onChange={(e) => setForm((f) => ({ ...f, cidade: toUpperCase(e.target.value) }))}
                      className={selectClass}
                      placeholder="Cidade"
                    />
                  </div>
                  <div>
                    <FieldLabel>UF</FieldLabel>
                    <select
                      value={form.uf}
                      onChange={(e) => setForm((f) => ({ ...f, uf: e.target.value }))}
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
                    value={form.notes}
                    onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                    rows={3}
                    className={`${selectClass} resize-y min-h-[72px]`}
                    placeholder="Opcional"
                  />
                </div>
              </div>
            </div>

            {/* Ações — rodapé horizontal */}
            <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3 mt-8 pt-5 border-t border-gray-100 dark:border-neutral-800">
              <button
                type="button"
                onClick={onCancel}
                className="sm:min-w-[120px] py-2.5 px-5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-800"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={onSave}
                disabled={saving}
                className="sm:min-w-[160px] flex items-center justify-center gap-2 py-2.5 px-5 rounded-lg text-white text-sm font-medium disabled:opacity-60"
                style={{ backgroundColor: accentColor }}
              >
                {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                {saving ? "Salvando..." : editing ? "Salvar alterações" : "Cadastrar cliente"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
