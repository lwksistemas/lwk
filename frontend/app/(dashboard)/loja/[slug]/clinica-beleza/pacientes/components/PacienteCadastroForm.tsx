"use client";

import {
  Calendar,
  CreditCard,
  Loader2,
  Mail,
  MapPin,
  Phone,
  User,
  UserPlus,
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

function LotusLogo({ color }: { color: string }) {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden>
      <path
        d="M24 8c-2 6-6 10-12 12 6 2 10 6 12 12 2-6 6-10 12-12-6-2-10-6-12-12z"
        fill={color}
        fillOpacity="0.85"
      />
      <path
        d="M24 14c-1.5 4-4 7-8 8 4 1 7 4 8 8 1-4 4-7 8-8-4-1-7-4-8-8z"
        fill={color}
        fillOpacity="0.55"
      />
      <ellipse cx="24" cy="38" rx="3" ry="2" fill={color} fillOpacity="0.4" />
    </svg>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
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
        size={18}
        className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
        aria-hidden
      />
      <input
        {...props}
        className={`w-full pl-10 pr-3 py-2.5 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-0 ${className}`}
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
  lojaNome?: string;
  lojaLogo?: string;
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
  lojaNome,
  lojaLogo,
  accentColor = CLINICA_BELEZA_PRIMARY,
}: PacienteCadastroFormProps) {
  const selectClass =
    "w-full px-3 py-2.5 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-0";

  const nomeParts = (lojaNome || "Clínica").split(/\s+/);
  const tituloLoja = nomeParts.slice(0, 2).join(" ").toUpperCase() || "CLÍNICA";
  const subtituloLoja = nomeParts.slice(2).join(" ").toUpperCase() || "ESTÉTICA AVANÇADA";

  return (
    <div className="min-h-full bg-[#ececec] dark:bg-neutral-950 py-6 px-4 md:py-10">
      <div className="max-w-2xl mx-auto">
        {/* Logo / marca */}
        <div className="text-center mb-6">
          {lojaLogo ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={lojaLogo}
              alt={lojaNome || "Logo"}
              className="h-14 w-auto mx-auto object-contain mb-2"
            />
          ) : (
            <div className="flex justify-center mb-2">
              <LotusLogo color={accentColor} />
            </div>
          )}
          <p
            className="text-xl font-serif tracking-wide text-gray-900 dark:text-gray-100"
            style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
          >
            {tituloLoja}
          </p>
          <p className="text-xs tracking-[0.2em] mt-0.5 font-medium" style={{ color: accentColor }}>
            {subtituloLoja}
          </p>
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-neutral-900 rounded-2xl shadow-lg border border-gray-100 dark:border-neutral-800 px-6 py-8 md:px-10 md:py-10">
          <div className="text-center mb-8">
            <h1
              className="text-2xl md:text-3xl text-gray-900 dark:text-gray-100 mb-2"
              style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
            >
              {editing ? "Editar Cliente" : "Cadastro de Cliente"}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {editing
                ? "Atualize os dados do cliente abaixo"
                : "Preencha os dados abaixo para realizar seu cadastro"}
            </p>
          </div>

          {error && (
            <div className="mb-6 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}

          <div className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <FieldLabel>Nome completo *</FieldLabel>
                <IconInput
                  icon={User}
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: toUpperCase(e.target.value) }))}
                  placeholder="Digite seu nome completo"
                  autoFocus
                  style={{ focusRingColor: accentColor } as React.CSSProperties}
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
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <FieldLabel>E-mail</FieldLabel>
                <IconInput
                  icon={Mail}
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  placeholder="Digite seu e-mail"
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
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
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

            {/* Endereço */}
            <div>
              <FieldLabel>Endereço</FieldLabel>
              <div className="relative mb-3">
                <MapPin
                  size={18}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
                  aria-hidden
                />
                <input
                  value={form.logradouro}
                  onChange={(e) => setForm((f) => ({ ...f, logradouro: toUpperCase(e.target.value) }))}
                  className="w-full pl-10 pr-3 py-2.5 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800"
                  placeholder="Digite seu endereço"
                />
              </div>
              <div className="flex flex-col sm:flex-row gap-2 mb-3">
                <input
                  type="text"
                  value={form.cep}
                  onChange={(e) => onCepChange(e.target.value)}
                  onBlur={() => form.cep.replace(/\D/g, "").length === 8 && onBuscarCep()}
                  maxLength={9}
                  className={`${selectClass} sm:max-w-[140px]`}
                  placeholder="CEP"
                  inputMode="numeric"
                />
                <button
                  type="button"
                  onClick={onBuscarCep}
                  disabled={buscarCepLoading || form.cep.replace(/\D/g, "").length !== 8}
                  className="px-4 py-2.5 rounded-lg border text-sm font-medium disabled:opacity-50 whitespace-nowrap"
                  style={{ borderColor: accentColor, color: accentColor }}
                >
                  {buscarCepLoading ? "Consultando..." : "Consultar CEP"}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <FieldLabel>Número</FieldLabel>
                <input
                  value={form.numero}
                  onChange={(e) => setForm((f) => ({ ...f, numero: e.target.value }))}
                  className={selectClass}
                  placeholder="Número"
                />
              </div>
              <div>
                <FieldLabel>Complemento</FieldLabel>
                <input
                  value={form.complemento}
                  onChange={(e) => setForm((f) => ({ ...f, complemento: toUpperCase(e.target.value) }))}
                  className={selectClass}
                  placeholder="Complemento (opcional)"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
              <div>
                <FieldLabel>Bairro</FieldLabel>
                <input
                  value={form.bairro}
                  onChange={(e) => setForm((f) => ({ ...f, bairro: toUpperCase(e.target.value) }))}
                  className={selectClass}
                  placeholder="Digite seu bairro"
                />
              </div>
              <div>
                <FieldLabel>Cidade</FieldLabel>
                <input
                  value={form.cidade}
                  onChange={(e) => setForm((f) => ({ ...f, cidade: toUpperCase(e.target.value) }))}
                  className={selectClass}
                  placeholder="Digite sua cidade"
                />
              </div>
              <div>
                <FieldLabel>Estado</FieldLabel>
                <select
                  value={form.uf}
                  onChange={(e) => setForm((f) => ({ ...f, uf: e.target.value }))}
                  className={selectClass}
                >
                  <option value="">Selecione</option>
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
                className={`${selectClass} resize-y min-h-[80px]`}
                placeholder="Observações sobre o cliente (opcional)"
              />
            </div>

            <label className="flex items-start gap-3 cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={form.allow_whatsapp}
                onChange={(e) => setForm((f) => ({ ...f, allow_whatsapp: e.target.checked }))}
                className="mt-0.5 rounded border-gray-300"
                style={{ accentColor }}
              />
              <span className="text-sm text-gray-600 dark:text-gray-400 leading-snug">
                Permitir WhatsApp (lembretes e cobranças) — LGPD: o cliente pode optar por não receber
              </span>
            </label>

            <button
              type="button"
              onClick={onSave}
              disabled={saving}
              className="w-full flex items-center justify-center gap-2 py-3.5 rounded-lg text-white text-base font-medium disabled:opacity-60 transition-opacity hover:opacity-95 mt-2"
              style={{ backgroundColor: accentColor }}
            >
              {saving ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                <UserPlus size={20} />
              )}
              {saving ? "Salvando..." : editing ? "Salvar alterações" : "Cadastrar"}
            </button>

            <p className="text-center text-sm text-gray-500 dark:text-gray-400 pt-1">
              <button
                type="button"
                onClick={onCancel}
                className="hover:underline"
                style={{ color: accentColor }}
              >
                Voltar à lista de clientes
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
