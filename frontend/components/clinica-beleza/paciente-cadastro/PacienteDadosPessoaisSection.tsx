import { Calendar, CreditCard, Mail, Phone, User } from "lucide-react";
import type { ConvenioItem } from "@/lib/clinica-beleza-api";
import {
  CONVENIO_PARTICULAR_LABEL,
  findConvenioParticular,
  isConvenioParticularNome,
  ordenarConveniosComParticularPrimeiro,
} from "@/lib/convenio-precos";
import { formatCpf, formatTelefone, toUpperCase } from "@/lib/format-br";
import { PacienteFotoCadastro } from "@/components/clinica-beleza/pacientes-page/components/PacienteFotoCadastro";
import { FieldLabel, FORM_SELECT_CLASS, IconInput, SECTION_TITLE_CLASS } from "./paciente-cadastro-ui";
import type { PacienteFormState } from "./paciente-cadastro-types";

interface PacienteDadosPessoaisSectionProps {
  form: PacienteFormState;
  convenios: ConvenioItem[];
  saving: boolean;
  accentColor: string;
  lojaSlug: string;
  onChange: (patch: Partial<PacienteFormState>) => void;
  hideConvenio?: boolean;
}

export function PacienteDadosPessoaisSection({
  form,
  convenios,
  saving,
  accentColor,
  lojaSlug,
  onChange,
  hideConvenio = false,
}: PacienteDadosPessoaisSectionProps) {
  return (
    <div className="space-y-4">
      <p className={SECTION_TITLE_CLASS}>Dados pessoais</p>

      <PacienteFotoCadastro
        slug={lojaSlug}
        value={form.foto_url}
        onChange={(url) => onChange({ foto_url: url })}
        disabled={saving}
        accentColor={accentColor}
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="sm:col-span-2">
          <FieldLabel>Nome completo *</FieldLabel>
          <IconInput
            icon={User}
            value={form.name}
            onChange={(e) => onChange({ name: toUpperCase(e.target.value) })}
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
            onChange={(e) => onChange({ birth_date: e.target.value })}
          />
        </div>
        <div>
          <FieldLabel>CPF</FieldLabel>
          <IconInput
            icon={CreditCard}
            value={form.cpf}
            onChange={(e) => onChange({ cpf: formatCpf(e.target.value) })}
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
            onChange={(e) => onChange({ email: e.target.value })}
            placeholder="email@exemplo.com"
          />
        </div>
        <div>
          <FieldLabel>Telefone</FieldLabel>
          <IconInput
            icon={Phone}
            value={form.phone}
            onChange={(e) => onChange({ phone: formatTelefone(e.target.value) })}
            placeholder="(00) 00000-0000"
            inputMode="tel"
            maxLength={15}
          />
        </div>
        {!hideConvenio && (
          <div className="sm:col-span-2">
            <FieldLabel>Convênio padrão</FieldLabel>
            <select
              value={form.convenio}
              onChange={(e) =>
                onChange({ convenio: e.target.value ? Number(e.target.value) : "" })
              }
              className={FORM_SELECT_CLASS}
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
        )}
      </div>

      <label className="flex items-start gap-2.5 cursor-pointer pt-1">
        <input
          type="checkbox"
          checked={form.allow_whatsapp}
          onChange={(e) => onChange({ allow_whatsapp: e.target.checked })}
          className="mt-0.5 rounded border-gray-300"
          style={{ accentColor }}
        />
        <span className="text-xs text-gray-600 dark:text-gray-400 leading-snug">
          Permitir WhatsApp (lembretes e cobranças) — LGPD
        </span>
      </label>
    </div>
  );
}
